import os
import subprocess

from lib.memory import Memory


def executeShellScript(script: list) -> tuple: # Returns  (return code, stdout, stderr)
    print("Executing shell command:", script)
    process = subprocess.Popen(script, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return process.returncode, stdout.decode(), stderr.decode()


def executeShellScriptAsyncBackground(script: list) -> int:
    print("Executing shell command:", script)
    process = subprocess.Popen(script, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process.pid


def executeShellScriptWithRealtimeOutput(script: list) -> tuple:
    print("Executing shell command:", script)
    process = subprocess.Popen(script, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = ""
    for line in iter(process.stdout.readline, b''):
        print(line.decode(), end='')
        output += line.decode()
    process.stdout.close()
    process.wait()
    return process.returncode, output


def executePowerShellScript(script: str) -> tuple: # Returns  (return code, stdout, stderr)
    print("Executing PowerShell command:", script)
    return executeShellScript(["powershell", "-Command", script])


def executePowerShellScriptWithRealtimeOutput(script: str) -> tuple:
    print("Executing PowerShell command:", script)
    return executeShellScriptWithRealtimeOutput(["powershell", "-Command", script])


def isRunningKaliLinux() -> bool:
    paths: list = Memory.get("config").get("kaliDetectionPath").split(",")
    for path in paths:
        if os.path.isfile(path):
            return True
    return False


def isRunningWindows() -> bool:
    return os.name == 'nt'


def isRunningLinux() -> bool:
    return os.name == 'posix'


def isRunningLinuxSuperuser() -> bool:
    return os.geteuid() == 0


def isRunningWindowsAdministrator() -> bool:
    return os.system("NET SESSION >nul 2>&1") == 0


def isRunningPrivileged() -> bool:
    if isRunningWindows():
        return isRunningWindowsAdministrator()
    if isRunningLinux():
        return isRunningLinuxSuperuser()
    return False

def isCurrentSystemSupportingModule(module) -> bool:
    supportList = []
    for function in dir(module):
        if function in ["windows", "linux", "kali"]:
            supportList.append(function)

    if isRunningWindows() and "windows" in supportList:
        return True
    if isRunningLinux() and "linux" in supportList:
        return True
    if isRunningKaliLinux() and "kali" in supportList:
        return True
    return False


def closestDistribution() -> str:
    if isRunningKaliLinux():
        return "kali"
    if isRunningLinux():
        return "linux"
    if isRunningWindows():
        return "windows"
    return "unknown"
