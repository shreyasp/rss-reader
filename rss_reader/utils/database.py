# external imports
from sqlalchemy.engine import URL
from sqlmodel import create_engine, Session

# internal imports
from ..config.config import DBConfig
from .singleton import Singleton


class Database(metaclass=Singleton):
    db: Session

    _db_name: str
    _host: str
    _port: str
    _username: str
    _password: str

    def __init__(self):
        pass

    def setup(self, config: DBConfig):
        """setup db object for access"""

        self._db_name = config.name
        self._host = config.host
        self._port = config.port
        self._username = config.user
        self._password = config.pswd

        pg_conn_str = self.create_pg_connection_string()

        engine = create_engine(pg_conn_str, echo=True)
        self.db = Session(engine)

    def create_pg_connection_string(self) -> str:
        url = URL.create(
            drivername="postgresql+psycopg2",
            username=self._username,
            password=self._password or "",
            host=self._host,
            database=self._db_name,
            port=self._port,
        )

        return url

    def get_db_connection(self):
        return self.db
