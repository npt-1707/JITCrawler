from abc import ABC, abstractmethod
from time import time
from .utils.utils import check_path
import json

class Config:
    def __init__(self, 
                mode:str,
                repo_name:str,
                repo_owner:str,
                save_path="data/save",
                repo_path="data/repo",
                extract_features=False,
                num_commits_per_file=1000):
        '''
        Parameters:
        - mode: str
            - "local": use local repo
            - "remote": use remote repo
        - repo_name: str
            - name of the repo
        - repo_owner: str
            - owner of the repo
        - save_path: str
            - path to save the files extracted from the repo
        - repo_path: str
            - path to the repo
        - extract_features: bool
            - whether to extract features or not
        - num_commits_per_file: int
            - number of commits to extract per file
        '''
        assert mode in ["local", "remote"], f"Invalid mode: {mode}. Mode must be in {['local', 'remote']}"
        self.mode = mode
        self.repo_name = repo_name
        self.repo_owner = repo_owner
        self.save_path = check_path(save_path)
        self.repo_path = check_path(repo_path)
        self.num_commits_per_file = num_commits_per_file
        self.extract_features = extract_features
        print(f"Config:\n{self}")
        
    def __str__(self):
        return json.dumps(self.__dict__, indent=4)

