import lib.host as Host


def parameters() -> dict:
    return {
        "host": {
            "type": str,
            "description": "The IP address of the host to ping.",
            "required": True,
            "default": "$$config:DefaultConnections.targetMachine"
        },
        "iterations": {
            "type": int,
            "description": "The number of times to ping the host.",
            "required": False,
            "default": 3
        },
        "timeout": {
            "type": int,
            "description": "The timeout for each ping in seconds.",
            "required": False,
            "default": 1
        },
        "return": {
            "type": bool,
            "description": "Returns True if the host is reachable, False otherwise."
        }
    }


def resultAnalysis(result: bool) -> str:
    return "Host is reachable." if result else "Host is unreachable."


def linux(host: str, iterations: int, timeout: int) -> bool:
    return Host.executeShellScript(["ping", "-c", str(iterations), "-W", str(timeout), host])[0] == 0


def kali(host: str, iterations: int, timeout: int) -> bool:
    return linux(host, iterations, timeout)


def windows(host: str, iterations: int, timeout: int) -> bool:
    return Host.executeShellScript(["ping", "-n", str(iterations), "-w", str(timeout * 1000), host])[0] == 0
