import os
import numpy as np
import pandas as pd
from github import Github
from tqdm import tqdm
from utils.utils import *
import pickle


class RepositoryExtractor:
    def __init__(self, g: Github, owner: str, name: str, path: str, end):
        self.repo = g.get_repo(f"{owner}/{name}")
        self.clone_path = os.path.join(path, "repo", owner)
        self.repo_path = os.path.join(self.clone_path, name)
        self.save_path = os.path.join(path, "save")
        self.commits_path = os.path.join(
            self.save_path, f"commits_{name}_{end}.pkl")
        # self.features_path = os.path.join(
        #     self.save_path, f"features_{name}_{end}.pkl")
        # self.files_path = os.path.join(
        #     self.save_path, f"files_{name}_{end}.pkl")
        # self.authors_path = os.path.join(
        #     self.save_path, f"authors_{name}_{end}.pkl")
        self.csv_path = os.path.join(self.save_path, f"{owner}_{name}_{end}.csv")
        if not os.path.exists(self.clone_path):
            os.makedirs(self.clone_path)
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)
        # clone the repository
        os.chdir(self.clone_path)
        clone_repo(self.clone_path, self.repo.name, self.repo.clone_url)

        # get the commit hashes from start to end
        os.chdir(self.repo_path)
        self.commit_ids = get_commit_hashes(end)[::-1]
        print(f"Number of commits before {end}: {len(self.commit_ids)}")

        # load the existing commits info, files info, authors info
        self.commits = {}
        self.files = {}
        self.authors = {}
        self.features = {}

        if os.path.exists(self.commits_path):
            with open(self.commits_path, "rb") as f:
                self.commits = pickle.load(f)

        # if os.path.exists(self.files_path):
        #     with open(self.files_path, "rb") as f:
        #         self.files = pickle.load(f)

        # if os.path.exists(self.authors_path):
        #     with open(self.authors_path, "rb") as f:
        #         self.authors = pickle.load(f)
                
        # if os.path.exists(self.features_path):
        #     with open(self.features_path, "rb") as f:
        #         self.features = pickle.load(f)

        # get main language
        self.language = self.repo.language

    def get_repo_commits_info(self, main_language_only=False):
        if main_language_only:
            languages = [self.language]
        else:
            languages = []
        print("Collecting commits information ...")
        for commit_id in tqdm(self.commit_ids):
            if commit_id not in self.commits:
                commit = get_commit_info(commit_id, languages)
                if not commit["diff"]:
                    continue
                self.commits[commit_id] = commit

        with open(self.commits_path, "wb") as f:
            pickle.dump(self.commits, f)

    def extract_k_features(self, commit_id):
        commit = self.commits[commit_id]
        commit_date = commit["commit_date"]
        commit_message = commit["commit_msg"]
        commit_author = commit["author"]
        commit_diff = commit["diff"]
        commit_blame = commit["blame"]

        la, ld, lt, age, nuc = (0, 0, 0, 0, 0)
        subs, dirs, files = [], [], []
        totalLOCModified = 0
        locModifiedPerFile = []
        authors = []
        ages = []
        author_exp = self.authors.get(commit_author, {})

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
            ld += result[0]
            lt += result[1]

            totalLOCModified += la + ld
            locModifiedPerFile.append(totalLOCModified)

            file = self.files.get(file_path, {"author": [], "nuc": 0})
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
            self.files[file_path] = file

            if file_path in author_exp:
                author_exp[file_path].append(commit_date)
            else:
                author_exp[file_path] = [commit_date]
            self.authors[commit_author] = author_exp

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

    def extrac_repo_k_features(self):
        print("Extracting features ...")
        for commit_id in tqdm(self.commits):
            if commit_id not in self.features:
                k_features = self.extract_k_features(commit_id)
                self.features[commit_id] = k_features

        # with open(self.files_path, "wb") as f:
        #     pickle.dump(self.files, f)

        # with open(self.authors_path, "wb") as f:
        #     pickle.dump(self.authors, f)

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
        for commit_feature in self.features.values():
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
        pd.DataFrame(data).to_csv(self.csv_path)
        print("Done")
