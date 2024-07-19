from lib.memory import Memory

import lib.host as Host


def parameters() -> dict:
    return {}


def init() -> tuple:
    if not Host.isRunningLinuxSuperuser():
        return False, "This module requires superuser privileges"
    return True, ""


def linux():
    paths: list = Memory.get("config").get("kaliDetectionPath").split(",")
    with open(paths[-1], "w") as f:
        try:
            f.write("Kali Linux")
            return "Emulation flag wrote at " + paths[-1]
        except Exception as e:
            print("Error writing to file")
            return str(e)
