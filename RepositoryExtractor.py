import os
import numpy as np
import pandas as pd
from github import Github
from tqdm import tqdm
from utils import *
import datetime
import sys
import random


class RepositoryExtractor:

    def config_repo(self, config):
        """
        Input:
            config: dict
                # compulsory parameters
                |- save_path: the root path of the saved data
                |- mode: "local" or "online"
                |- start: start date to extract
                |- end: end date to extract
                
                # optional parameters
                ## for local repo
                |- local_repo_path: the path to the local repositoy
                |- main_language: the main programming language of the repository
                
                ## for online repo
                |- github_token_path: the path to the github token
                |- github_owner: the owner of the github repository
                |- github_repo: the name of the github repository
                
                ## other parameters
                |- excepted_ids_path: the path to the pickle file of the excepted commit ids
                |- extract_features: whether to extract features
                |- rand_num: the number of random commits to extract
                |- to_csv: whether to save the features to csv
                
        Output:
            self.cfg: dict
                |- mode: "local" or "online"
                |- date: the date of checking the repository
                |- main_language: the main programming language of the repository
                |- save_path: the paths saving extractor information
                |- repo_path: the path of the saved repository
                
            self.repo: dict
                |- ids: the list of commit ids
                |- commits: the dict of commits information
                |- features: the dict of commits features
                |- authors: the dict of authors 
                |- files: the dict of files 
        """
        self.cfg = {
            "mode": config.mode,
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "start": config.start,
            "end": config.end,
            "rand_num": config.rand_num,
            "extract_features": config.extract_features,
            "excepted_ids_path": config.excepted_ids_path,
            "ids_path": config.ids_path,
            "num_commits_per_file": config.num_commits_per_file,
            "num_files": 0,
            "last_file_num_commits": 0,
            "to_csv": config.to_csv,
        }

        if config.mode == "local":
            self.init_local_repo(config)
        elif config.mode == "online":
            self.init_online_repo(config)

        save_path = os.path.join(os.path.abspath(config.save_path),
                                 self.cfg["name"])
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        self.cfg["save_path"] = save_path

        self.files = {
            "ids": os.path.join(save_path, "commit_ids.pkl"),
            "commits": os.path.join(save_path, "repo_commits_{}.pkl"),
            "features": os.path.join(save_path, "repo_features.pkl"),
            "authors": os.path.join(save_path, "repo_authors.pkl"),
            "files": os.path.join(save_path, "repo_files.pkl"),
            "config": os.path.join(save_path, "config.json"),
        }

        if os.path.exists(self.files["config"]):
            last_cfg = load_json(self.files["config"])
            self.cfg["num_files"] = last_cfg["num_files"]
            self.cfg["last_file_num_commits"] = last_cfg[
                "last_file_num_commits"]
            del last_cfg

        self.repo = {
            "ids": {},
            "commits": {},
            "features": {},
            "authors": {},
            "files": {},
        }
        self.repo["ids"] = load_pkl(self.files["ids"])
        self.run()
        save_json(self.cfg, self.files["config"])

    def run(self):
        """
        Extract the repository information and check for uncommited files
        """
        print(f"Running repo {self.cfg['name']} ...")
        cur_dir = os.getcwd()
        os.chdir(self.cfg["repo_path"])
        if self.cfg["ids_path"]:
            ids = load_pkl(self.cfg["ids_path"])
        else:
            ids = get_commit_hashes(start=self.cfg["start"],
                                    end=self.cfg["end"])[::-1]
            if self.cfg["excepted_ids_path"]:
                excepted_ids = load_pkl(self.cfg["excepted_ids_path"])
                ids = list(set(ids).difference(excepted_ids))
            if self.cfg["rand_num"]:
                ids = random.sample(ids, self.cfg["rand_num"])

        for id in ids:
            if id not in self.repo["ids"]:
                self.repo["ids"][id] = -1
        if not self.cfg["num_commits_per_file"]:
            self.cfg["num_commits_per_file"] = len(self.repo["ids"])
        del ids

        self.extract_repo_commits_info()
        if self.cfg["extract_features"]:
            self.extract_repo_commits_features(to_csv=self.cfg["to_csv"])

        # if self.cfg["mode"] == "local":
        #     self.check_uncommit()
        os.chdir(cur_dir)
        save_pkl(self.repo["ids"], self.files["ids"])

    def init_local_repo(self, config):
        """
        Config the local repository path
        """
        self.cfg["name"] = os.path.basename(
            os.path.normpath(os.path.abspath(config.local_repo_path)))
        self.cfg["main_language"] = config.main_language
        self.cfg["repo_path"] = os.path.abspath(config.local_repo_path)

    def init_online_repo(self, config):
        """
        Config the cloned repository path
        """
        with open(config.github_token_path, "r") as f:
            github_token = f.read().strip()
        g = Github(github_token)
        repo = g.get_repo(f"{config.github_owner}/{config.github_repo}")
        clone_url = repo.clone_url
        root = sys.path[0]
        clone_path = os.path.join(root, "repo")
        if not os.path.exists(clone_path):
            os.makedirs(clone_path)
        clone_repo(clone_path, config.github_repo, clone_url)
        self.cfg["name"] = config.github_repo
        self.cfg["main_language"] = repo.language
        self.cfg["repo_path"] = os.path.join(clone_path, config.github_repo)

    def extract_one_commit_info(self, commit_id, languages=[]):
        """
        Input:
            commit_id: the id of the commit
        Output:
            commit: dict of commit's information
                |- commit_id: the id of the commit
                |- parent_id: the id of the parent commit
                |- subject: the subject of the commit
                |- msg: the message of the commit
                |- author: the author of the commit
                |- date: the date of the commit
                |- files: the list of files in the commit
                |- diff: the dict of files diff in the commit
                |- blame: the dict of files blame in the commit
        """
        command = "git show {} --name-only --pretty=format:'%H%n%P%n%an%n%ct%n%s%n%B%n[ALL CHANGE FILES]'"

        show_msg = exec_cmd(command.format(commit_id))
        show_msg = [msg.strip() for msg in show_msg]
        file_index = show_msg.index("[ALL CHANGE FILES]")

        subject = show_msg[4]
        head = show_msg[:5]
        commit_msg = show_msg[5:file_index]

        parent_id = head[1]
        author = head[2]
        commit_date = head[3]
        commit_msg = " ".join(commit_msg)

        command = "git show {} --pretty=format: --unified=999999999"
        diff_log = split_diff_log(exec_cmd(command.format(commit_id)))
        commit_diff = {}
        commit_blame = {}
        files = []
        for log in diff_log:
            try:
                files_diff = aggregator(parse_lines(log))
            except:
                continue
            for file_diff in files_diff:
                file_name_a = (file_diff["from"]["file"] if file_diff["rename"]
                               or file_diff["from"]["mode"] != "0000000" else
                               file_diff["to"]["file"])
                file_name_b = (file_diff["to"]["file"] if file_diff["rename"]
                               or file_diff["to"]["mode"] != "0000000" else
                               file_diff["from"]["file"])
                if file_diff["is_binary"] or len(file_diff["content"]) == 0:
                    continue

                if file_diff["from"]["mode"] == "0000000":
                    continue

                if len(languages) > 0:
                    file_language = get_programming_language(file_name_b)
                    if file_language not in languages:
                        continue

                command = "git blame -t -n -l {} '{}'"
                file_blame_log = exec_cmd(
                    command.format(parent_id, file_name_a))
                if not file_blame_log:
                    continue
                file_blame = get_file_blame(file_blame_log)

                commit_blame[file_name_b] = file_blame
                commit_diff[file_name_b] = file_diff
                files.append(file_name_b)

        commit = {
            "commit_id": commit_id,
            "parent_id": parent_id,
            "subject": subject,
            "msg": commit_msg,
            "author": author,
            "date": int(commit_date),
            "files": files,
            "diff": commit_diff,
            "blame": commit_blame,
        }
        return commit

    def extract_repo_commits_info(self, main_language_only=True):
        """
        Input:
            main_language_only: whether to only extract commits with main language
        Output:
            self.repo["commits"]: dict of commits information
        """
        if main_language_only:
            languages = [self.cfg["main_language"]]
        else:
            languages = []
        print("Collecting commits information ...")

        if self.cfg["last_file_num_commits"] > 0:
            self.repo["commits"] = load_pkl(self.files["commits"].format(
                self.cfg["num_files"]))

        for commit_id in tqdm(self.repo["ids"].keys()):
            if self.repo["ids"][commit_id] == -1:
                try:
                    commit = self.extract_one_commit_info(commit_id, languages)
                    if not commit["diff"]:
                        self.repo["ids"][commit_id] = -2
                        continue
                    self.repo["commits"][commit_id] = commit
                    self.repo["ids"][commit_id] = self.cfg["num_files"]
                    self.cfg["last_file_num_commits"] += 1
                except Exception:
                    self.repo["ids"][commit_id] = -3

                # if self.cfg["mode"] == "local":
                #     self.repo["commits"]["uncommit"] = self.check_uncommit()
                #     if self.repo["commits"]["uncommit"] is not None:
                #         is_updated = True

                if self.cfg["last_file_num_commits"] == self.cfg[
                        "num_commits_per_file"]:
                    save_pkl(
                        self.repo["commits"],
                        self.files["commits"].format(self.cfg["num_files"]))
                    self.cfg["last_file_num_commits"] = 0
                    self.cfg["num_files"] += 1
                    self.repo["commits"] = {}
        if self.repo["commits"]:
            save_pkl(self.repo["commits"],
                     self.files["commits"].format(self.cfg["num_files"]))
            self.repo["commits"] = {}
        # print(json.dumps(self.repo["ids"], indent=4))

    def extract_one_commit_features(self, commit):
        commit_id = commit["_id"]
        commit_date = commit["date"]
        commit_message = commit["msg"]
        commit_author = commit["author"]
        commit_diff = commit["diff"]
        commit_blame = commit["blame"]

        la, ld, lt, age, nuc = (0, 0, 0, 0, 0)
        subs, dirs, files = [], [], []
        totalLOCModified = 0
        locModifiedPerFile = []
        authors = []
        ages = []
        author_exp = self.repo["authors"].get(commit_author, {})

        for file_elem in list(commit_diff.items()):
            file_path = file_elem[0]
            val = file_elem[1]

            subsystem, directory, filename = get_subs_dire_name(file_path)
            if subsystem not in subs:
                subs.append(subsystem)
            if directory not in dirs:
                dirs.append(directory)
            if filename not in files:
                files.append(filename)

            result = calu_modified_lines(val)
            la += result[0]
            ld += result[1]
            lt += result[2]

            totalLOCModified += la + ld
            locModifiedPerFile.append(totalLOCModified)

            file = self.repo["files"].get(file_path, {"author": [], "nuc": 0})
            file_author = file["author"]
            if commit_author not in file_author:
                file_author.append(commit_author)
            authors = list(set(authors) | set(file_author))

            prev_time = get_prev_time(commit_blame, file_path)
            age = commit_date - prev_time if prev_time else 0
            age = max(age, 0)
            ages.append(age)

            file_nuc = file["nuc"] + 1
            nuc += file_nuc

            file["nuc"] = file_nuc
            self.repo["files"][file_path] = file

            if file_path in author_exp:
                author_exp[file_path].append(commit_date)
            else:
                author_exp[file_path] = [commit_date]
            self.repo["authors"][commit_author] = author_exp

        feature = {
            "_id": commit_id,
            "date": commit_date,
            "ns": len(subs),
            "nd": len(dirs),
            "nf": len(files),
            "entrophy": calc_entrophy(totalLOCModified, locModifiedPerFile),
            "la": la,
            "ld": ld,
            "lt": lt,
            "fix": check_fix(commit_message),
            "ndev": len(authors),
            "age": np.mean(ages) / 86400 if ages else 0,
            "nuc": nuc,
            "exp": get_author_exp(author_exp),
            "rexp": get_author_rexp(author_exp, commit_date),
            "sexp": get_author_sexp(author_exp, subs),
        }
        return feature

    def extract_repo_commits_features(self, to_csv=False):
        print("Extracting features ...")
        self.repo["files"] = load_pkl(self.files["files"])
        self.repo["authors"] = load_pkl(self.files["authors"])

        is_updated = False
        for num_file in range(self.cfg["num_files"] + 1):
            commits = load_pkl(self.files["commits"].format(num_file))
            for commit_id in tqdm(commits):
                if commit_id not in self.repo["features"]:
                    k_features = self.extract_one_commit_features(
                        commits[commit_id])
                    self.repo["features"][commit_id] = k_features
                    is_updated = True

        # if self.cfg["mode"] == "local":
        #     if self.repo["commits"]["uncommit"] is not None:
        #         self.repo["features"][
        #             "uncommit"] = self.extract_one_commit_features("uncommit")
        #         is_update = True
        #     else:
        #         self.repo["features"]["uncommit"] = None

        if is_updated:
            save_pkl(self.repo["files"], self.files["files"])
            save_pkl(self.repo["authors"], self.files["authors"])
            save_pkl(self.repo["features"], self.files["features"])
        self.repo["files"] = {}
        self.repo["authors"] = {}

        if to_csv:
            self.cfg["csv_path"] = os.path.join(self.cfg["save_path"],
                                                "features.csv")
            self.to_csv()

    def to_csv(self):
        print("Saving features to CSV...", end=" ")
        (
            _id,
            date,
            ns,
            nd,
            nf,
            entrophy,
            la,
            ld,
            lt,
            fix,
            ndev,
            age,
            nuc,
            exp,
            rexp,
            sexp,
        ) = ([], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [])
        for commit_feature in self.repo["features"].values():
            _id.append(commit_feature["_id"])
            date.append(commit_feature["date"])
            ns.append(commit_feature["ns"])
            nd.append(commit_feature["nd"])
            nf.append(commit_feature["nf"])
            entrophy.append(commit_feature["entrophy"])
            la.append(commit_feature["la"])
            ld.append(commit_feature["ld"])
            lt.append(commit_feature["lt"])
            fix.append(commit_feature["fix"])
            ndev.append(commit_feature["ndev"])
            age.append(commit_feature["age"])
            nuc.append(commit_feature["nuc"])
            exp.append(commit_feature["exp"])
            rexp.append(commit_feature["rexp"])
            sexp.append(commit_feature["sexp"])
        data = {
            "_id": _id,
            "date": date,
            "ns": ns,
            "nd": nd,
            "nf": nf,
            "entrophy": entrophy,
            "la": la,
            "ld": ld,
            "lt": lt,
            "fix": fix,
            "ndev": ndev,
            "age": age,
            "nuc": nuc,
            "exp": exp,
            "rexp": rexp,
            "sexp": sexp,
        }
        pd.DataFrame(data).to_csv(self.cfg["csv_path"])
        print("Done")

    # def get_commits(self, commit_ids: list):
    #     """
    #     Input:
    #         commit_ids: the list of commit ids
    #     Output:
    #         commits: the list of commits
    #     """
    #     infos = []
    #     features = []
    #     for commit_id in commit_ids:
    #         if commit_id not in self.repo["commits"]:
    #             raise Exception(
    #                 f"Commit id {commit_id} not found in extractor {self.cfg.path['commits']}"
    #             )
    #         infos.append(self.repo["commits"][commit_id])
    #         features.append(self.repo["features"][commit_id])

    #     return infos, features

    # def check_uncommit(self):
    #     command = "git config --get user.name"
    #     author = exec_cmd(command)[0]

    #     command = "git diff --pretty=format: --unified=999999999"
    #     diff_log = exec_cmd(command)
    #     if diff_log == []:
    #         return None
    #     diff_log = split_diff_log(exec_cmd(command))
    #     commit_diff = {}
    #     commit_blame = {}
    #     files = []
    #     languages = [self.cfg["main_language"]]
    #     for log in diff_log:
    #         try:
    #             files_diff = aggregator(parse_lines(log))
    #         except:
    #             continue
    #         for file_diff in files_diff:
    #             file_name_a = (file_diff["from"]["file"] if file_diff["rename"]
    #                            or file_diff["from"]["mode"] != "0000000" else
    #                            file_diff["to"]["file"])
    #             file_name_b = (file_diff["to"]["file"] if file_diff["rename"]
    #                            or file_diff["to"]["mode"] != "0000000" else
    #                            file_diff["from"]["file"])
    #             if file_diff["is_binary"] or len(file_diff["content"]) == 0:
    #                 continue

    #             if file_diff["from"]["mode"] == "000000000":
    #                 continue

    #             file_language = get_programming_language(file_name_b)
    #             if file_language not in languages:
    #                 continue

    #             command = "git blame -t -n -l {} '{}'"
    #             file_blame_log = exec_cmd(
    #                 command.format(self.head, file_name_a))
    #             if not file_blame_log:
    #                 continue
    #             file_blame = get_file_blame(file_blame_log)

    #             commit_blame[file_name_b] = file_blame
    #             commit_diff[file_name_b] = file_diff
    #             files.append(file_name_b)

    #     commit = {
    #         "commit_id": "Uncommit",
    #         "parent_id": self.head,
    #         "subject": None,
    #         "msg": "",
    #         "author": author,
    #         "date": int(datetime.datetime.now().timestamp()),
    #         "files": files,
    #         "diff": commit_diff,
    #         "blame": commit_blame,
    #     }
    #     return commit
