import os
import sys
import json
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
os.chdir(PROJECT_DIR)

PID_FILE = PROJECT_DIR / ".service_pids.json"
PORTS = [8501, 8502, 4200]


def kill_pid(pid):
    subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)


def kill_port(port):
    result = subprocess.run(
        f'netstat -ano | findstr ":{port}" | findstr "LISTENING"',
        shell=True, capture_output=True, text=True
    )
    if result.returncode == 0 and result.stdout:
        for line in result.stdout.strip().splitlines():
            parts = line.split()
            if len(parts) >= 5:
                pid = parts[-1]
                kill_pid(pid)


def main():
    print("=" * 44)
    print("Dividend Recovery Trading System - STOP")
    print("=" * 44)

    # Ferma dai PID salvati
    if PID_FILE.exists():
        try:
            pids = json.loads(PID_FILE.read_text())
            for name, pid in pids.items():
                print(f"Arresto {name} (PID {pid})...")
                kill_pid(pid)
        except Exception:
            pass
        PID_FILE.unlink()

    # Fallback: libera le porte
    print("Verifica porte residue...")
    for port in PORTS:
        kill_port(port)

    print()
    print("Servizi arrestati.")
    try:
        input("Premi INVIO per chiudere...")
    except EOFError:
        pass


if __name__ == "__main__":
    main()
