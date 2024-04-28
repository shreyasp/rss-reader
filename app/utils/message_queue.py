# externa imports
from rq import Queue

# internal imports
from .cache import Cache

class MessageQueue:
    _q: Queue

    def __init__(self):
        pass

    def setup(self) -> None:
        redis_conn = Cache().get_redis_connection()

        self._q = Queue(
            connection=redis_conn,
            name="rss-reader-sync-feeds",
            default_timeout=10,
        )
