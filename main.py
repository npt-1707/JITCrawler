import argparse
from RepositoryExtractor import RepositoryExtractor

def get_params():
    parser = argparse.ArgumentParser()
    parser.add_argument("--save_path", type=str, default=".", required=True)
    parser.add_argument("--mode", type=str, required=True, default="local")
    parser.add_argument("--start", type=str, default=None)
    parser.add_argument("--end", type=str, default=None)
    parser.add_argument("--to_csv", type=bool, default=False)
    parser.add_argument("--local_repo_path", type=str, default="")
    parser.add_argument("--main_language", type=str)
    parser.add_argument("--github_repo", type=str)
    parser.add_argument("--github_owner", type=str)
    parser.add_argument("--github_token_path", type=str)
    parser.add_argument("--extract_features", type=bool, default=False)
    parser.add_argument("--rand_num", type=int, default=None)
    parser.add_argument("--excepted_ids_path", type=str, default=None)
    
    return parser.parse_args()

config = get_params()
extractor = RepositoryExtractor()
extractor.config_repo(config)
extractor.run()