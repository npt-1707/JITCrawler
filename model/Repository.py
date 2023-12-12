from .Config import Config
from .utils.utils import clone_repo
import os

class Repository:
    def __init__(self, config:Config):
        self.config = config
        self.repo = {
            "ids": {},
            "commits": {}
        }
        self.files = {
            "config": "config.json",
            "ids": "repo_ids.pkl",
            "commits": "repo_commits_{}.pkl",
            "features": "repo_features.pkl",
        }
        self.load()       
            
    def load(self):
        if self.config.mode == "remote":
            self.clone_repo()
        
        save_path = os.path.join(self.config.save_path, self.config.repo_owner, self.config.repo_name)
        if os.path.isdir(save_path):
            files = os.listdir(save_path)
            if "config.json" in files:
                print("Loading existing repo...")
                self.load_existing()
        else:
            self.create_new()
    
    def clone_repo(self):
        clone_url = f"https://github.com/{self.config.repo_owner}/{self.config.repo_name}.git"
        cur_dir = os.getcwd()
        os.chdir(self.config.repo_path)
        clone_repo(self.config.repo_path, self.config.repo_owner, self.config.repo_name, clone_url)
        os.chdir(cur_dir)
    
    def load_existing(self, args):
        pass
    
    def create_new(self, args):
        pass
    