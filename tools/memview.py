from lib.memory import Memory


def parameters() -> dict:
    return {
        "simplifyExtent": {
            "type": int,
            "description": "If True, the full view of the memory will be displayed. Otherwise, a simplified view will be displayed.",
            "required": False,
            "default": 50
        }
    }


def linux(simplifyExtent: int) -> str:
    keys = Memory.data.keys()
    pairStr = ""
    import time
    import hashlib
    timeOfExecution = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    timeOfExecution = hashlib.md5(timeOfExecution.encode()).hexdigest()[0:4]

    longestKey = 0
    for key in keys:
        memType = str(type(Memory.data[key])).replace('<class \'', '').replace('\'>', '')
        fullKeypath = f"[{timeOfExecution}]: {key}({memType})"
        if len(fullKeypath) > longestKey:
            longestKey = len(fullKeypath)

    for key in keys:
        memType = str(type(Memory.data[key])).replace('<class \'', '').replace('\'>', '')
        dataSimplified = str(Memory.data[key])

        if len(dataSimplified) > simplifyExtent:
            dataSimplified = dataSimplified[:simplifyExtent] + "..."

        fullKeypath = f"[{timeOfExecution}]: {key}({memType})"

        if "\n" in dataSimplified:
            dataSimplified = dataSimplified.replace("\n", "\n" + " " * (longestKey + 3))

        pairStr += f"[{timeOfExecution}]: {key}({memType}) {' ' * (longestKey - len(fullKeypath))}: {dataSimplified}\n"

    return pairStr


def windows(simplifyExtent: int) -> str:
    return linux(simplifyExtent)

