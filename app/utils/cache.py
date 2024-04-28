# builtin imports
import os
import signal

# external imports
from redis import Redis
from redis import exceptions as redis_exceptions


# internal imports
from .singleton import Singleton
from ..config.config import CacheConfig


class Cache(metaclass=Singleton):
    _redis: Redis
    
    def __init__(self):
        pass

    def setup(self, config:CacheConfig):
        try:
            self._redis = Redis(
                host=config.host,
                port=config.port,
                db=config.dbno,
                password=config.pswd,
                decode_responses=True
            )

            _ = not self._redis.ping()
        except redis_exceptions.ConnectionError:
            # kill the process if we cannot connect to redis instance
            print("failed to connect to redis {}:{}".format(config.host, config.port))
            os.kill(os.getpid(), signal.SIGKILL)

    def get_redis_connection(self):
        return self._redis

    def get(self, key:str) -> any:
        # check if key exists, or return empty string 
        val = self._redis.get(key)
        if val is None:
            return ""
        
        return val

    def set(self, key:str, val:any, ttl:int) -> bool:
        return self._redis.set(
            name=key,
            value=val,
            ex=ttl
        )
