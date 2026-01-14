#!/usr/bin/env python3
"""
Script per analizzare il database e vedere quali titoli sono stati acquisiti
"""
import sqlite3
from datetime import datetime
from collections import defaultdict

DB_PATH = "data/dividend_recovery.db"

def analyze_database():
    """Analizza il database e mostra statistiche sui titoli"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "="*80)
    print(" " * 25 + "ANALISI DATABASE TITOLI")
    print("="*80)

    # 1. Lista tutti i titoli nel database
    print("\n📊 TITOLI NEL DATABASE:")
    print("-" * 80)

    cursor.execute("""
        SELECT ticker, name, market, currency, created_at
        FROM stocks
        ORDER BY ticker
    """)

    stocks = cursor.fetchall()
    print(f"\nTotale titoli registrati: {len(stocks)}\n")

    if stocks:
        for ticker, name, market, currency, created_at in stocks:
            print(f"  • {ticker:15s} - {name[:40]:40s} ({market}, {currency})")

    # 2. Analisi prezzi storici per ogni titolo
    print("\n" + "="*80)
    print("\n📈 DATI PREZZI STORICI:")
    print("-" * 80)

    cursor.execute("""
        SELECT s.ticker,
               COUNT(pd.id) as num_prices,
               MIN(pd.date) as first_date,
               MAX(pd.date) as last_date
        FROM stocks s
        LEFT JOIN price_data pd ON s.id = pd.stock_id
        GROUP BY s.ticker
        ORDER BY s.ticker
    """)

    price_stats = cursor.fetchall()

    for ticker, num_prices, first_date, last_date in price_stats:
        if num_prices > 0:
            print(f"\n{ticker}:")
            print(f"  ✅ Prezzi: {num_prices} record")
            print(f"  📅 Periodo: {first_date} → {last_date}")
        else:
            print(f"\n{ticker}:")
            print(f"  ❌ Nessun prezzo storico")

    # 3. Analisi dividendi per ogni titolo
    print("\n" + "="*80)
    print("\n💰 DATI DIVIDENDI:")
    print("-" * 80)

    cursor.execute("""
        SELECT s.ticker,
               COUNT(d.id) as num_dividends,
               MIN(d.ex_date) as first_div_date,
               MAX(d.ex_date) as last_div_date,
               SUM(CASE WHEN d.status = 'CONFIRMED' THEN 1 ELSE 0 END) as confirmed,
               SUM(CASE WHEN d.status = 'PREDICTED' THEN 1 ELSE 0 END) as predicted
        FROM stocks s
        LEFT JOIN dividends d ON s.id = d.stock_id
        GROUP BY s.ticker
        ORDER BY s.ticker
    """)

    div_stats = cursor.fetchall()

    for ticker, num_divs, first_div, last_div, confirmed, predicted in div_stats:
        if num_divs > 0:
            print(f"\n{ticker}:")
            print(f"  ✅ Dividendi: {num_divs} record")
            print(f"  📅 Periodo: {first_div} → {last_div}")
            print(f"  📊 Status: {confirmed} CONFIRMED, {predicted} PREDICTED")
        else:
            print(f"\n{ticker}:")
            print(f"  ❌ Nessun dividendo")

    # 4. Riepilogo finale
    print("\n" + "="*80)
    print("\n📋 RIEPILOGO:")
    print("-" * 80)

    cursor.execute("""
        SELECT
            COUNT(DISTINCT s.id) as total_stocks,
            COUNT(DISTINCT pd.stock_id) as stocks_with_prices,
            COUNT(DISTINCT d.stock_id) as stocks_with_dividends,
            SUM(CASE WHEN pd.stock_id IS NOT NULL AND d.stock_id IS NOT NULL THEN 1 ELSE 0 END) as stocks_complete
        FROM stocks s
        LEFT JOIN price_data pd ON s.id = pd.stock_id
        LEFT JOIN dividends d ON s.id = d.stock_id
    """)

    total, with_prices, with_divs, complete = cursor.fetchone()

    print(f"\n  📊 Totale titoli:                    {total}")
    print(f"  📈 Titoli con prezzi storici:        {with_prices}")
    print(f"  💰 Titoli con dividendi:             {with_divs}")

    # 5. Titoli per mercato
    print("\n" + "="*80)
    print("\n🌍 DISTRIBUZIONE PER MERCATO:")
    print("-" * 80)

    cursor.execute("""
        SELECT market, COUNT(*) as num_stocks
        FROM stocks
        GROUP BY market
        ORDER BY num_stocks DESC
    """)

    markets = cursor.fetchall()
    for market, count in markets:
        market_name = market if market else "Non specificato"
        print(f"  • {market_name:20s}: {count} titoli")

    # 6. Ultimi download
    print("\n" + "="*80)
    print("\n📥 ULTIMI DOWNLOAD:")
    print("-" * 80)

    cursor.execute("""
        SELECT stock_ticker, source, operation, status, timestamp, message
        FROM data_collection_logs
        ORDER BY timestamp DESC
        LIMIT 10
    """)

    logs = cursor.fetchall()
    if logs:
        for ticker, source, operation, status, timestamp, message in logs:
            print(f"\n  {timestamp}")
            print(f"    Ticker: {ticker}")
            print(f"    Source: {source} | Operation: {operation}")
            print(f"    Status: {status}")
            if message:
                print(f"    Message: {message[:60]}...")
    else:
        print("\n  Nessun log disponibile")

    print("\n" + "="*80 + "\n")

    conn.close()

if __name__ == "__main__":
    try:
        analyze_database()
    except Exception as e:
        print(f"\n❌ Errore nell'analisi del database: {str(e)}")
        import traceback
        traceback.print_exc()
