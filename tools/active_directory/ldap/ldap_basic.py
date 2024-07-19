import lib.host as Host


def parameters() -> dict:
    return {
        "distinguish_name": {
            "type": str,
            "description": "The domain controller to query. Example: dc=htb,dc=local",
            "required": True
        },
        "param": {
            "type": str,
            "description": "The parameters to execute.",
            "required": True,
            "default": "ldapsearch -x -b DISTINGUISH_NAME * -H ldap://$$config:DefaultConnections.targetMachine"
        },
        "return": {
            "type": str,
            "description": "Returns the result of ldap search."
        }
    }


def resultAnalysis(result: tuple) -> str:
    if result[0] == 0:
        from lib.memory import Memory
        Memory.set("ldap_search_text", result[1])
        return result[1]
    else:
        return "STDOUT: " + result[1] + "\n\n\nSTDERR: " + result[2]


def kali(distinguish_name: str, param: str) -> tuple:
    commandStruct = param.split(" ")
    for index, value in enumerate(commandStruct):
        if value == "DISTINGUISH_NAME":
            commandStruct[index] = distinguish_name
    return Host.executeShellScript(commandStruct)
