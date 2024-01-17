from .Repository import Repository
from .Dict import Dict
from utils import save_pkl, split_sentence, create_dict
import pandas as pd
import numpy as np
import os


class Processor:
    def __init__(self, save_path: str, save: bool = True):
        self.path = os.path.abspath(save_path)
        self.save = save
        self.repo = None
        self.feature_path = None
        self.commit_path = None
        self.df = None
        self.ids = None
        self.messages = None
        self.cc2vec_codes = None
        self.deepjit_codes = None
        self.simcom_codes = None
        self.labels = None

    def set_repo(self, repo: Repository):
        self.repo = repo
        self.feature_path = os.path.join(self.path, self.repo.name, "feature")
        self.commit_path = os.path.join(self.path, self.repo.name, "commit")

    def run(self, szz_output):
        self.create_dirs()
        szz_bug_ids = self.process_szz_output(szz_output)
        self.process_features(szz_bug_ids)
        self.process_diffs(szz_bug_ids)
        if self.save:
            self.to_dataset()

    def create_dirs(self):
        """
        Create directories for storing data
        """
        if not os.path.exists(os.path.join(self.path, self.repo.name)):
            os.mkdir(os.path.join(self.path, self.repo.name))
        if not os.path.exists(self.feature_path):
            os.mkdir(self.feature_path)
        if not os.path.exists(self.commit_path):
            os.mkdir(self.commit_path)

    def process_szz_output(self, szz_output):
        """
        Process szz output to get bug ids
        """
        if szz_output:
            repo_name = szz_output[0]["repo_name"]
            assert (
                repo_name == f"{self.repo.owner}/{self.repo.name}"
            ), f"Unmatch szz output vs repo's info: got {repo_name} and {self.repo.owner}/{self.repo.name}"
            szz_bug_ids = set()
            for out in szz_output:
                for id in out["inducing_commit_hash"]:
                    szz_bug_ids.add(id)
        else:
            szz_bug_ids = set()
        return szz_bug_ids

    def process_features(self, bug_ids):
        """
        Convert features to dataframe, and add bug label
        """

        def is_sorted_by_date(features):
            dates = [features[id]["date"] for id in features]
            return dates == sorted(dates)

        self.repo.load_features()
        assert is_sorted_by_date(self.repo.features), "Features are not sorted by date"
        data = {
            "_id": [],
            "date": [],
            "bug": [],
            "ns": [],
            "nd": [],
            "nf": [],
            "entropy": [],
            "la": [],
            "ld": [],
            "lt": [],
            "fix": [],
            "ndev": [],
            "age": [],
            "nuc": [],
            "exp": [],
            "rexp": [],
            "sexp": [],
        }
        for commit_id in self.repo.features:
            feature = self.repo.features[commit_id]
            data["_id"].append(feature["_id"])
            data["date"].append(feature["date"])
            data["bug"].append(1 if feature["_id"] in bug_ids else 0)
            data["ns"].append(feature["ns"])
            data["nd"].append(feature["nd"])
            data["nf"].append(feature["nf"])
            data["entropy"].append(feature["entropy"])
            data["la"].append(feature["la"])
            data["ld"].append(feature["ld"])
            data["lt"].append(feature["lt"])
            data["fix"].append(feature["fix"])
            data["ndev"].append(feature["ndev"])
            data["age"].append(feature["age"])
            data["nuc"].append(feature["nuc"])
            data["exp"].append(feature["exp"])
            data["rexp"].append(feature["rexp"])
            data["sexp"].append(feature["sexp"])
        self.df = pd.DataFrame(data)

    def process_diffs(self, bug_ids):
        """
        Process diffs to get format [ids, messages, codes, and labels]
        """
        cfg = self.repo.get_last_config()
        num_files = (
            cfg["num_files"]
            if cfg["last_file_num_commits"] == 0
            else cfg["num_files"] + 1
        )

        self.ids = []
        self.messages = []
        self.cc2vec_codes = []
        self.deepjit_codes = []
        self.simcom_codes = []
        self.labels = []

        for i in range(num_files):
            self.repo.load_commits(i)
            for commit_id in self.repo.commits:
                commit = self.repo.commits[commit_id]
                (
                    id,
                    mes,
                    cc2vec_commit,
                    deepjit_commit,
                    simcom_commit,
                ) = self.process_one_commit(commit)
                label = 1 if id in bug_ids else 0
                self.ids.append(id)
                self.messages.append(mes)
                self.cc2vec_codes.append(cc2vec_commit)
                self.deepjit_codes.append(deepjit_commit)
                self.simcom_codes.append(simcom_commit)
                self.labels.append(label)
                del commit, id, mes, cc2vec_commit, deepjit_commit, simcom_commit, label
        self.code_dict = create_dict(self.messages, self.deepjit_codes)

    def process_one_commit(self, commit):
        id = commit["commit_id"]
        mes = commit["message"].strip()
        mes = split_sentence(mes)
        mes = " ".join(mes.split(" ")).lower()
        cc2vec_commit = []
        deepjit_commit = []
        simcom_commit = []
        for file in commit["files"]:
            cc2vec_file = {"added_code": [], "removed_code": []}
            for hunk in commit["diff"][file]["content"]:
                if "ab" in hunk:
                    continue
                if "a" in hunk:
                    for line in hunk["a"]:
                        line = line.strip()
                        line = split_sentence(line)
                        line = " ".join(line.split(" ")).lower()
                        if len(cc2vec_file["removed_code"]) <= 10:
                            cc2vec_file["removed_code"].append(line)
                        deepjit_commit.append(line)
                if "b" in hunk:
                    for line in hunk["b"]:
                        line = line.strip()
                        line = split_sentence(line)
                        line = " ".join(line.split(" ")).lower()
                        if len(cc2vec_file["added_code"]) <= 10:
                            cc2vec_file["added_code"].append(line)
                        deepjit_commit.append(line)
            deepjit_commit = deepjit_commit[:10]
            if len(cc2vec_commit) == 10:
                continue
            cc2vec_commit.append(cc2vec_file)
            added_code = " ".join(cc2vec_file["added_code"])
            removed_code = " ".join(cc2vec_file["removed_code"])
            simcom_commit.append(f"{added_code} {removed_code}")
        return id, mes, cc2vec_commit, deepjit_commit, simcom_commit

    def to_dataset(self):
        """
        Save processed data to dataset
        """
        self.df.to_csv(
            os.path.join(self.path, self.repo.name, "feature", "features.csv"),
            index=False,
        )
        code_msg_dict = create_dict(self.messages, self.deepjit_codes)
        save_pkl(
            code_msg_dict, os.path.join(self.path, self.repo.name, "commit", "dict.pkl")
        )
        save_pkl(
            [self.ids, self.messages, self.cc2vec_codes, self.labels],
            os.path.join(self.path, self.repo.name, "commit", "cc2vec.pkl"),
        )
        save_pkl(
            [self.ids, self.messages, self.deepjit_codes, self.labels],
            os.path.join(self.path, self.repo.name, "commit", "deepjit.pkl"),
        )
        save_pkl(
            [self.ids, self.messages, self.simcom_codes, self.labels],
            os.path.join(self.path, self.repo.name, "commit", "simcom.pkl"),
        )