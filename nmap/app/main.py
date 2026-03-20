from fastapi import FastAPI, HTTPException
import subprocess
import json
import xmltodict
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware with explicit configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporary: allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


def run_nmap(command: list):
    """
    Executes an Nmap command, captures XML output, and converts it to JSON.
    """
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        xml_output = result.stdout
        json_output = json.loads(json.dumps(xmltodict.parse(xml_output)))
        return {"success": True, "output": json_output}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr}


@app.get("/")
async def root():
    return {"message": "nmap rest api is up and running!"}

@app.get("/scan/basic")
def basic_scan(target: str):
    """Performs a basic Nmap scan with service version detection."""
    return run_nmap(["nmap", "-sV", "-oX", "-", target])

@app.get("/scan/ports")
def port_scan(target: str, ports: str):
    """Scans specific ports on a target with service version detection."""
    return run_nmap(["nmap", "-sV", "-p", ports, "-oX", "-", target])

@app.get("/scan/all_ports")
def all_ports_scan(target: str):
    """Scans all 65,535 ports on a target."""
    return run_nmap(["nmap", "-p-", "-oX", "-", target])

@app.get("/scan/aggressive")
def aggressive_scan(target: str):
    """Performs an aggressive Nmap scan (-A)."""
    return run_nmap(["nmap", "-A", "-oX", "-", target])

@app.get("/scan/os")
def os_scan(target: str):
    """Attempts to detect the operating system and service versions of the target."""
    return run_nmap(["nmap", "-O", "-sV", "-oX", "-", target])

@app.get("/scan/network")
def network_scan(network: str):
    """Scans an entire network range (ping sweep - no port scanning)."""
    return run_nmap(["nmap", "-sn", "-oX", "-", network])

@app.get("/scan/stealth")
def stealth_scan(target: str):
    """Performs a stealth SYN scan with service version detection (-sS -sV)."""
    return run_nmap(["nmap", "-sS", "-sV", "-oX", "-", target])

@app.get("/scan/no_ping")
def no_ping_scan(target: str):
    """Scans a target without ping, with service version detection (-Pn -sV)."""
    return run_nmap(["nmap", "-Pn", "-sV", "-oX", "-", target])

@app.get("/scan/fast")
def fast_scan(target: str):
    """Performs a quick Nmap scan with service version detection (-F -sV)."""
    return run_nmap(["nmap", "-F", "-sV", "-oX", "-", target])


@app.get("/scan/service_version")
def service_version_scan(target: str, ports: str = None):
    """
    Performs a service version detection scan (-sV).
    Detects service names and versions on open ports.
    Optionally specify ports to scan.
    """
    if ports:
        return run_nmap(["nmap", "-sV", "-p", ports, "-oX", "-", target])
    return run_nmap(["nmap", "-sV", "-oX", "-", target])

