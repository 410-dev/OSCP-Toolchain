import lib.host as Host


def parameters() -> dict:
    return {
        "param": {
            "type": str,
            "description": "The parameters to execute.",
            "required": True,
            "default": "-A -T5 $$config:DefaultConnections.targetMachine"
        }
    }


def kali(param: str) -> str:
    import tools.scan.services.using_nmap1 as nmap1
    return nmap1.kali(param)

