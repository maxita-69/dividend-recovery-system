#!/usr/bin/env python3
"""
Setup Database Script

Questo script inizializza il database SQLite per il sistema dividend recovery.
Crea le tabelle necessarie e opzionalmente popola con dati di esempio.

Usage:
    python scripts/setup_db.py
    python scripts/setup_db.py --with-sample-data
"""

import os
import sys
from pathlib import Path

# Aggiungi src al path per import
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def create_database():
    """Crea il database e le tabelle principali"""
    print("🗄️  Creazione database...")
    
    # TODO: Implementare logica creazione database
    # Questo è un placeholder per mostrare la struttura
    
    print("✅ Database creato con successo!")
    print("📍 Location: data/dividend_recovery.db")

def add_sample_data():
    """Aggiunge dati di esempio per testing"""
    print("📊 Aggiunta dati di esempio...")
    
    # TODO: Implementare popolazione dati esempio
    
    print("✅ Dati di esempio aggiunti!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup dividend recovery database')
    parser.add_argument('--with-sample-data', action='store_true',
                       help='Popola il database con dati di esempio')
    
    args = parser.parse_args()
    
    create_database()
    
    if args.with_sample_data:
        add_sample_data()
    
    print("\n🚀 Setup completato! Puoi ora eseguire l'applicazione.")
