from utils import *


def process_content(content, surrounding_lines=3):
    length = len(content)
    i = 0
    hunks = []
    cur_hunk = []
    pred = {}
    cur = []
    while i < length:
        if "ab" in content[i]:
            if len(cur) > 0:
                if len(content[i]["ab"]) <= surrounding_lines:
                    cur.append(content[i])
                else:
                    cur_hunk.append(pred)
                    pred = content[i]
                    for d in cur:
                        cur_hunk.append(d)
                    cur = []
                    next = content[i]
                    next["ab"] = next["ab"][:surrounding_lines]
                    cur_hunk.append(content[i])
                    hunks.append(cur_hunk)
                    cur_hunk = []
            else:
                pred = content[i]
                pred["ab"] = pred["ab"][-surrounding_lines:]
        if "a" in content[i] or "b" in content[i]:
            cur.append(content[i])
        i += 1
    if len(cur) > 0:
        cur_hunk.append(pred)
        for d in cur:
            cur_hunk.append(d)
        hunks.append(cur_hunk)
    del pred, cur, cur_hunk
    return hunks


def process_diff_log(diff_log):
    commit_diff = {}
    diff_log = split_diff_log(diff_log)
    for log in diff_log:
        files_diff = aggregator(parse_lines(log))
        for file_diff in files_diff:
            file_name_a = (file_diff["from"]["file"] if file_diff["rename"]
                           or file_diff["from"]["mode"] != "0000000" else
                           file_diff["to"]["file"])
            file_name_b = (file_diff["to"]["file"] if file_diff["rename"]
                           or file_diff["to"]["mode"] != "0000000" else
                           file_diff["from"]["file"])
            if file_diff["is_binary"] or len(file_diff["content"]) == 0:
                continue

            if file_diff["from"]["mode"] == "0000000":
                continue
            commit_diff[file_name_b] = file_diff
    return commit_diff