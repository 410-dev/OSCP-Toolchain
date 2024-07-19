import lib.host as Host
import os


def parameters() -> dict:
    return {
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
        Memory.set("passwdcrackresult", result[1])
        return result[1]
    else:
        return "STDOUT: " + result[1] + "\n\n\nSTDERR: " + result[2]


def kali(pwCrackCmd: str) -> tuple:
    print("Cracking passwords...")
    commandStruct = pwCrackCmd.split(" ")
    crackResult = Host.executeShellScript(commandStruct)
    if crackResult[0] != 0:
        print("Password cracking failed.")
        print("STDOUT: ", crackResult[1])
        print("STDERR: ", crackResult[2])
        return crackResult

    print("User enumeration and password cracking successful.")
    commandStruct = ["john", "--show", "cache/pwcrack_result.txt"]
    crackResult = Host.executeShellScript(commandStruct)
    if crackResult[0] != 0:
        print("Password show failed.")
        print("STDOUT: ", crackResult[1])
        print("STDERR: ", crackResult[2])

    return crackResult
