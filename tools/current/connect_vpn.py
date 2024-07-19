import lib.host as Host


def parameters() -> dict:
    return {
        "vpnfile": {
            "type": str,
            "description": "The OVPN file for OpenVPN connection",
            "required": True,
            "default": "$$config:VPNConnection.filePath"
        }
    }


def kali(vpnfile: str) -> int:
    commandStruct = vpnfile.split(" ")
    command = ["sudo", "openvpn"]
    command.extend(commandStruct)
    return Host.executeShellScriptAsyncBackground(command)
