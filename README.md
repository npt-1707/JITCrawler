# JIT-DP Data Crawling Tool

Tool crawls 14 features data for JIT-DP problem with traditional machine learning approaches.

## Requirements:

Check for module in `requirements.txt`

## Run steps

-   Change github access token: Create your own access token and paste it into `github_access_token.txt`
-   Run `main.py' file to clone all repos and extract features:

```
...
for line in lines:
    ...
```

or for some repos:

```
...
for line in lines[start_repo_index:end_repo_index]:
    ...
```
