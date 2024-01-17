from utils import load_json, load_pkl, save_json, save_pkl
import os


class Repository:
    def __init__(
        self,
        repo_owner: str,
        repo_name: str,
        save_path: str,
        repo_path: str,
        language: list = [],
    ):
        """
        Folder's structure:
        --repo_path
        |   --repo_owner
        |   |   --repo_name
        |   |   |   --.git

        --save_path
        |   --repo_name
        |   |   --extracted_info.json
        |   |   --commit_ids.pkl
        |   |   --repo_commits_<num>.pkl
        |   |   --repo_features.csv
        |   |   --repo_bug_fix.json
        """
        self.owner = repo_owner
        self.name = repo_name
        self.save_path = os.path.abspath(save_path)
        self.repo_path = os.path.abspath(repo_path)
        self.language = language
        if not os.path.exists(os.path.join(self.save_path, self.name)):
            os.mkdir(os.path.join(self.save_path, self.name))
        self.paths = {
            "extracted_info": os.path.join(
                self.save_path, self.name, "extracted_info.json"
            ),
            "ids": os.path.join(self.save_path, self.name, "commit_ids.pkl"),
            "commits": os.path.join(self.save_path, self.name, "repo_commits_{}.pkl"),
            "features": os.path.join(self.save_path, self.name, "repo_features.pkl"),
            "bug_fix": os.path.join(self.save_path, self.name, "repo_bug_fix.json"),
        }
        self.ids = {}
        self.commits = {}
        self.features = {}

    # load
    def load_ids(self):
        self.ids = load_pkl(self.paths["ids"])

    def load_commits(self, num):
        self.commits = load_pkl(self.paths["commits"].format(num))

    def load_features(self):
        self.features = load_pkl(self.paths["features"])

    # get
    def get_last_config(self):
        config = load_json(self.paths["extracted_info"])
        if config:
            return config
        return {
            "language": self.language,
        }

    def get_ids_path(self):
        return self.paths["ids"]

    def get_commits_path(self, num):
        return self.paths["commits"].format(num)

    def get_repo_path(self):
        return self.repo_path

    def get_path(self):
        return os.path.join(self.repo_path, self.owner, self.name)

    def get_bug_fix_path(self):
        return self.paths["bug_fix"]

    def get_csv_path(self):
        return self.paths["csv"]
    
    def get_language(self):
        return self.language

    # save
    def save_ids(self):
        save_pkl(self.ids, self.paths["ids"])

    def save_commits(self, num):
        save_pkl(self.commits, self.paths["commits"].format(num))

    def save_bug_fix(self, ids):
        bug_fix = load_json(self.paths["bug_fix"])
        if not bug_fix:
            bug_fix = []
        existed_ids = map(lambda x: x["fix_commit_hash"], bug_fix)
        for id in ids:
            if id not in existed_ids:
                bug_fix.append(
                    {"fix_commit_hash": id, "repo_name": f"{self.owner}/{self.name}"}
                )
        save_json(bug_fix, self.paths["bug_fix"])

    def save_features(self):
        save_pkl(self.features, self.paths["features"])

    def save_config(self, config):
        cfg = {
            "owner": self.owner,
            "name": self.name,
            "repo_path": self.repo_path,
            "save_path": self.save_path,
        }
        for key, val in config.items():
            cfg[key] = val
        save_json(cfg, self.paths["extracted_info"])
