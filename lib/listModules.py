import os
import importlib
import lib.host as Host


def fullPathBuild(path: str) -> list:
    fileList = []
    fullList = os.listdir(path)
    for file in fullList:
        if os.path.isdir(f"{path}/{file}"):
            fileList += fullPathBuild(f"{path}/{file}")
        else:
            if file.endswith(".py") and not file.startswith("__"):
                fileList.append(f"{path}/{file}")

    return fileList


def run() -> dict:
    print("\nList of modules:")

    fullPaths = fullPathBuild("tools")
    # sort the list
    fullPaths = sorted(fullPaths)
    index = 3
    maps = {}
    for path in fullPaths:
        path = path.replace("/", ".").replace(".py", "").replace(os.path.sep, "").replace("tools.", "")
        module = importlib.import_module(f"tools.{path}")
        importlib.reload(module)
        if not Host.isCurrentSystemSupportingModule(module):
            print(f"{index}: [Unsupported] {path}")
        else:
            print(f"{index}: [ Supported ] {path}")

        maps[index] = path
        index += 1

    return maps
