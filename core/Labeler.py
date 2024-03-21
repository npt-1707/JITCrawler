import logging
import os
import yaml
from utils import exec_cmd, load_json, LANG2EXT


class PySZZ:
    def __init__(
        self,
        pyszz_path: str,
        log_path: str = "log",
        pyszz_conf: str = "bszz",
        keep_output: int = 50,
    ):
        """
        Wrapper for PySZZ from https://github.com/grosa1/pyszz_v2
        """
        assert os.path.exists(pyszz_path), "PySZZ: Path not found: {}".format(
            pyszz_path
        )
        self.path = os.path.abspath(pyszz_path)
        self.log_path = os.path.abspath(log_path)
        self.set_conf(pyszz_conf)
        self.keep_output = keep_output

    def set_conf(self, conf="bszz"):
        valid_conf = list(
            map(lambda x: x[:-4], os.listdir(os.path.join(self.path, "conf")))
        )
        assert conf in valid_conf, "PySZZ: Invalid type: {}".format(valid_conf)
        self.conf = conf
        with open(os.path.join(self.path, "conf", conf + ".yml"), "r") as f:
            self.base_conf = yaml.load(f, Loader=yaml.FullLoader)

    def run(self, bug_fix_path, szz_conf_path, repo_path, repo_language):
        logging.basicConfig(
            filename=os.path.join(self.log_path, "pyszz_log.log"),
            level=logging.DEBUG,
            format="%(asctime)s %(message)s",
            filemode="w",
        )
        cur_dir = os.getcwd()
        os.chdir(self.path)

        # modify config file
        conf = self.base_conf
        if repo_language:
            conf["file_ext_to_parse"] = list(
                map(lambda x: LANG2EXT[x][1:], repo_language)
            )

        with open(szz_conf_path, "w") as f:
            yaml.dump(conf, f)

        # remove historical output
        self.remove_historical_output()

        # run pyszz
        cmd = "python3 main.py {} {} {}".format(bug_fix_path, szz_conf_path, repo_path)
        logging.debug(cmd)
        out = exec_cmd(cmd)
        logging.debug(out)
        os.chdir(cur_dir)

    def get_outputs(self):
        assert "out" in os.listdir(self.path), "PySZZ: No output folder"
        output_files = [
            file
            for file in os.listdir(os.path.join(self.path, "out"))
            if self.conf in file
        ]

        sorted_output_files = sorted(
            output_files,
            key=lambda x: os.path.getmtime(os.path.join(self.path, "out", x)),
            reverse=True,
        )
        return sorted_output_files

    def get_lastest_output(self, repo_owner, repo_name):
        output_files = self.get_outputs()
        for file in output_files:
            data = load_json(os.path.join(self.path, "out", file))
            if data[0]["repo_name"] == os.path.join(repo_owner, repo_name):    
                return data
        raise FileNotFoundError("PySZZ: No output found for {}/{}".format(repo_owner, repo_name))
    
    def remove_historical_output(self):
        output_files = self.get_outputs()
        if len(output_files) > self.keep_output:
            print("Removing historical output")
            for file in output_files[self.keep_output:]:
                os.remove(os.path.join(self.path, "out", file))
