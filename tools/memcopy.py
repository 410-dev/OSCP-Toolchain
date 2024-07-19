from lib.memory import Memory


def parameters() -> dict:
    return {
        "source": {
            "type": str,
            "description": "The source memory key. For empty data, type \"null\"",
            "required": True
        },
        "destination": {
            "type": str,
            "description": "The destination memory key.",
            "required": True
        }
    }


def linux(source: str, destination: str) -> str:
    if source == "null":
        Memory.data[destination] = None
    else:
        Memory.data[destination] = Memory.data[source]
    return f"MEMCOPY {source} >>> {destination}"


def windows(source: str, destination: str) -> str:
    return linux(source, destination)
