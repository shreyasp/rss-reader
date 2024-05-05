# external imports
from re import M
from sqlalchemy.ext.asyncio import AsyncSession

# internal imports
from ..database import session as db_session
from ..config.config import DBConfig
from .singleton import Singleton

class Database(metaclass=Singleton):
    _db: AsyncSession

    _db_name: str
    _host: str
    _port: str
    _username: str
    _password: str

    
    def __init__(self, config: DBConfig):
        self._db_name = config.name
        self._host = config.host
        self._port = config.port
        self._username = config.user
        self._password = config.pswd

    def setup(self):
        """setup db object for access"""
        
        pg_conn_str = self.create_pg_connection_string()
        self._db = db_session.get_db_session(pg_conn_str=pg_conn_str)

    def create_pg_connection_string(self) -> str:
        return "postgresql://{username}:{password}@{host}:{port}/{db_name}".format(
            db_name=self._db_name,
            host=self._host,
            port=self._port,
            username=self._username,
            password=self._password
        )