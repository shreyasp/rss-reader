# external imports
from fastapi import APIRouter, status
from fastapi import __version__ as fastapi_version

# builtin imports
import git 
import os 

# data model to represent the application level metadata such as
# app_name, app_version, framework_version, etc.
class AppMetadata:
    app_version = ""
    fastapi_version = ""

    def __init__(self):
        self._get_git_head_commit()
        self._get_fastapi_version()
    
    def _get_git_head_commit(self):
        repo = git.Repo(path=os.getcwd(), search_parent_directories=True)
        head = repo.active_branch.checkout()
        self.app_version = head.commit.hexsha

    def _get_fastapi_version(self):
        self.fastapi_version = fastapi_version


# represents router that can be used to define endpoints that can be
# present at the root level of the application
root_router = APIRouter(tags=["application-data"])

@root_router.get(
    path="/ping",
    name="ping",
    description="checks application sanity",
    status_code=status.HTTP_200_OK
)
def ping():
    return {"ping": "pong"}


@root_router.get(
    path="/version",
    name="version",
    summary="describes application metadata",
    description="returns fastapi_version, deployed commit hash",
    status_code=status.HTTP_200_OK
)
def version():
    amd = AppMetadata()
    version_data = {
        "app_version": amd.app_version,
        "fastapi_version": amd.fastapi_version,
    }

    return version_data

