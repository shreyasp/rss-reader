# builtin imports
import os

# external imports
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

# internal imports except routers
from .config.config import Config
from .utils.cache import Cache
from .utils.message_queue import MessageQueue

# import all routers here
from .models.app_data import root_router
from .models.users import users_router


class RSSReaderApplication:
    _mode: str
    _fastapi_app: FastAPI
    _config: Config
    _cache: Cache
    _queue: MessageQueue

    def __init__(self, web_app:FastAPI, app_mode:str):
        self._fastapi_app = web_app
        self._mode=app_mode

        self._get_config()
        if self._config.app_config.debug:
            self._fastapi_app.debug = True
    
        self._setup_middleware()
        self._setup_routers()
        self._setup_application()
        self._setup_message_queue()

    def _setup_middleware(self):
        origins = ["*"]
        self._fastapi_app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routers(self):
        self._fastapi_app.include_router(root_router)
        self._fastapi_app.include_router(users_router)

    def _get_config(self):
        self._config = Config(self._mode)


    def _setup_application(self):
        self._cache = Cache()
        self._cache.setup(self._config.cache_config)


    def _setup_message_queue(self):
        self._queue = MessageQueue()
        self._queue.setup()



# initialize fastapi
app = FastAPI()


# setup application
mode = os.getenv("APP_MODE")
RSSReaderApplication(app, mode)
