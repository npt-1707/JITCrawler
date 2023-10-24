import os
import math
import subprocess
import re
import pickle
import json


def clone_repo(clone_path, name, url):
    """
    Clones a repository to the current directory
    """
    if name not in os.listdir(clone_path):
        command = "git clone {}"
        os.system(command.format(url))
    else:
        print(f"Existed '{name}' repository")
        command = "git pull"
        os.system(command)


def exec_cmd(command):
    """
    Get ouput of executing a command
    """
    # pip = os.popen(command)
    # output = pip.buffer.read().decode(encoding="utf8", errors="ignore")
    # output = output.strip("\n").split("\n") if output else []
    # return output
    result = subprocess.run(command,
                            shell=True,
                            capture_output=True,
                            text=False)
    output = result.stdout.strip(b"\n").split(b"\n") if result.stdout else []
    output = [
        line.decode(encoding="utf8", errors="replace") for line in output
    ]
    return output


def get_commit_hashes(start=None, end=None):
    """
    Get commit hashes of a repository between `start` and `end`
    """
    if start is None and end is None:
        command = 'git log --all --no-decorate --no-merges --pretty=format:"%H"'
    elif start is None:
        command = f'git log --all --before={end} --no-decorate --no-merges --pretty=format:"%H"'
    else:
        command = f'git log --all --after={start} --no-decorate --no-merges --pretty=format:"%H"'
    return exec_cmd(command)


def split_diff_log(file_diff_log):
    """
    Split the log of a commit into a list of diff
    """
    files_log, file_log = [], []
    for line in file_diff_log:
        if line[:10] == "diff --git":
            if file_log:
                files_log.append(file_log)
                file_log = []

        file_log.append(line)

    if file_log:
        files_log.append(file_log)

    return files_log


def is_numeric_string(string):
    # Regular expression pattern to match decimal numbers
    pattern = r"^[+-]?\d*\.?\d+$"

    # Check if the string matches the pattern
    return re.match(pattern, string) is not None


def process_one_line_blame(log):
    log = log.split()
    while not is_numeric_string(log[1]):
        log.remove(log[1])
    log = " ".join(log)

    pattern = r'(\S+)\s+(\d+)\s+\((.*?)\s+(\d+)\s+[-+]\d{4}\s+(\d+)\)(.*)'

    # Extract the information using the pattern
    match = re.match(pattern, log)

    if match:
        # Extract the matched components
        commit_id = match.group(1)
        blame_line_a = int(match.group(2))
        author_name = match.group(3)
        date = int(match.group(4))
        blame_line_b = int(match.group(5))

        # Create a dictionary with the extracted information
        return {
            "blame_id": commit_id,
            "blame_line_a": blame_line_a,
            "blame_author": author_name,
            "blame_date": date,
            "blame_line_b": blame_line_b,
        }
    return None


def get_file_blame(file_blame_log):
    file_blame_log = [log.strip("\t").strip() for log in file_blame_log]
    id2line = {}
    for _, log in enumerate(file_blame_log):
        line_blame = process_one_line_blame(log)

        if not line_blame["blame_id"] in id2line:
            id2line[line_blame["blame_id"]] = {
                "id": line_blame["blame_id"],
                "author": line_blame["blame_author"],
                "time": line_blame["blame_date"],
                "ranges": [],
            }

        idb = id2line[line_blame["blame_id"]]
        this_line = line_blame["blame_line_b"]
        ranges = idb["ranges"]
        if ranges:
            if this_line == ranges[-1]["end"] + 1:
                ranges[-1]["end"] += 1
            else:
                ranges.append({"start": this_line, "end": this_line})
        else:
            ranges.append({"start": this_line, "end": this_line})
    return id2line


def find_file_author(blame, file_path):
    if not file_path in blame:
        return [], []
    author = set()
    commit = set()
    file_blame = blame[file_path]["id2line"]
    for elem in file_blame:
        name = file_blame[elem]["author"]
        commit.add(file_blame[elem]["id"])
        author.add(name)
    return list(commit), list(author)


def get_subs_dire_name(fileDirs):
    """
    Get the subsystem, directory, and file from a file path
    """
    fileDirs = fileDirs.split("/")
    if len(fileDirs) == 1:
        subsystem = "root"
        directory = "root"
    else:
        subsystem = fileDirs[0]
        directory = "/".join(fileDirs[0:-1])
    file_name = fileDirs[-1]

    return subsystem, directory, file_name


def calc_entrophy(totalLOCModified, locModifiedPerFile):
    """
    Calculate the entrophy
    """
    entrophy = 0
    for fileLocMod in locModifiedPerFile:
        if fileLocMod != 0:
            avg = fileLocMod / totalLOCModified
            entrophy -= avg * math.log(avg, 2)

    return entrophy


def check_fix(msg):
    # List of keywords indicating bug fixes
    bug_keywords = ["fix", "bug", "issue"]
    wrong_keywords = ["fix typo", "fix build", "non-fix"]
    if any(keyword in msg for keyword in bug_keywords):
        if not any(keyword in msg for keyword in wrong_keywords):
            return 1
    return 0


def get_prev_time(blame, file):
    if not file in blame:
        return 0

    max_time = 0
    for elem in blame[file].items():
        elem = elem[1]
        max_time = max(elem["time"], max_time)
    return max_time


def get_author_exp(author_exp):
    exp = 0
    for file in list(author_exp.items())[1:]:
        exp += len(file[1])
    return exp


def get_author_rexp(author_exp, now):
    rexp = 0
    for file in list(author_exp.items())[1:]:
        for t in file[1]:
            age = (now - t) / 86400
            age = max(age, 0)
            rexp += 1 / (age + 1)
    return rexp


def get_author_sexp(author_exp, subsystems):
    sexp = 0
    for file in author_exp.items():
        file_path = file[0]
        sub, _, _ = get_subs_dire_name(file_path)
        if sub in subsystems:
            sexp += 1
    return sexp


def calu_modified_lines(file):
    add_line, del_line = 0, 0
    t_line = file["meta_a"]["lines"] if "meta_a" in file else 0
    for ab in file["content"]:
        if "a" in ab:
            del_line += len(ab["a"])
        if "b" in ab:
            add_line += len(ab["b"])

    return add_line, del_line, t_line


def get_programming_language(file_path):
    extension = os.path.splitext(file_path)[1].lower()

    language_map = {
        ".py": "Python",
        ".java": "Java",
        ".cpp": "C++",
        ".c": "C",
        ".js": "JavaScript",
        ".rb": "Ruby",
        ".swift": "Swift",
        ".go": "Go",
        ".rs": "Rust",
        ".ts": "TypeScript",
        ".php": "PHP",
        # ".html": "HTML",
        # ".css": "CSS",
        # ".pl": "Perl",
        # ".sh": "Bash",
        # ".lua": "Lua",
        # ".sql": "SQL",
        ".cc": "C++",
        # ".h": "C",
        # Add more extensions and programming languages as needed
    }

    return language_map.get(extension, None)


def load_pkl(path):
    if not os.path.exists(path):
        return {}
    with open(path, "rb") as f:
        data = pickle.load(f)
    return data


def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "rb") as f:
        data = json.load(f)
    return data


def save_pkl(data, path):
    with open(path, "wb") as f:
        pickle.dump(data, f)


def save_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)