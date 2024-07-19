import lib.host as Host


def parameters() -> dict:
    return {
        "param": {
            "type": str,
            "description": "The parameters to execute.",
            "required": True,
            "default": "-sC -sV $$config:DefaultConnections.targetMachine"
        }
    }


def kali(param: str) -> str:
    commandStruct = param.split(" ")
    command = ["nmap"]
    command.extend(commandStruct)
    returned = Host.executeShellScriptWithRealtimeOutput(command)
    if returned[0] == 0:
        result = returned[1]
    else:
        result = "TERMINAL OUT: " + returned[1]

    return result
