from src import Repository, Extractor, Processor, PySZZ, Splitter
from utils import clone_repo


class BasicPipeline:
    def __init__(self, cfg):
        # init extractor
        self.extractor = Extractor(
            start=cfg.extractor_start,
            end=cfg.extractor_end,
            num_commits_per_file=cfg.extractor_num_commits_per_file,
            language=cfg.repo_language,
            save=cfg.extractor_save,
            force_reextract=cfg.extractor_force_reextract,
        )

        # init pyszz
        self.pyszz = PySZZ(pyszz_path=cfg.pyszz_path, keep_output=cfg.pyszz_keep_output)

        # init processor
        self.processor = Processor(save_path=cfg.dataset_save_path, save=cfg.processor_save)
        
        # init splitter
        self.splitter = Splitter(save_path=cfg.dataset_save_path)

    def set_repo(self, cfg):
        assert cfg.mode in ["local", "remote"], "Invalid mode: {}".format(cfg.mode)
        if cfg.mode == "local":
            self.repo = self.local_repo(cfg)
        else:
            self.repo = self.remote_repo(cfg)

    def local_repo(self, cfg):
        repo = Repository(
            cfg.repo_owner,
            cfg.repo_name,
            cfg.repo_save_path,
            cfg.repo_path,
            cfg.repo_language,
        )
        return repo

    def remote_repo(self, cfg):
        clone_repo(cfg.repo_clone_path, cfg.repo_owner, cfg.repo_name, cfg.repo_clone_url)
        repo = Repository(
            cfg.repo_owner,
            cfg.repo_name,
            cfg.repo_save_path,
            cfg.repo_clone_path,
            cfg.repo_language,
        )
        return repo

    def run(self):
        print("Running repository: {}/{}".format(self.repo.owner, self.repo.name))
        # extract repo
        # print("Extracting repository...")
        self.extractor.set_repo(self.repo)
        self.extractor.run()

        # run pyszz
        print("Running PySZZ...")
        self.pyszz.run(
            self.repo.get_bug_fix_path(),
            self.repo.get_repo_path(),
            self.repo.get_language()
        )
        szz_output = self.pyszz.get_lastest_output()
        print("PySZZ output: {}".format(len(szz_output)))

        # process data
        print("Processing information...")
        self.processor.set_repo(self.repo)
        self.processor.run(szz_output, self.extractor.end)
        
        # split data
        print("Splitting data...")
        self.splitter.set_processor(self.processor)
        self.splitter.run()
        
        print("Done")
