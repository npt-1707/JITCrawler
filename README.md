# JITCrawler

A JIT-DP data crawling tool that collects codes and features data for JIT-DP problem for different approaches.

## Requirements

This tool utilize the code of [PySZZ](https://github.com/grosa1/pyszz_v2/). Please install PySZZ and pass its path as a parameter when the code in [Run](#run).

**Notice**: to run PySZZ:
- Python 3.9
- [srcML](https://www.srcml.org/) (i.e., the srcml command should be in the system path)

## Setup:

Run follwing command:
```
    pip3 install -r requirements.txt
```

Also notice to check for requirement of PySZZ.

## Structure:

### Folder's structure
```bash
.
├── model // main classes for collecting and processing data
│   ├── Dict.py
│   ├── Extractor.py // A tool for extracting information from git repository
│   ├── Labeler.py // A PySZZ wrapper for labeling extracted data
│   ├── Processor.py // A tool for processing extracted data t and formating to JITDP models input format
│   ├── Repository.py // A repository wrapper
│   ├── Splitter.py // A tool for splitting processed data
├── utils
├── data // default folder for saving dataset
├── save // default folder for saving extracted data
├── repo // default folder for cloning github repository
├── .gitignore
├── Pipeline.py // A complete pipeline for creating a JITDP dataset
├── main.py
├── README.md
```

### Extracted Data's folder structure

A sample structure of extracted data:
```bash
.
├── save
|   ├── repo_name
|   |   ├── commit_ids.pkl
|   |   ├── etracted_info.json // the config for Extractor
|   |   ├── repo_bug_fix.json // the bug_fix file for running PySZZ
|   |   ├── repo_commits_{num}.pkl // files storing commits information
|   |   ├── repo_features.pkl // files storing commits features
```

### Processed Data's folder structure

A sample structure of processed data:
```bash
.
├── dataset
|   ├── repo_name
|   |   ├── commits
|   |   |   ├── cc2vec.pkl
|   |   |   ├── deepjit.pkl
|   |   |   ├── simcom.pkl
|   |   |   ├── dict.pkl
|   |   ├── features
|   |   |   ├── feature.csv
```

### Repository's structure

In case this tool is run on `mode="local"`, please follow this repository's structure paths:
```bash
.
├── repo_path
|   ├── repo_owner
|   |   ├── repo_name
|   |   |   ├── .git
|   |   |   ├── other repo content
```

## Run:

Execute the following command:
```
python3 main.py --mode mode \
    --repo_owner owner --repo_name name \
    --extractor_save --extractor_start start_date --extractor_end end_date \
    --pyszz_path path/to/cloned/pyssz \
    --processor_save \
    --dataset_save_path path/to/dataset \ 
```

For more options of running `main.py`:
- `--mode`: "local" or "remote". Default: `"local"`
    - local: for a local repository
    - remote: for a remote repository, it will be cloned into `repo` folder
- `--repo_path`: the path following [structure](#repositorys-structure)
- `--repo_owner`: the repository's owner.
- `--repo_name`: the repository's name.
- `--repo_language`: a string of repository's languages splitted by spaces, the empty string means all languages. Default: "".
- `--repo_save_path`: the path for saving extracted data. Default: "save".
- `--repo_clone_path`: the path for saving cloned repository in case `mode="remote"`. Default: "repo".
- `--repo_clone_url`: the url for clonning repository in case `mode="remote"`.
- `--extractor_start`: the date starting to extract data, if None, data is extracted from the beginning. Format: "yyyy-mm-dd". Default: None.
- `--extractor_end`: the date ending to extract data, if None, data is extracted to the lastest commit. Format: "yyyy-mm-dd". Default: None.
- `--extractor_num_commits_per_file`: the number of extracted commits to save in a file. Default: 5000.
- `--extractor_save`: whether or not save the extracted data.
- `--extractor_force_reextract`:  whether or not reextract data. Notice once this tag is given, all saved repository's extracted files in `save_path` are deleted.
- `pyszz_path`: the path to pyssz's folder.
- `pyszz_keep_output`: number of pyszz's output files kept after running code. Default: 10.
- `pyszz_conf`: the configuration for running pyszz. Default: "bszz".
- `processor_save`: whether or not save processed data.
- `dataset_save_path`: the path to the dataset.
