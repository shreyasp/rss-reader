# builtin imports
from os import path

# external imports
import yaml

# internal imports
from ..utils.singleton import Singleton

class AppConfig(metaclass=Singleton):
    debug: bool

    def __init__(self, config:any) -> None:
        self.debug = config["debug"]


class DBConfig(metaclass=Singleton):
    host: str
    port: int
    user: str
    pswd: str
    
    def __init__(self, config: any) -> None:
        self.host = config["host"]
        self.port = config["port"]
        self.user = config["user"]
        self.pswd = config["pswd"]

class CacheConfig(metaclass=Singleton):
    host: str
    port: int
    dbno: int
    pswd: str

    def __init__(self, config: any) -> None:
        self.host = config["host"] or "localhost"
        self.port = config["port"] or 6379
        self.dbno = config["dbno"]
        self.pswd = config["pswd"]


class Config(metaclass=Singleton):
    app_config: AppConfig
    db_config: DBConfig
    cache_config: CacheConfig

    def __init__(self, mode:str) -> None:    
        # path to config file
        config_file_path = path.abspath(path.join("app", "config", "config.dev.yml"))
        if mode == "prod":
            config_file_path = path.abspath(path.join("app", "config", "config.prod.yml"))
        elif mode == "test":
            config_file_path = path.abspath(path.join("app", "config", "config.test.yml"))

        with open(config_file_path, "r") as config_file:
            config = yaml.safe_load(config_file)
            
            # init application config
            self.app_config = AppConfig(config["app"])

            # init database config
            self.db_config = DBConfig(config["db"])
            
            # init cache config
            self.cache_config = CacheConfig(config["cache"])



