from .Repository import Repository
from .Dict import create_dict
from utils import save_pkl, split_sentence
from datetime import datetime
import time
import pandas as pd
import numpy as np
import os


class Processor:
    def __init__(self, save_path: str, save: bool = True):
        self.path = os.path.abspath(save_path)
        self.save = save

    def set_repo(self, repo: Repository):
        self.repo = repo
        self.repo_save_path = os.path.join(self.path, self.repo.owner, self.repo.name)
        self.feature_path = os.path.join(self.repo_save_path, "feature")
        self.commit_path = os.path.join(self.repo_save_path, "commit")
        self.df = None
        self.ids = None
        self.messages = None
        self.cc2vec_codes = None
        self.deepjit_codes = None
        self.simcom_codes = None
        self.labels = None

    def run(self, szz_output, extracted_date):
        self.create_dirs()
        szz_bug_ids = self.process_szz_output(szz_output)
        time_upper_limit = 0
        if szz_bug_ids:
            date_df = self.process_features(szz_bug_ids, cols=["_id", "date"])
            time_median = self.cal_median_fix_time(szz_bug_ids, date_df)
            time_upper_limit = (
                datetime.strptime(extracted_date, "%Y-%m-%d").timestamp()
                if extracted_date
                else int(time.time())
            ) - time_median

        self.df = self.process_features(
            bug_ids=szz_bug_ids, cols=[], time_upper_limit=time_upper_limit
        )
        self.process_diffs(szz_bug_ids)
        if self.save:
            self.to_dataset()

    def create_dirs(self):
        """
        Create directories for storing data
        """
        if not os.path.exists(self.repo_save_path):
            os.makedirs(self.repo_save_path)
        if not os.path.exists(self.feature_path):
            os.mkdir(self.feature_path)
        if not os.path.exists(self.commit_path):
            os.mkdir(self.commit_path)

    def process_szz_output(self, szz_output):
        """
        Process szz output to get bug ids
        """
        szz_bug_ids = {}
        if szz_output:
            repo_name = szz_output[0]["repo_name"]
            assert repo_name == os.path.join(
                self.repo.owner, self.repo.name
            ), f"Unmatch szz output vs repo's info: got {repo_name} and {self.repo.owner}/{self.repo.name}"
            for out in szz_output:
                if out["inducing_commit_hash"]:
                    for id in out["inducing_commit_hash"]:
                        if id not in szz_bug_ids:
                            szz_bug_ids[id] = []
                        else:
                            szz_bug_ids[id].append(out["fix_commit_hash"])
        return szz_bug_ids

    def process_features(self, bug_ids, cols=[], time_upper_limit=None):
        """
        Convert features to dataframe, and add bug label
        """

        def is_sorted_by_date(features):
            dates = [features[id]["date"] for id in features]
            return dates == sorted(dates)

        self.repo.load_features()
        assert is_sorted_by_date(self.repo.features), "Features are not sorted by date"
        if not cols:
            cols = [
                "_id",
                "date",
                "bug",
                "ns",
                "nd",
                "nf",
                "entropy",
                "la",
                "ld",
                "lt",
                "fix",
                "ndev",
                "age",
                "nuc",
                "exp",
                "rexp",
                "sexp",
            ]
        data = {key: [] for key in cols}
        for commit_id in self.repo.features:
            feature = self.repo.features[commit_id]
            if time_upper_limit and feature["date"] > time_upper_limit:
                continue
            for key in cols:
                if key == "bug":
                    data[key].append(1 if commit_id in bug_ids else 0)
                else:
                    data[key].append(feature[key])
        self.repo.features = {}
        return pd.DataFrame(data)

    def cal_median_fix_time(self, bug_ids, date_df):
        """
        Calculate median fix time for each bug
        """
        fix_times = []
        for bug_id, fix_ids in bug_ids.items():
            if bug_id in date_df["_id"].values:
                bug_date = date_df[date_df["_id"] == bug_id]["date"].values[0]
                fix_dates = date_df[date_df["_id"].isin(fix_ids)]["date"].values
                for fix_date in fix_dates:
                    fix_time = fix_date - bug_date
                    fix_time = fix_time / 86400
                    fix_times.append(fix_time)
        time_median = np.median(fix_times)
        return time_median

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

        df_ids = self.df["_id"].values

        for i in range(num_files):
            self.repo.load_commits(i)
            for commit_id in self.repo.commits:
                if commit_id not in df_ids:
                    continue
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
            os.path.join(self.feature_path, "features.csv"),
            index=False,
        )
        code_msg_dict = create_dict(self.messages, self.deepjit_codes)
        save_pkl(code_msg_dict, os.path.join(self.commit_path, "dict.pkl"))
        save_pkl(
            [self.ids, self.messages, self.cc2vec_codes, self.labels],
            os.path.join(self.commit_path, "cc2vec.pkl"),
        )
        save_pkl(
            [self.ids, self.messages, self.deepjit_codes, self.labels],
            os.path.join(self.commit_path, "deepjit.pkl"),
        )
        save_pkl(
            [self.ids, self.messages, self.simcom_codes, self.labels],
            os.path.join(self.commit_path, "simcom.pkl"),
        )
