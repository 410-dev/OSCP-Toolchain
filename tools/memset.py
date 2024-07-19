from lib.memory import Memory


def parameters() -> dict:
    return {
        "key": {
            "type": str,
            "description": "Key to set.",
            "required": True
        },
        "value": {
            "type": str,
            "description": "Value to set.",
            "required": True
        }
    }


def linux(key: str, value: str) -> str:
    if value == "null":
        Memory.data[key] = None
    else:
        Memory.data[key] = value
    return f"MEMSET '{value}' >>> {key}"


def windows(key: str, value: str) -> str:
    return linux(key, value)

