import subprocess
from requests.exceptions import RequestException
import tempfile


def parameters() -> dict:
    return {
        "host": {
            "type": str,
            "description": "The target host to connect to.",
            "required": True,
            "default": "$$config:DefaultConnections.targetMachine"
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
        }
    }


def kali(host: str, username: str, password: str) -> str:
    toReturn = f"""
    This module is not natively supported in Kali Linux. Instead, use evil-winrm.
    
    1. Install evil-winrm:
    sudo apt install evil-winrm
    
    2. Run evil-winrm:
    evil-winrm -i {host} -u {username} -p {password}
    """
    return toReturn


def windows(host: str, username: str, password: str) -> None:

    # Configure WinRM on the local machine
    cmd = [
        ["winrm.cmd", "quickconfig", "-q"],
        ["winrm.cmd", "set", "winrm/config/client", "@{TrustedHosts=\"*\"}"],
        ["winrm.cmd", "set", "winrm/config/service", "@{AllowUnencrypted=\"true\"}"]
    ]

    for command in cmd:
        print(f"Running command: {' '.join(command)}")
        try:
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running command: {e}")
            print(f"STDOUT: {e.stdout.decode()}")
            print(f"STDERR: {e.stderr.decode()}")

    print("WinRM is now configured. Trying to pull up PowerShell window...")

    try:
        ps_script = f"""
        $svcPassword = ConvertTo-SecureString '{password}' -AsPlainText -Force
        $login = New-Object System.Management.Automation.PSCredential('{host}\\{username}', $svcPassword)
        Enter-PSSession -ComputerName {host} -Credential $login
        """

        print("")
        print("==POWERSHELL==")
        print(ps_script)
        print("==============")


        # Create a temporary file to store the PowerShell script
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ps1') as temp_file:
            temp_file.write(ps_script.encode('utf-8'))
            temp_file_path = temp_file.name

        # Command to run PowerShell with the script
        powershell_command = f'powershell.exe -ExecutionPolicy Bypass -File "{temp_file_path}"'

        # Run the PowerShell script in a new window
        subprocess.Popen(powershell_command, creationflags=subprocess.CREATE_NEW_CONSOLE)

    except Exception as e:
        print(f"PowerShell failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        if hasattr(e, 'response'):
            print(f"Response status code: {e.response.status_code}")
            print(f"Response content: {e.response.text}")

