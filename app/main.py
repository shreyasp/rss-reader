from fastapi import FastAPI, __version__ as fastapi_version
from fastapi.middleware.cors import CORSMiddleware

import git

app = FastAPI(debug=True)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
def ping():
    return {"ping": "pong"}


@app.get("/version")
def version():
    amd = AppMetadata()
    return {
        "app_version": amd.app_version,
        "fastapi_version": amd.fastapi_version,
        "api_version": app.version
    }

class AppMetadata:
    app_version = ""
    fastapi_version = ""

    def __init__(self):
        self._get_git_head_commit()
    
    def _get_git_head_commit(self):
        repo = git.Repo(search_parent_directories=True)
        head_commit = repo.commit("main")
        self.app_version = head_commit.hexsha

    def _get_fastapi_version(self):
        self.fastapi_version = fastapi_version
