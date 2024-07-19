
from lib import listModules
from lib.lks410sdm import Data as LKSDM
from lib.memory import Memory

import tools.connections.ping as Ping
import lib.host as Host

import importlib
import sys
import re
import os

data = LKSDM()

if not os.path.isdir("cache"):
    os.makedirs("cache", exist_ok=True)

if os.path.isfile("configs/main.json"):
    with open("configs/main.json", "r") as file:
        data = LKSDM(parseString=file.read())
        print("configs/main.json loaded")

else:
    data.set("kaliDetectionPath", "/etc/kali-menu,/etc/kali_menu,/tmp/kali_emulate")
    data.set("MemoryPersistence", {
        "enabled": False,
        "loadOnStart": True
    })
    data.set("DefaultConnections", {
        "enabled": False,
        "targetMachine": "",
        "pingOnStartup": True
    })
    data.set("VPNConnection", {
        "filePath": "",
    })
    data.sortKeysByName()
    data.typeCheck(writeTypeData=True)

    os.makedirs("configs", exist_ok=True)

    with open("configs/main.json", "w") as file:
        file.write(data.compileString())
        print("configs/main.json saved")


if data.typeCheck(strictTypeChecks=True):
    print("Config type checks passed")
else:
    print("Error: Config checks failed")
    sys.exit(1)

Memory.set("config", data)

#### INTERFACE

if data.get("DefaultConnections.enabled"):
    print("Default connections enabled.")
    targetIP = data.get("DefaultConnections.targetMachine")
    print(f"Target IP: {targetIP}")
    if data.get("DefaultConnections.pingOnStartup"):
        print("Pinging target machine...")
        if Host.isRunningWindows():
            success = Ping.windows(targetIP, 3, 1)
        else:
            success = Ping.linux(targetIP, 3, 1)


else:
    print("Default connections disabled.")
    targetIP = input("Enter target IP: ")
    Memory.get("config").set("DefaultConnections.targetMachine", targetIP)

print(f"Current machine is {Host.closestDistribution()}")


def mapFromMemory(string):
    result = string
    try:
        if not isinstance(string, str) or "$$" not in string:
            return string

        if ":" in string:
            # Regex to match the pattern $$<memoryId>:<key>
            pattern = re.compile(r'\$\$([^\s:]+):([^\s]+)')

            def replace_token(match):
                memoryId = match.group(1)
                key = match.group(2)
                # Assuming Memory.get(memoryId).get(key) retrieves the desired value
                if len(key) == 0:
                    value = str(Memory.get(memoryId))
                else:
                    value = str(Memory.get(memoryId).get(key))
                return value

            # Substitute all matches in the string using the replace_token function
            result = pattern.sub(replace_token, string)

        else:
            # Regex to match the pattern $$<memoryId>
            pattern = re.compile(r'\$\$([^\s]+)')

            def replace_token(match):
                memoryId = match.group(1)
                # Assuming Memory.get(memoryId) retrieves the desired value
                value = str(Memory.get(memoryId))
                return value

            # Substitute all matches in the string using the replace_token function
            result = pattern.sub(replace_token, string)

    except Exception as e:
        return result

    if "$$" in result:
        return mapFromMemory(result)
    return result


def get_user_input(param_name, param_info):
    while True:
        defaultAllowed = False
        if 'default' in param_info:
            defaultAllowed = True

        defaultStr = mapFromMemory(param_info['default'] if defaultAllowed else "")

        user_input = input(f"Enter {param_name} ({f"Default: '{defaultStr}'" if defaultAllowed else ''}{', ' if defaultAllowed and param_info['required'] else ''}{'Required' if param_info['required'] else ''}): ")
        if user_input == "exit":
            return "_______EXIT________"
        if user_input == "?" or user_input == "help":
            print(f"Enter {param_name} ({param_info['description']}): ", end="")
            print(f"Default: {defaultStr}")
            continue
        if not user_input and defaultAllowed:
            if not isinstance(param_info['default'], str) or "$$" in param_info['default']:
                return param_info['type'](defaultStr)
            return param_info['default']
        if not user_input and not defaultAllowed:
            if param_info['required']:
                print(f"{param_name} is required.")
                continue
            else:
                return None
        try:
            if "$$" in user_input:
                return param_info['type'](mapFromMemory(user_input))
            return param_info['type'](user_input)
        except ValueError:
            print(f"Invalid input. Please enter a {param_info['type'].__name__}.")


def run_module(module_name):
    try:
        autoParams: list = []
        if " " in module_name:
            module_name, autoParamsStr = module_name.split(" ", 1)
            autoParams = autoParamsStr.split(" ")
        if not module_name.startswith("tools."):
            module_name = f"tools.{module_name}"
        module = importlib.import_module(module_name)
        importlib.reload(module)
        current_os = Host.closestDistribution()
        if not Host.isCurrentSystemSupportingModule(module):
            print(f"This module is not supported on {current_os}.")
            return

        if 'init' in dir(module):
            initResult: tuple = module.init()
            if not initResult[0]:
                print(f"Module '{module_name}' could not be initialized: {initResult[1]}")
                return

        params = module.parameters()
        args = {}
        for param_name, param_info in params.items():
            if param_name != "return":
                if len(autoParams) > 0:
                    args[param_name] = param_info['type'](autoParams.pop(0).replace("__", " "))
                else:
                    args[param_name] = get_user_input(param_name, param_info)
                    if args[param_name] == "_______EXIT________":
                        return

        if Host.isRunningKaliLinux():
            if 'kali' in dir(module):
                current_os = "kali"
            elif 'linux' in dir(module):
                current_os = "linux"

        func = getattr(module, current_os)
        result = func(**args)
        print("=======RESULT=======")
        if 'return' in params or 'resultAnalysis' in dir(module):
            print(module.resultAnalysis(result))
        else:
            print(result)

        Memory.set("LastRun-Module", module_name)
        Memory.set("LastRun-Args", args)
        Memory.set("LastRun-Result", result)

    except ImportError:
        print(f"Module launch '{module_name}' not found.")
    except AttributeError:
        print(f"Module '{module_name}' is not properly structured.")
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        print(f"An error occurred while running the module: {str(e)}")


def main():
    off = False

    # Load memory if persistency is enabled
    if Memory.get("config").get("MemoryPersistence.loadOnStart"):
        Memory.load()

    modules = listModules.run()
    while not off:
        if not os.path.isdir("cache"):
            os.makedirs("cache", exist_ok=True)
        print("")
        print("=========== Main Menu ===========")
        if not Host.isRunningPrivileged():
            print("WARNING: Toolchain is NOT in superuser.")
            print("WARNING: This program recommends using superuser privileges.")
            print("================================")
        print("1. List installed modules")
        print("2. Exit")
        print("")
        print("Module name >>> ", end="")
        option = input()

        if option == "1":
            modules = listModules.run()
        elif option == "2":
            off = True
        else:
            if option.startswith("$$"):
                print(mapFromMemory(option))
            else:
                try:
                    if int(option) in modules:
                        print(f"Running module: {modules[int(option)]}")
                        option = modules[int(option)]
                        run_module(option)
                    else:
                        print("Invalid module number.")
                except ValueError:
                    run_module(option)


main()
