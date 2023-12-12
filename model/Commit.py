class Commit(dict):
    """
    Structure of a commit:
    {
        "commit_id": str,
        "parent_id": str,
        "author": str,
        "date": str,
        "message": str,
        "subject": str,
        "files": list,
        "diff": dict,
        "blame": dict,
        "features": dict,
        "label": int
    }
    """
    def __init__(self, args):
        for key, val in args.items():
            self[key] = val