import socket
import subprocess


def parameters() -> dict:
    return {
        "host": {
            "type": str,
            "description": "The target host to check for WinRM.",
            "required": True,
            "default": "$$config:DefaultConnections.targetMachine"
        },
        "ports": {
            "type": str,
            "description": "The ports to check, comma-separated. You can also specify a range using a hyphen. Example: 5985,5986 or 5985-5986",
            "required": False,
            "default": "5985,5986"
        }
    }


def resultAnalysis(result: tuple) -> str:
    successList, errorList = result
    if len(successList) > 0:
        success = "Success:\n"
        for item in successList:
            success += f"   Port {item['port']}\n"
    else:
        success = ""

    if len(errorList) > 0:
        error = "Errors:\n"
        for item in errorList:
            error += f"   Port {item['port']}: {item['error']}\n"
    else:
        error = ""

    return success + error + "\n\nUse memory view to see the full result."


def linux(host: str, ports: str) -> tuple:
    global sock
    port_list = ports.split(",")
    for i in range(len(port_list)):
        if "-" in str(port_list[i]):
            start, end = port_list[i].split("-")
            port_list += list(range(int(start), int(end) + 1))
            port_list.remove(port_list[i])

    for i in range(len(port_list)):
        port_list[i] = str(port_list[i])

    successList = []
    errorList = []

    for port in port_list:
        print("Checking port", port)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            if sock.connect_ex((host, int(port))) == 0:

                # Try to get WinRM banner
                sock.send(b"POST /wsman HTTP/1.1\r\nHost: " + host.encode() + b"\r\n\r\n")
                banner = sock.recv(1024).decode('utf-8', errors='ignore')
                if "Server: Microsoft-HTTPAPI" in banner:
                    successList.append({"port": port, "error": "", "message": banner})
                else:
                    errorList.append({"port": port, "error": "No WinRM banner detected", "message": ""})
            else:
                errorList.append({"port": port, "error": "Port is closed", "message": ""})
        except socket.error as e:
            errorList.append({"port": port, "error": str(e), "message": f"Error checking port {port} on {host}"})
        finally:
            sock.close()

    return successList, errorList


def windows(host: str, ports: str) -> tuple:
    global sock

    successList, errorList = linux(host, ports)

    # Additional Windows-specific WinRM check
    try:
        print(f"Checking WinRM on {host} using winrm command")
        command = f"winrm id -r:{host} -auth:basic"
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate()
        if "IdentifyResponse" in stdout.decode():
            successList.append({"port": "WinRM (Windows additional check)", "error": "", "message": "WinRM is responsive"})
        else:
            errorList.append({"port": "WinRM (Windows additional check)", "error": "WinRM is not responsive", "message": stderr.decode()})
    except subprocess.SubprocessError as e:
        errorList.append({"port": "WinRM (Windows additional check)", "error": str(e), "message": "Error running WinRM command"})

    return successList, errorList
