#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "============================================"
echo "Dividend Recovery Trading System - STOP"
echo "============================================"

# 1. Ferma dai PID file
for pidfile in "$PROJECT_DIR"/.pid_*; do
    if [ -f "$pidfile" ]; then
        pid=$(cat "$pidfile")
        name=$(basename "$pidfile")
        if taskkill //F //PID "$pid" 2>/dev/null; then
            echo "Arrestato $name (PID $pid)"
        else
            echo "$name (PID $pid) già chiuso o non accessibile"
        fi
        rm -f "$pidfile"
    fi
done

# 2. Fallback: libera le porte per PID specifico
echo "Verifica porte residue..."
for port in 8501 4200; do
    pid=$(netstat -ano | grep ":$port" | grep LISTENING | awk '{print $5}')
    if [ -n "$pid" ]; then
        echo "Porta $port occupata da PID $pid. Arresto..."
        taskkill //F //PID "$pid" 2>/dev/null || true
    fi
done

echo ""
echo "Servizi arrestati."
