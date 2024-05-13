# externa imports
from redis import Redis
from rq import Queue
from rq_scheduler import Scheduler


from rss_reader.utils.singleton import Singleton

# internal imports
from .cache import Cache


def get_queue_conn():
    mq: MessageQueue = MessageQueue()
    yield mq.get_queue()


class MessageQueue(metaclass=Singleton):
    _q: Queue
    _queue_name: str = "rss_reader.feeds.sync"
    _scheduler: Scheduler

    def __init__(self):
        pass

    def setup(self) -> None:
        redis_conn: Redis = Cache().get_redis_connection()

        self._q = Queue(
            connection=redis_conn,
            name=self._queue_name,
            default_timeout=10,
        )

    def get_queue(self) -> Queue:
        return self._q

    def get_scheduler(self) -> Scheduler:
        return self._scheduler

    def get_queue_name(self) -> str:
        return self._queue_name


class BackgroundScheduler(metaclass=Singleton):
    _scheduler: Scheduler

    def __init__(self):
        pass

    def setup(self, q: Queue, redis_conn: Redis):
        self._scheduler = Scheduler(
            queue=q,
            connection=redis_conn,
            name="background sync scheduler",
        )

    def get_scheduler(self) -> Scheduler:
        return self._scheduler
