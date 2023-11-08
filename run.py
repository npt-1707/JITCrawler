import os, argparse, subprocess
from RepositoryExtractor import RepositoryExtractor
def get_params():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=str, default="gerrit")
    parser.add_argument("--prj", type=str, default="")
    parser.add_argument("--mode", type=str, default="local")
    parser.add_argument("--local_repo_path", type=str)
    parser.add_argument("--ids_path", type=str, default="")
    parser.add_argument("--num_commits_per_file", type=int, default=5000)
    parser.add_argument("--save_path", type=str, default="save")
    return parser.parse_args()

params = get_params()

os.chdir(f"git_datasets/{params.project}")
with open(f"{params.project}.txt", "r") as f:
    clone_cmds = [cmd.strip("\n") for cmd in f.readlines()]
for cmd in clone_cmds:
    try:
        os.system(cmd)
    except:
        IOError(f'Git Clone Error {cmd}')
os.chdir("../../")

repos = [r for r in os.listdir(f"git_datasets/{params.project}") if os.path.isdir(os.path.join("git_datasets", params.project, r))]
assert len(repos) > 0, "No repos found"
extractor = RepositoryExtractor()

for repo in repos:
    params.prj = repo
    params.local_repo_path = f"git_datasets/{params.project}/{params.prj}"
    params.ids_path = f"git_datasets/{params.project}/{params.prj}.pkl"
    params.save_path = f"save/{params.project}"
    extractor.config_repo(params)