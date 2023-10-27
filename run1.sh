python3 main.py \
    --save_path $1\
    --mode online\
    --start "2013-10-24"\
    --end "2022-11-20"\
    --github_token_path $2\
    --github_owner torvalds\
    --github_repo linux\
    --ids_path $3\
    --num_commits_per_file 5000\