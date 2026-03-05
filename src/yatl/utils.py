import os


def search_files(current_path, item: str, files: list):
    full_path = os.path.join(current_path, item)
    if os.path.isfile(full_path) and (
        item.endswith(".test.yaml") or item.endswith(".test.yml")
    ):
        files.append(full_path)
        return
    elif os.path.isdir(full_path):
        for i in os.listdir(full_path):
            search_files(full_path, i, files)
    return files
