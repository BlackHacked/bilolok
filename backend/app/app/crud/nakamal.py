from typing import Type, List
from uuid import UUID

from sqlalchemy import select

from app.crud.base import CRUDBase
from app.models.nakamal import Nakamal
from app.schemas.nakamal import NakamalSchemaIn, NakamalSchema
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import selectinload


class CRUDNakamal(CRUDBase[Nakamal, NakamalSchemaIn, NakamalSchema]):    
    @property
    def _in_schema(self) -> Type[NakamalSchemaIn]:
        return NakamalSchemaIn

    @property
    def _schema(self) -> Type[NakamalSchema]:
        return NakamalSchema

    @property
    def _table(self) -> Type[Nakamal]:
        return Nakamal

    async def _get_one(self, item_id: UUID):
        query = (
            select(self._table)
            .options(selectinload(self._table.resources))
            .where(self._table.id == item_id)
        )
        try:
            (item,) = (await self._db_session.execute(query)).one()
        except NoResultFound:
            item = None
        return item

    async def get_multi(self) -> List[NakamalSchema]:
        query = select(self._table).options(selectinload(self._table.resources))
        results = await self._db_session.execute(query)
        return (self._schema.from_orm(item) for item in results.scalars())