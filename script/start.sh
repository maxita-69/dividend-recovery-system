#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

VENV_DIR="$PROJECT_DIR/venv"
STREAMLIT="$VENV_DIR/Scripts/streamlit.exe"

echo "============================================"
echo "Dividend Recovery Trading System - START"
echo "============================================"

# 1. Virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "[1/4] Creazione virtual environment..."
    python -m venv venv
    echo "        Installazione dipendenze Python (può richiedere tempo)..."
    "$VENV_DIR/Scripts/pip.exe" install -r requirements.txt -q
else
    echo "[1/4] Virtual environment OK"
fi

# 2. Libera porte
echo "[2/4] Verifica porte..."
for port in 8501 4200; do
    pid=$(netstat -ano | grep ":$port" | grep LISTENING | awk '{print $5}')
    if [ -n "$pid" ]; then
        echo "        Porta $port occupata (PID $pid). Libero..."
        taskkill //F //PID "$pid" 2>/dev/null || true
    fi
done
sleep 1

# 3. Avvio servizi
echo "[3/4] Avvio servizi..."

"$STREAMLIT" run app/Home.py --server.port 8501 --browser.gatherUsageStats false > streamlit1.log 2>&1 &
echo $! > "$PROJECT_DIR/.pid_streamlit1"
echo "        Streamlit Dashboard -> http://localhost:8501"
sleep 4

cd frontend
npm run start > "$PROJECT_DIR/angular.log" 2>&1 &
echo $! > "$PROJECT_DIR/.pid_angular"
echo "        Angular Frontend    -> http://localhost:4200"
cd "$PROJECT_DIR"

# Attesa fino a 40s per Angular (prima build lenta)
echo "        Attesa compilazione Angular..."
for i in $(seq 1 40); do
    if netstat -ano | grep -q ":4200.*LISTENING"; then
        break
    fi
    sleep 1
done

# 4. Verifica
echo "[4/4] Verifica avvio..."
sleep 3

OK=true
for port in 8501 4200; do
    if netstat -ano | grep -q ":$port.*LISTENING"; then
        echo "        Porta $port -> OK"
    else
        echo "        Porta $port -> NON ATTIVA"
        OK=false
    fi
done

echo ""
if [ "$OK" = true ]; then
    echo "============================================"
    echo "TUTTI I SERVIZI ATTIVI"
    echo "- http://localhost:8501  (Dashboard)"
    echo "- http://localhost:4200  (Angular)"
    echo "============================================"
else
    echo "ATTENZIONE: alcuni servizi non sono attivi."
    echo "Controlla i log: streamlit1.log, angular.log"
fi

echo ""
echo "Per arrestare: ./script/stop.sh"
