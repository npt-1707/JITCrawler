from argparse import ArgumentParser
from Pipeline import BasicPipeline
from utils import is_supported_language
import os


def get_params():
    parser = ArgumentParser()
    valid_modes = ["local", "remote"]
    parser.add_argument("--mode", type=str, default="local", choices=valid_modes)
    parser.add_argument("--repo_path", type=str, default="repo")
    parser.add_argument("--repo_name", type=str, required=True)
    parser.add_argument("--repo_owner", type=str, required=True)
    parser.add_argument(
        "--repo_language",
        type=lambda x: (
            [i for i in x.split(" ") if is_supported_language(i)] if x else []
        ),
        default="",
    )
    parser.add_argument("--repo_save_path", type=str, default="save")
    parser.add_argument("--repo_clone_path", type=str, default="repo")
    parser.add_argument("--repo_clone_url", type=str)
    parser.add_argument("--extractor_start", type=str, default=None)
    parser.add_argument("--extractor_end", type=str, default=None)
    parser.add_argument("--extractor_num_commits_per_file", type=int, default=5000)
    parser.add_argument("--extractor_save", action="store_true")
    parser.add_argument("--extractor_force_reextract", action="store_true")
    parser.add_argument("--extractor_check_uncommit", action="store_true")
    parser.add_argument("--pyszz_path", type=str, default="pyszz_v2")
    parser.add_argument("--pyszz_keep_output", type=int, default=50)
    parser.add_argument("--pyszz_conf", type=str, default="bszz")
    parser.add_argument("--pyszz_log_path", type=str, default="log")
    parser.add_argument("--processor_save", action="store_true")
    parser.add_argument("--dataset_save_path", type=str, default="dataset")

    return parser.parse_args()


def create_default_save_folders():
    folders = ["repo", "save", "dataset", "log"]
    for folder in folders:
        if not os.path.exists(folder):
            os.mkdir(folder)


if __name__ == "__main__":
    config = get_params()
    create_default_save_folders()
    crawler = BasicPipeline(config)
    crawler.set_repo(config)
    crawler.run()
