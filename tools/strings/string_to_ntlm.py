import lib.host as Host
import hashlib
import binascii


def parameters() -> dict:
    return {
        "string": {
            "type": str,
            "description": "The string to convert to NTLM hash.",
            "required": True
        }
    }


def resultAnalysis(result: tuple) -> str:
    nthash, lmhash = result
    return f"NT Hash: {nthash}\nLM Hash: {lmhash}"


def linux(string: str) -> (tuple):
    print(f"String: {string}")
    nthash = hashlib.new('md4', string.encode('utf-16le')).digest()
    lmhash = binascii.hexlify(nthash).decode('utf-8')
    return nthash, lmhash
