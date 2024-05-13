# builtin imports
import os
import signal
import json

# external imports
from redis import Redis
from redis import exceptions as redis_exceptions


# internal imports
from .singleton import Singleton
from ..config.config import CacheConfig


def get_cache():
    c: Cache = Cache()
    yield c


class Cache(metaclass=Singleton):
    _redis: Redis

    def __init__(self):
        pass

    def setup(self, config: CacheConfig):
        try:
            self._redis = Redis(
                host=config.host,
                port=config.port,
                db=config.dbno,
                password=config.pswd,
            )

            _ = not self._redis.ping()
        except redis_exceptions.ConnectionError:
            # kill the process if we cannot connect to redis instance
            print("failed to connect to redis {}:{}".format(config.host, config.port))
            os.kill(os.getpid(), signal.SIGKILL)

    def get_redis_connection(self) -> Redis:
        return self._redis

    def get(self, key: str) -> any:
        # check if key exists, or return empty string
        val = self._redis.get(key)
        if val is None:
            return ""

        return json.loads(val)

    def set(self, key: str, val: any, ttl: int = 0) -> bool:
        val_str = json.dumps(val)

        if not ttl:
            return self._redis.set(name=key, value=val_str)

        return self._redis.set(name=key, value=val_str, ex=ttl)
