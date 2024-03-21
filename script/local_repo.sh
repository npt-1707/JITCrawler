cd ..
git clone https://github.com/manhlamabc123/DefectGuard-the-Package.git
cd JITCrawler

python3 main.py \
    --mode local \
    --repo_owner "" \
    --repo_name DefectGuard-the-Package \
    --repo_path .. \
    --repo_language Python \
    --extractor_save \
    --extractor_check_uncommit \
    --extractor_start 2010-01-01 --extractor_end 2023-12-25 \
    --pyszz_path ../pyszz_v2 \
    --processor_save \

