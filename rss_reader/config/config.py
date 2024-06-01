# builtin imports
import os
from os import path

# external imports
import yaml

# internal imports
from ..utils.singleton import Singleton


class AppConfig(metaclass=Singleton):
    debug: bool

    def __init__(self, config: any) -> None:
        self.debug = config["debug"]


class DBConfig(metaclass=Singleton):
    host: str
    port: int
    user: str
    pswd: str
    name: str

    def __init__(self, config: any) -> None:
        self.host = config["host"]
        self.port = config["port"]
        self.user = config["user"]
        self.pswd = config["pswd"]
        self.name = config["name"]


class CacheConfig(metaclass=Singleton):
    host: str
    port: int
    dbno: int
    pswd: str

    def __init__(self, config: any, mode: str) -> None:
        self.host = config["host"] or "localhost"
        self.port = config["port"] or 6379
        self.dbno = config["dbno"]
        self.pswd = config["pswd"]

        # to ensure we don't leak the secrets in the public
        # these secrets will be set in fly.io dashboard
        if (
            mode == "prod"
            and os.getenv("REDIS_URL") != ""
            and os.getenv("REDIS_PASSWORD") != ""
            and os.getenv("REDIS_PORT") != ""
        ):
            self.host = os.getenv("REDIS_URL")
            self.pswd = os.getenv("REDIS_PASSWORD")
            self.port = int(os.getenv("REDIS_PORT"))


class Config(metaclass=Singleton):
    app_config: AppConfig
    db_config: DBConfig
    cache_config: CacheConfig

    def __init__(self, mode: str = "dev") -> None:
        # path to config file

        if mode == "prod":
            config_file_path = path.abspath(
                path.join("rss_reader", "config", "config.prod.yml")
            )
        elif mode == "test":
            config_file_path = path.abspath(
                path.join("rss_reader", "config", "config.test.yml")
            )
        elif mode == "docker":
            config_file_path = path.abspath(
                path.join("rss_reader", "config", "config.docker.yml")
            )
        else:
            config_file_path = path.abspath(
                path.join("rss_reader", "config", "config.dev.yml")
            )

        with open(config_file_path, "r") as config_file:
            config = yaml.safe_load(config_file)

            # init application config
            self.app_config = AppConfig(config["app"])

            # init database config
            self.db_config = DBConfig(config["db"])

            # init cache config
            self.cache_config = CacheConfig(config["cache"], mode)
