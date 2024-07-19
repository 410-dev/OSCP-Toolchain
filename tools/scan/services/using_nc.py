import lib.host as Host


def parameters() -> dict:
    return {
        "port": {
            "type": str,
            "description": "The port to connect to.",
            "required": True
        },
        "param": {
            "type": str,
            "description": "The parameters to execute.",
            "required": True,
            "default": "-z -v -w $$config:DefaultConnections.targetMachine <PORT>"
        }
    }


def init() -> tuple:
    return Host.isRunningLinuxSuperuser(), "This tool requires superuser privileges." if not Host.isRunningLinuxSuperuser() else ""


def kali(port: str, param: str) -> str:
    param = param.replace("<PORT>", port)
    commandStruct = param.split(" ")
    command = ["sudo", "nc"]
    command.extend(commandStruct)
    returned = Host.executeShellScript(command)
    if returned[0] == 0:
        result = returned[1]
    else:
        result = "STDOUT: " + returned[1] + "\n\n\nSTDERR: " + returned[2]

    return result
