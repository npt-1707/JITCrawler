import os
from github import Github
from RepositoryExtractor import RepositoryExtractor

ORG_DIR = os.getcwd()

with open("repos.txt", "r") as f:
    lines = f.read().split("\n")

with open("github_access_token.txt") as f:
    github_access_token = f.read()

g = Github(github_access_token)

if not os.path.exists("repo"):
    os.mkdir("repo")

end = "2023-05-01"
for line in lines:
    print(line)
    owner, name = line.split("/")
    extractor = RepositoryExtractor(g, owner, name, ORG_DIR, end)
    extractor.get_repo_commits_info(main_language_only=True)
    extractor.extrac_repo_k_features()
    extractor.to_csv()
    os.chdir(ORG_DIR)
