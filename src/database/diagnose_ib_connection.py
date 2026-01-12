#!/usr/bin/env python3
"""
Diagnostic script per testare connessione a IB Gateway
Prova multiple configurazioni e fornisce info dettagliate
"""

from ib_insync import IB
import socket
import time

def test_port_open(host, port):
    """Verifica se la porta è aperta e in ascolto"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        return False

def test_connection(host, port, client_id):
    """Tenta connessione con parametri specifici"""
    ib = IB()
    try:
        print(f"  ⏳ Tentativo: {host}:{port} (clientId={client_id})")
        ib.connect(host, port, clientId=client_id, timeout=10)
        print(f"  ✅ SUCCESSO! Connesso come clientId={client_id}")
        print(f"  📊 Account: {ib.managedAccounts()}")
        ib.disconnect()
        return True
    except Exception as e:
        print(f"  ❌ Fallito: {e}")
        return False

print("=" * 60)
print("🔍 DIAGNOSTICA CONNESSIONE IB GATEWAY")
print("=" * 60)

# Test 1: Verifica porta aperta
print("\n1️⃣ Verifica se porta 4002 è in ascolto...")
if test_port_open('127.0.0.1', 4002):
    print("  ✅ Porta 4002 APERTA e in ascolto")
else:
    print("  ❌ Porta 4002 NON risponde")
    print("  💡 Verifica che IB Gateway sia:")
    print("     - In esecuzione (processo attivo)")
    print("     - Completamente loggato (connesso ai server IBKR)")
    print("     - Mostra 'Connected' in verde nella GUI")

# Test 2: Prova con diversi client IDs
print("\n2️⃣ Test connessione con diversi Client IDs...")
for client_id in [0, 1, 2, 100, 999]:
    if test_connection('127.0.0.1', 4002, client_id):
        print(f"\n🎯 SOLUZIONE TROVATA: usa clientId={client_id}")
        break
    time.sleep(1)

# Test 3: Prova localhost vs 127.0.0.1
print("\n3️⃣ Test 'localhost' invece di '127.0.0.1'...")
test_connection('localhost', 4002, 1)

# Test 4: Info rete
print("\n4️⃣ Informazioni rete locale...")
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
print(f"  📍 Hostname: {hostname}")
print(f"  📍 IP locale: {local_ip}")

print("\n" + "=" * 60)
print("📋 CHECKLIST TROUBLESHOOTING:")
print("=" * 60)
print("  ☐ IB Gateway è in esecuzione?")
print("  ☐ IB Gateway mostra 'Connected' (verde) nella finestra principale?")
print("  ☐ Hai fatto login con username/password?")
print("  ☐ Il login è completato (non più in fase di connessione)?")
print("  ☐ Nelle impostazioni API Settings:")
print("     - 'Socket port' è 4002?")
print("     - 'Read-Only API' è disabilitato (se vuoi fare operazioni)?")
print("     - 'Master API client ID' è vuoto o corrisponde?")
print("  ☐ Firewall/Antivirus non blocca la porta 4002?")
print("  ☐ Hai provato a riavviare IB Gateway dopo aver modificato le impostazioni?")
print("=" * 60)
