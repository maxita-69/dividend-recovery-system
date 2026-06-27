import os
import sys
import json
import subprocess
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
os.chdir(PROJECT_DIR)

PID_FILE = PROJECT_DIR / ".service_pids.json"
PORTS = {
    "streamlit1": 8501,
    "angular": 4200,
}


def check_port(port):
    result = subprocess.run(
        f'netstat -ano | findstr ":{port}" | findstr "LISTENING"',
        shell=True, capture_output=True, text=True
    )
    return result.returncode == 0


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
                subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)


def main():
    print("=" * 44)
    print("Dividend Recovery Trading System - START")
    print("=" * 44)

    # 1. Virtual environment
    venv_path = PROJECT_DIR / "venv"
    if not venv_path.exists():
        print("[1/4] Creazione virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"])
        print("        Installazione dipendenze Python...")
        pip_exe = str((PROJECT_DIR / "venv" / "Scripts" / "pip.exe").resolve())
        subprocess.run([pip_exe, "install", "-r", "requirements.txt", "-q"])
    else:
        print("[1/4] Virtual environment OK")

    # 2. Libera porte
    print("[2/4] Verifica porte...")
    for name, port in PORTS.items():
        kill_port(port)

    time.sleep(1)

    # 3. Avvio servizi
    print("[3/4] Avvio servizi...")

    pids = {}

    print("        Streamlit Dashboard -> http://localhost:8501")
    streamlit_exe = str((PROJECT_DIR / "venv" / "Scripts" / "streamlit.exe").resolve())
    with open("streamlit1.log", "w") as slog:
        p1 = subprocess.Popen(
            [
                streamlit_exe, "run", "app/Home.py",
                "--server.port", "8501", "--browser.gatherUsageStats", "false"
            ],
            stdout=slog, stderr=subprocess.STDOUT
        )
    pids["streamlit1"] = p1.pid
    time.sleep(3)

    print("        Angular Frontend    -> http://localhost:4200")
    # Apre Angular in una nuova console dedicata, nella directory frontend
    frontend_dir = str(PROJECT_DIR / "frontend")
    subprocess.Popen(
        "npm.cmd run start",
        cwd=frontend_dir,
        shell=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    time.sleep(1)

    print("        Attesa compilazione Angular...")
    angular_ready = False
    for i in range(40):
        if check_port(4200):
            angular_ready = True
            break
        time.sleep(1)

    if not angular_ready:
        print("        ATTENZIONE: Angular non risponde entro 40s")

    # Salva PID
    PID_FILE.write_text(json.dumps(pids, indent=2))

    # 4. Verifica
    print("[4/4] Verifica avvio...")
    all_ok = True
    for name, port in PORTS.items():
        if check_port(port):
            print(f"        Porta {port} -> OK")
        else:
            print(f"        Porta {port} -> NON ATTIVA")
            all_ok = False

    print()
    if all_ok:
        print("=" * 44)
        print("TUTTI I SERVIZI ATTIVI")
        print("- http://localhost:8501  Dashboard")
        print("- http://localhost:4200  Angular")
        print("=" * 44)
    else:
        print("ATTENZIONE: alcuni servizi non sono attivi.")

    print()
    print("Per arrestare: python script/stop.py")
    try:
        input("Premi INVIO per chiudere...")
    except EOFError:
        pass


if __name__ == "__main__":
    main()
