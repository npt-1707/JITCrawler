from .Repository import Repository
from utils import *
import time
from tqdm import tqdm
import numpy as np
import pandas as pd


class Extractor:
    def __init__(
        self,
        start: str = None,
        end: str = None,
        num_commits_per_file: int = 5000,
        language: list = [],
        save: bool = True,
        force_reextract: bool = False,
    ):
        self.start = start
        self.end = end
        self.date = int(time.time())
        self.num_commits_per_file = num_commits_per_file
        self.last_file_num_commits = 0
        self.num_files = 0
        self.language = language
        self.save = save
        self.force_reextract = force_reextract

    def set_repo(self, repo: Repository):
        self.repo = repo
        if self.force_reextract:
            print("Start extracting repository ...")
            self.reset_repo()
        else:
            print("Continue extracting repository ...")
        self.load_config(repo.get_last_config())

    def load_config(self, config):
        keys = [
            "num_commits_per_file",
            "last_file_num_commits",
            "num_files",
            "language",
        ]
        if config:
            for key in keys:
                if key in config:
                    setattr(self, key, config[key])

    def reset_repo(self):
        for path in self.repo.paths:
            if os.path.exists(self.repo.paths[path]):
                os.remove(self.repo.paths[path])

    def save_config(self):
        config = {
            "date": self.date,
            "num_commits_per_file": self.num_commits_per_file,
            "last_file_num_commits": self.last_file_num_commits,
            "num_files": self.num_files,
            "language": self.language,
        }
        self.repo.save_config(config)

    def run(self):
        cur_dir = os.getcwd()
        os.chdir(self.repo.get_path())
        found_ids = self.extract_repo_commit_ids()[::-1]
        self.repo.load_ids()
        for id in found_ids:
            if id not in self.repo.ids:
                self.repo.ids[id] = -1
        self.extract_repo_commit_diffs()
        self.extract_repo_commits_features()
        self.date = int(time.time())
        if self.save:
            self.save_config()
        os.chdir(cur_dir)

    def extract_repo_commit_ids(self):
        """
        Extract the repository's commit ids
        """
        return get_commit_hashes(self.start, self.end)

    def extract_one_commit_diff(self, commit_id: str, languages: []):
        """
        Input:
            commit_id: the id of the commit
        Output:
            commit: dict of commit's information
                |- commit_id: the id of the commit
                |- parent_id: the id of the parent commit
                |- subject: the subject of the commit
                |- message: the message of the commit
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
                file_name_a = (
                    file_diff["from"]["file"]
                    if file_diff["rename"] or file_diff["from"]["mode"] != "0000000"
                    else file_diff["to"]["file"]
                )
                file_name_b = (
                    file_diff["to"]["file"]
                    if file_diff["rename"] or file_diff["to"]["mode"] != "0000000"
                    else file_diff["from"]["file"]
                )
                if file_diff["is_binary"] or len(file_diff["content"]) == 0:
                    continue

                if file_diff["from"]["mode"] == "0000000":
                    continue

                if len(languages) > 0:
                    file_language = get_programming_language(file_name_b)
                    if file_language not in languages:
                        continue

                command = "git blame -t -n -l {} '{}'"
                file_blame_log = exec_cmd(command.format(parent_id, file_name_a))
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
            "message": commit_msg,
            "author": author,
            "date": int(commit_date),
            "files": files,
            "diff": commit_diff,
            "blame": commit_blame,
        }
        return commit

    def extract_repo_commit_diffs(self):
        print("Collecting commits information ...")
        if not self.num_commits_per_file:
            self.num_commits_per_file = len(self.repo.ids)
        extracting_ids = [id for id in self.repo.ids if self.repo.ids[id] == -1]
        if len(extracting_ids) == 0:
            return
        bug_fix_ids = []
        if self.last_file_num_commits > 0:
            self.repo.load_commits(self.num_files)

        for commit_id in tqdm(extracting_ids):
            try:
                commit = self.extract_one_commit_diff(commit_id, self.language)
                if not commit["diff"]:
                    self.repo.ids[commit_id] = -2
                    continue
                self.repo.commits[commit_id] = commit
                self.repo.ids[commit_id] = self.num_files
                self.last_file_num_commits += 1
                if check_fix(commit["message"]):
                    bug_fix_ids.append(commit_id)
            except Exception:
                self.repo.ids[commit_id] = -3

            if self.last_file_num_commits == self.num_commits_per_file and self.save:
                self.repo.save_commits(self.num_files)
                self.last_file_num_commits = 0
                self.num_files += 1
                self.repo.commits = {}

        if self.save:
            if self.repo.commits:
                self.repo.save_commits(self.num_files)
            self.repo.save_bug_fix(bug_fix_ids)
            self.repo.save_ids()

    def extract_one_commit_features(self, commit):
        commit_id = commit["commit_id"]
        commit_date = commit["date"]
        commit_message = commit["message"]
        commit_author = commit["author"]
        commit_diff = commit["diff"]
        commit_blame = commit["blame"]

        la, ld, lt, age, nuc = (0, 0, 0, 0, 0)
        subs, dirs, files = [], [], []
        totalLOCModified = 0
        locModifiedPerFile = []
        authors = []
        ages = []
        author_exp = self.repo.authors.get(commit_author, {})

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

            file = self.repo.files.get(file_path, {"author": [], "nuc": 0})
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
            self.repo.files[file_path] = file

            if file_path in author_exp:
                author_exp[file_path].append(commit_date)
            else:
                author_exp[file_path] = [commit_date]
            self.repo.authors[commit_author] = author_exp

        feature = {
            "_id": commit_id,
            "date": commit_date,
            "ns": len(subs),
            "nd": len(dirs),
            "nf": len(files),
            "entropy": calc_entropy(totalLOCModified, locModifiedPerFile),
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

    def extract_repo_commits_features(self):
        print("Extracting features ...")
        self.repo.files = {}
        self.repo.authors = {}
        self.repo.features = {}

        num_file = (
            self.num_files if self.last_file_num_commits == 0 else self.num_files + 1
        )
        for num in range(num_file):
            self.repo.load_commits(num)
            for commit_id in tqdm(self.repo.commits):
                commit_feature = self.extract_one_commit_features(
                    self.repo.commits[commit_id]
                )
                self.repo.features[commit_id] = commit_feature
        if self.save:
            self.repo.save_features()
        self.repo.files = {}
        self.repo.authors = {}
