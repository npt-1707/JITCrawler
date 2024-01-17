import os
import yaml
from utils import exec_cmd, load_json


class PySZZ:
    def __init__(
        self, pyszz_path: str, pyszz_conf: str = "bszz", keep_output: int = 10
    ):
        """
        Wrapper for PySZZ from https://github.com/grosa1/pyszz_v2
        """
        assert os.path.exists(pyszz_path), "PySZZ: Path not found: {}".format(
            pyszz_path
        )
        self.path = os.path.abspath(pyszz_path)
        self.conf = pyszz_conf
        self.base_bzz_conf = """
            szz_name: b
            issue_date_filter: false
        """
        self.keep_output = keep_output

    def set_conf(self, conf="bszz"):
        valid_conf = ["bszz", "pdszz"]
        assert conf in ["bszz", "pdszz"], "PySZZ: Invalid type: {}".format(conf)
        self.conf = conf

    def get_conf(self):
        return f"conf/{self.conf}.yml"

    def run(self, bug_fix_path, conf, repo_path, repo_language):
        cur_dir = os.getcwd()
        os.chdir(self.path)

        # modify config file
        base_conf = yaml.load(self.base_bzz_conf, Loader=yaml.FullLoader)
        if repo_language:
            base_conf["file_ext_to_parse"] = repo_language
        with open(self.get_conf(), "w") as f:
            yaml.dump(base_conf, f)

        # remove historical output
        self.remove_historical_output()

        # run pyszz
        cmd = "python3 main.py {} {} {}".format(bug_fix_path, conf, repo_path)
        exec_cmd(cmd)
        os.chdir(cur_dir)

    def get_lastest_output(self):
        output_files = os.listdir(os.path.join(self.path, "out"))
        lastest_file = max(
            output_files,
            key=lambda x: os.path.getmtime(os.path.join(self.path, "out", x)),
        )
        data = load_json(os.path.join(self.path, "out", lastest_file))
        return data

    def remove_historical_output(self):
        output_files = os.listdir(os.path.join(self.path, "out"))
        sorted_output_files = sorted(
            output_files,
            key=lambda x: os.path.getmtime(os.path.join(self.path, "out", x)),
        )
        if len(sorted_output_files) > self.keep_output:
            for file in sorted_output_files[: -self.keep_output]:
                os.remove(os.path.join(self.path, "out", file))
