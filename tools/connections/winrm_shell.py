import winrm
import subprocess
import sys
import os


def parameters() -> dict:
    return {
        "host": {
            "type": str,
            "description": "The target host to connect to.",
            "required": True,
            "default": "$$config:DefaultConnections.targetMachine"
        },
        "port": {
            "type": int,
            "description": "The port to connect to (default is 5985 for HTTP, 5986 for HTTPS).",
            "required": False,
            "default": "$$port"
        },
        "username": {
            "type": str,
            "description": "Username for WinRM authentication.",
            "required": True,
            "default": "$$username"
        },
        "password": {
            "type": str,
            "description": "Password for WinRM authentication.",
            "required": True,
            "default": "$$password"
        },
        "use_ssl": {
            "type": bool,
            "description": "Use SSL/HTTPS for the connection.",
            "required": False,
            "default": False
        }
    }


def init() -> tuple:
    if sys.platform.startswith('linux'):
        try:
            import winrm
            return True, ""
        except ImportError:
            return False, "pywinrm library is not installed. Please install it using: pip install pywinrm"
    elif sys.platform.startswith('win'):
        # Check if winrs command is available
        try:
            subprocess.run(["winrs", "/?"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True, ""
        except subprocess.CalledProcessError:
            return False, "winrs command is not available on this Windows system."
    else:
        return False, "Unsupported operating system."


def linux(host: str, port: int, username: str, password: str, use_ssl: bool) -> tuple:
    protocol = "https" if use_ssl else "http"
    session = winrm.Session(f"{protocol}://{host}:{port}/wsman", auth=(username, password))

    print("Testing connection...")

    try:
        result = session.run_cmd("ipconfig", ["/all"])
        print(result.std_out.decode('utf-8'))
        print("Test success.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return -1, f"Connection failed: {str(e)}"

    print(f"Connected to {host}. Type 'exit' to close the session.")

    lastExitCode = 0
    while True:
        try:
            command = input(f"({lastExitCode}) WinRM> ")
            if command.lower() == 'exit':
                break
            result = session.run_cmd(command)
            print(result.std_out.decode('utf-8'))
            if result.std_err:
                print("Error:", result.std_err.decode('utf-8'))
        except Exception as e:
            print("Error:", str(e))
            inp = input("Do you want to try again? (y/n): ")
            if inp.lower() != 'y':
                break

    return 0, "Session closed successfully"


def windows(host: str, port: int, username: str, password: str, use_ssl: bool) -> tuple:
    protocol = "https" if use_ssl else "http"
    command = f"winrs -r:{protocol}://{host}:{port} -u:{username} -p:{password} cmd"

    try:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        print(f"Connected to {host}. Type 'exit' to close the session.")
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())

            if "Microsoft Windows" in output:  # Wait for the prompt
                break

        while True:
            command = input()
            if command.lower() == 'exit':
                process.stdin.write("exit\n")
                process.stdin.flush()
                break
            process.stdin.write(command + "\n")
            process.stdin.flush()

            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
                if ">" in output:  # Wait for the prompt
                    break

        process.wait()
        return [{"port": port, "error": "", "message": "Session closed successfully"}], []
    except Exception as e:
        return [], [{"port": port, "error": str(e), "message": "Error executing command"}]

