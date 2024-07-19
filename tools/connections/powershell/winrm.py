from pypsrp.client import Client
import subprocess
import requests
from requests.exceptions import RequestException
import sys
import os
import lib.host as Host


def parameters() -> dict:
    return {
        "host": {
            "type": str,
            "description": "The target host to connect to.",
            "required": True,
            "default": "$$config:DefaultConnections.targetMachine"
        },
        "domain": {
            "type": str,
            "description": "The domain of the target host. Example: htb.local",
            "required": False,
            "default": "$$domain"
        },
        "host_link": {
            "type": str,
            "description": "The link to the target host.",
            "required": False,
            "default": "$$config:DefaultConnections.targetMachine forest.$$domain $$domain"
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


import socket

# Global variable to store the DNS override
dns_override = None


# Custom socket.getaddrinfo function
def custom_getaddrinfo(*args):
    global dns_override
    if dns_override and args[0] in dns_override:
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (dns_override[args[0]], args[1]))]
    return original_getaddrinfo(*args)


def windows(host: str, domain: str, host_link: str, username: str, password: str) -> None:
    global dns_override, original_getaddrinfo

    # Parse host_link if it's not empty, "None", or None
    if host_link and host_link.lower() != "none":
        parts = host_link.split()
        if len(parts) >= 2:
            ip = parts[0]
            hostnames = parts[1:]
            dns_override = {hostname: ip for hostname in hostnames}
            print(f"Using DNS override: {dns_override}")

            # Override socket.getaddrinfo
            original_getaddrinfo = socket.getaddrinfo
            socket.getaddrinfo = custom_getaddrinfo

            # Use the first hostname for the connection
            connection_host = hostnames[0]
        else:
            print(
                f"Invalid host_link format. Expected 'IP HOSTNAME [HOSTNAME...]', got '{host_link}'. Using default host.")
            connection_host = host
    else:
        print("No host_link provided or it's set to None. Using default host.")
        connection_host = host

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

    print("WinRM is now configured. Trying to connect to the remote host...")

    try:
        # First, try a basic HTTP GET to the WinRM endpoint
        url = f"http://{connection_host}:5985/wsman"
        response = requests.get(url, timeout=10)
        print(f"HTTP GET response: Status {response.status_code}, Content: {response.text[:100]}...")

        # Now try the WinRM connection
        client = Client(
            connection_host,
            username=f"{domain}\\{username}" if domain else username,
            password=password,
            ssl=False,
            auth="ntlm",
            encryption='never'  # For troubleshooting only, remove in production
        )

        # Test connection
        stdout, stderr, rc = client.execute_cmd("hostname")
        remote_hostname = stdout.strip()
        print(f"Connected successfully. Remote hostname: {remote_hostname}")

        is_powershell_mode = False
        print("Starting interactive mode. Type ';exit' to quit. To see internal commands, type ';;'")
        while True:
            command = input(f"WinRM@{remote_hostname} ({'PS' if is_powershell_mode else 'CMD'}) > ")
            if command.lower() == ";exit":
                break
            elif command.lower() == ";;":
                print("Internal commands:")
                print("  ;exit - Exit interactive mode")
                print("  ;;    - Show internal commands")
                print("  ;cmd  - Switch to CMD mode")
                print("  ;ps   - Switch to PowerShell mode")
                continue
            elif command.lower() == ";cmd":
                is_powershell_mode = False
                continue
            elif command.lower() == ";ps":
                is_powershell_mode = True
                continue

            try:
                if is_powershell_mode:
                    stdout, stderr, rc = client.execute_ps(command)
                else:
                    stdout, stderr, rc = client.execute_cmd(command)

                print(stdout)
                if stderr:
                    print(f"STDERR: {stderr}")
                if rc != 0:
                    print(f"Command returned non-zero exit code: {rc}")
            except Exception as e:
                print(f"Error executing command: {str(e)}")

    except RequestException as e:
        print(f"HTTP request failed: {str(e)}")
    except Exception as e:
        print(f"WinRM connection failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        if hasattr(e, 'response'):
            print(f"Response status code: {e.response.status_code}")
            print(f"Response content: {e.response.text}")
    finally:
        # Restore original socket.getaddrinfo if it was overridden
        if dns_override:
            socket.getaddrinfo = original_getaddrinfo
