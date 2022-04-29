# isort:skip_file

# import sys

# sys.path.extend(["./"])

# TODO debug this issue we are seeing https://github.com/aio-libs/aioredis-py/issues/878

from pydantic.utils import import_string
from arq import cron

from app.db.session import async_session
from app.core.arq_app import redis_settings
from app.models.user import User  # noqa


ARQ_BACKGROUND_FUNCTIONS = [
    "app.tasks.utils.test_arq",
    "app.tasks.utils.test_arq_subtask",
    "app.tasks.utils.send_daily_push_notification",
    "app.tasks.nakamal.select_featured_nakamal",
    "app.tasks.video.process_video",
]


FUNCTIONS: list = (
    [
        import_string(background_function)
        for background_function in list(ARQ_BACKGROUND_FUNCTIONS)
    ]
    if ARQ_BACKGROUND_FUNCTIONS is not None
    else list()
)


async def startup(ctx):
    """
    Binds a connection set to the db object.
    """
    ctx["db_session"] = async_session


async def shutdown(ctx):
    """
    Pops the bind on the db object.
    """
    pass


class WorkerSettings:
    """
    Settings for the ARQ worker.
    """

    # NOTE cron times must be in UTC (hour=6 == 6:00 UTC == 17:00 VUT)
    # XXX https://github.com/samuelcolvin/arq/issues/304 before uncommenting cron_jobs
    cron_jobs = [
        cron(
            "app.tasks.utils.send_daily_push_notification",
            weekday={0, 1, 2, 3, 4, 5},
            hour=6,
            minute=0,
        ),
        cron(
            "app.tasks.nakamal.select_featured_nakamal",
            hour=0,
            minute=0,
            run_at_startup=True,  # our redis is currently not persistent so we need to run this at startup
        ),
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = redis_settings
    functions: list = FUNCTIONS
