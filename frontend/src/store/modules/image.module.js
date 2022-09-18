/* eslint-disable */

import Vue from 'vue';
import ls from 'localstorage-slim';

import { normalizeRelations, resolveRelations } from '@/store/helpers';
import imagesApi from '@/api/images';
import nakamalsApi from '@/api/nakamals';
import usersApi from '@/api/users';
import i18n from '../../plugins/i18n';

const initialState = () => ({
  byId: {},
  byNakamalId: {},
  allIds: [],
  recentIds: [],
});

const state = initialState();

const getters = {
  // Return a single image with the given id.
  find: (state, _, __, rootGetters) => id => {
    // TODO if not found dispatch the get_by_id method
    // return resolveRelations(state.byId[id], ['nakamal', 'user'], rootGetters);
    return state.byId[id];
  },
  // Return a list of images in the order of `allIds`.
  list: (state, getters) => {
    return state.allIds.map(id => getters.find(id));
  },
  // Return a list of recent images. 
  recent: (state, getters) => {
    return state.recentIds.map(id => getters.find(id));
  },
  // Return a list of images of a nakamal.
  nakamal: (state, getters) => nakamalId => {
    if (!state.byNakamalId[nakamalId]) return [];
    return state.byNakamalId[nakamalId].map(id => getters.find(id));
  },
  // TODO is this needed - it feels hacky seeing it here
  nakamalHasImages: (state, getters) => nakamalId => {
    return Object.keys(state.byNakamalId).includes(nakamalId);
  },
  nakamalProfile: (state, getters) => nakamalId => {
    if (!state.byNakamalId[nakamalId]) return null;
    // Arbitrary first image but in future we could mark image as profile for easy filter
    const profileImageId = state.byNakamalId[nakamalId][0]
    return getters.find(profileImageId)
  },
  // Return a list of images of a user.
  user: (state, getters) => userId => {
    return state.allIds.map(id => getters.find(id)).filter(c => c.user === userId);
  },
};

function commitAddImage(image, commit) {
  // Normalize nested data and swap the image object
  // in the API response with an ID reference.
  commit('add', normalizeRelations(image, ['nakamal', 'user']));
  // Add or update the image relations.
  // if (image.nakamal.chief) {
  //   commit('user/setUser', image.nakamal.chief, {
  //     root: true,
  //   });
  // }
  // commit('nakamal/add', normalizeRelations(image.nakamal, ['chief']), {
  //   root: true,
  // });
  // commit('user/setUser', image.user, {
  //   root: true,
  // });
};

const actions = {
  loadOne: async ({ commit, getters }, id) => {
    // TODO handle network errors
    let image;
    const cacheKey = `images-one:${id}`;
    const cached = ls.get(cacheKey);
    if (cached) {
      image = cached;
    } else {
      let resp = await imagesApi.get(id);
      image = resp.data;
      ls.set(cacheKey, image, { ttl: 900 });
    }
    commitAddImage(image, commit);
    return Promise.resolve(getters.find(id));
  },
  getRecent: async ({ commit }) => {
    try {
      const threshold = 3; // XXX hardcoded value
      const response = await imagesApi.getRecent();
      let items = response.data;
      if (!items.length < threshold) {
        const response = await imagesApi.getAll({ limit: threshold });
        items = response.data;
      }
      items.forEach((item) => {
        commitAddImage(item, commit);
      });
      commit('setRecentIds', items.map((i) => i.id));
    } catch (error) {
      console.log('recent image error', error);
    }
  },
  getNakamal: async ({ commit }, nakamalId) => {
    const response = await nakamalsApi.getImages(nakamalId);
    const images = response.data;
    images.forEach((item) => {
      commitAddImage(item, commit);
    });
  },
  getUser: async ({ commit }, userId) => {
    const response = await usersApi.getImages(userId);
    const images = response.data;
    images.forEach((item) => {
      commitAddImage(item, commit);
    });
  },
  remove: async ({ commit, dispatch, rootState }, id) => {
    try {
      let token = rootState.auth.token;
      await imagesApi.remove(token, id);
      commit('remove', id);
      dispatch('notify/add', {
        title: i18n.t('image.alert.remove_title'),
        text: i18n.t('image.alert.remove_body'),
        type: 'warning',
      }, { root: true });
    }
    catch (error) {
      console.log('Image remove error');
      await dispatch('auth/checkApiError', error, { root: true });
    }
  },
};

const mutations = {
  RESET (state) {
    const newState = initialState();
    Object.keys(newState).forEach(key => {
      state[key] = newState[key];
    });
  },
  add: (state, item) => {
    Vue.set(state.byId, item.id, item);
    if (!state.allIds.includes(item.id)) {
      state.allIds.push(item.id);
    }
    if (!state.byNakamalId[item.nakamal]) {
      Vue.set(state.byNakamalId, item.nakamal, []);
      state.byNakamalId[item.nakamal].push(item.id);
    }
    else if (!state.byNakamalId[item.nakamal].includes(item.id)) {
      state.byNakamalId[item.nakamal].push(item.id);
    }
  },
  remove: (state, id) => {
    let index;
    const nId = state.byId[id].nakamal
    index = state.byNakamalId[nId].indexOf(id);
    if (index !== -1) {
      state.byNakamalId[nId].splice(index, 1);
    }
    index = state.recentIds.indexOf(id);
    if (index !== -1) {
      state.recentIds.splice(index, 1);
    }
    state.allIds.splice(state.allIds.indexOf(id), 1);
    Vue.delete(state.byId, id);
  },
  setRecentIds: (state, ids) => {
    state.recentIds = ids;
  },
};

export default {
  actions,
  getters,
  mutations,
  namespaced: true,
  state,
};
