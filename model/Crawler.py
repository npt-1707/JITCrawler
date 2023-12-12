from .Repository import Repository
from .Commit import Commit

class Crawler:
    def __init__(self, args):
        pass

    def extract_one_commit_diff(self, repo: Repository, commit_id:str):
        pass
    
    def extract_repo_commit_diff(self, repo: Repository):
        for id in repo.get_ids():
            commit = repo.get_commit(id)
            self.extract_one_commit_diff(repo, commit)