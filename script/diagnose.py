import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
os.chdir(PROJECT_DIR)

print("=" * 50)
print("DIAGNOSTICA Dividend Recovery System")
print("=" * 50)

print("\n--- Processi attivi ---")
result = subprocess.run("tasklist | findstr streamlit", shell=True, capture_output=True, text=True)
print(result.stdout if result.stdout else "Nessun processo streamlit trovato")

result = subprocess.run("tasklist | findstr python", shell=True, capture_output=True, text=True)
print(result.stdout if result.stdout else "Nessun processo python trovato")

print("\n--- Porte in ascolto ---")
for port in [8501, 8502, 4200]:
    result = subprocess.run(
        f'netstat -ano | findstr ":{port}" | findstr "LISTENING"',
        shell=True, capture_output=True, text=True
    )
    status = "IN ASCOLTO -> " + result.stdout.strip() if result.stdout else "NON ATTIVA"
    print(f"Porta {port}: {status}")

print("\n--- Log Streamlit 1 ---")
log1 = Path("streamlit1.log")
if log1.exists():
    print(log1.read_text()[-2000:] if len(log1.read_text()) > 2000 else log1.read_text())
else:
    print("File streamlit1.log non trovato")

print("\n--- Log Streamlit 2 ---")
log2 = Path("streamlit2.log")
if log2.exists():
    print(log2.read_text()[-2000:] if len(log2.read_text()) > 2000 else log2.read_text())
else:
    print("File streamlit2.log non trovato")

print("\n--- Angular log ---")
log3 = Path("angular.log")
if log3.exists():
    print(log3.read_text()[-2000:] if len(log3.read_text()) > 2000 else log3.read_text())
else:
    print("File angular.log non trovato")

print("\n" + "=" * 50)
print("Fine diagnostica")
print("=" * 50)
