#!/usr/bin/env python3
"""
Script di test per scaricare e analizzare dati da Yahoo Finance
================================================================

SCOPO:
  Testare il download da Yahoo Finance e verificare la qualità dei dati
  - Scaricare prezzi storici
  - Scaricare dividendi
  - Analizzare completezza e correttezza dei dati

COME USARE:
  python test_yahoo_download.py

PUOI MODIFICARE:
  - TEST_TICKERS: lista dei ticker da testare
  - START_DATE: data di inizio download
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd

# Aggiungi il path per importare i provider
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import diretto del provider Yahoo
import yfinance as yf

# Implementazione semplificata del provider Yahoo per il test
class YahooProvider:
    """Provider Yahoo Finance per test"""

    def fetch_prices(self, symbol, start_date=None):
        """Scarica prezzi storici da Yahoo Finance"""
        ticker = yf.Ticker(symbol)
        if start_date:
            data = ticker.history(start=start_date)
        else:
            data = ticker.history(period="max")
        return data if not data.empty else None

    def fetch_dividends(self, symbol, start_date=None):
        """Scarica dividendi da Yahoo Finance"""
        ticker = yf.Ticker(symbol)
        dividends = ticker.dividends
        if dividends.empty:
            return None
        if start_date:
            dividends = dividends[dividends.index >= start_date]
        return pd.DataFrame({'Dividends': dividends}) if not dividends.empty else None

# ============================================================
# CONFIGURAZIONE
# ============================================================

# Ticker da testare (modifica questa lista)
TEST_TICKERS = [
    "FBK.MI",      # FinecoBank - titolo italiano
    "ENI.MI",      # Eni - per confronto
    "ENEL.MI",     # Enel - per confronto
    "AEXAY",       # Titolo americano
]

# Data di inizio (ultimi 2 anni)
START_DATE = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')

# ============================================================
# FUNZIONI DI ANALISI
# ============================================================

def analyze_prices(ticker, prices_df):
    """Analizza i dati dei prezzi scaricati"""
    print(f"\n{'='*70}")
    print(f"📈 ANALISI PREZZI - {ticker}")
    print('='*70)

    if prices_df is None or prices_df.empty:
        print("❌ Nessun dato prezzi scaricato")
        return False

    # Statistiche base
    num_records = len(prices_df)
    first_date = prices_df.index.min()
    last_date = prices_df.index.max()

    print(f"\n✅ Record scaricati: {num_records}")
    print(f"📅 Periodo: {first_date.strftime('%Y-%m-%d')} → {last_date.strftime('%Y-%m-%d')}")
    print(f"🗓️  Giorni coperti: {(last_date - first_date).days} giorni")

    # Verifica colonne presenti
    print(f"\n📊 Colonne disponibili:")
    for col in prices_df.columns:
        print(f"  ✅ {col}")

    # Verifica valori nulli
    null_counts = prices_df.isnull().sum()
    print(f"\n🔍 Valori mancanti:")
    if null_counts.sum() == 0:
        print("  ✅ Nessun valore mancante")
    else:
        for col, count in null_counts.items():
            if count > 0:
                print(f"  ⚠️  {col}: {count} valori mancanti ({count/num_records*100:.1f}%)")

    # Verifica valori zero o negativi (anomalie)
    print(f"\n⚠️  Anomalie nei prezzi:")
    anomalies = False
    for col in ['Open', 'High', 'Low', 'Close']:
        if col in prices_df.columns:
            zero_count = (prices_df[col] <= 0).sum()
            if zero_count > 0:
                print(f"  ⚠️  {col}: {zero_count} valori ≤ 0")
                anomalies = True

    if not anomalies:
        print("  ✅ Nessuna anomalia rilevata")

    # Statistiche descrittive
    print(f"\n📊 Statistiche Close Price:")
    print(f"  • Min:    {prices_df['Close'].min():.4f} EUR")
    print(f"  • Max:    {prices_df['Close'].max():.4f} EUR")
    print(f"  • Media:  {prices_df['Close'].mean():.4f} EUR")
    print(f"  • Ultimo: {prices_df['Close'].iloc[-1]:.4f} EUR")

    # Mostra ultimi 5 record
    print(f"\n📋 Ultimi 5 record:")
    print(prices_df.tail(5).to_string())

    return True

def analyze_dividends(ticker, dividends_df):
    """Analizza i dati dei dividendi scaricati"""
    print(f"\n{'='*70}")
    print(f"💰 ANALISI DIVIDENDI - {ticker}")
    print('='*70)

    if dividends_df is None or dividends_df.empty:
        print("⚠️  Nessun dividendo trovato nel periodo")
        print("   (Potrebbe essere normale se il titolo non paga dividendi)")
        return False

    # Statistiche base
    num_dividends = len(dividends_df)
    first_date = dividends_df.index.min()
    last_date = dividends_df.index.max()

    print(f"\n✅ Dividendi trovati: {num_dividends}")
    print(f"📅 Periodo: {first_date.strftime('%Y-%m-%d')} → {last_date.strftime('%Y-%m-%d')}")

    # Statistiche sui dividendi
    print(f"\n📊 Statistiche dividendi:")
    print(f"  • Min:    {dividends_df['Dividends'].min():.4f} EUR")
    print(f"  • Max:    {dividends_df['Dividends'].max():.4f} EUR")
    print(f"  • Media:  {dividends_df['Dividends'].mean():.4f} EUR")
    print(f"  • Totale: {dividends_df['Dividends'].sum():.4f} EUR")

    # Frequenza (calcola intervallo medio tra dividendi)
    if num_dividends > 1:
        dates = sorted(dividends_df.index)
        intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
        avg_interval = sum(intervals) / len(intervals)
        print(f"  • Frequenza media: ogni {avg_interval:.0f} giorni")

        if avg_interval < 100:
            print(f"    → Probabile pagamento trimestrale")
        elif avg_interval < 200:
            print(f"    → Probabile pagamento semestrale")
        else:
            print(f"    → Probabile pagamento annuale")

    # Mostra tutti i dividendi
    print(f"\n📋 Elenco completo dividendi:")
    for date, row in dividends_df.iterrows():
        print(f"  {date.strftime('%Y-%m-%d')}: {row['Dividends']:.4f} EUR")

    return True

def test_ticker(ticker):
    """Testa il download completo per un ticker"""
    print(f"\n\n{'#'*70}")
    print(f"{'#'*70}")
    print(f"##  TICKER: {ticker}")
    print(f"{'#'*70}")
    print(f"{'#'*70}")

    # Inizializza provider
    provider = YahooProvider()

    try:
        # Download prezzi
        print(f"\n🔄 Download prezzi storici da Yahoo Finance...")
        prices = provider.fetch_prices(ticker, start_date=START_DATE)
        prices_ok = analyze_prices(ticker, prices)

        # Download dividendi
        print(f"\n🔄 Download dividendi da Yahoo Finance...")
        dividends = provider.fetch_dividends(ticker, start_date=START_DATE)
        dividends_ok = analyze_dividends(ticker, dividends)

        # Riepilogo finale per questo ticker
        print(f"\n{'='*70}")
        print(f"📋 RIEPILOGO {ticker}")
        print('='*70)
        print(f"  Prezzi:    {'✅ OK' if prices_ok else '❌ ERRORE'}")
        print(f"  Dividendi: {'✅ OK' if dividends_ok else '⚠️  Nessuno (normale se non distribuisce)'}")

        return prices_ok

    except Exception as e:
        print(f"\n❌ ERRORE durante il download di {ticker}:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print(" " * 15 + "TEST YAHOO FINANCE DOWNLOAD")
    print("="*70)
    print(f"\n📅 Download dati dal: {START_DATE}")
    print(f"🎯 Ticker da testare: {', '.join(TEST_TICKERS)}")

    results = {}

    for ticker in TEST_TICKERS:
        results[ticker] = test_ticker(ticker)

    # Riepilogo finale globale
    print(f"\n\n{'#'*70}")
    print(f"{'#'*70}")
    print(f"##  RIEPILOGO FINALE - TUTTI I TICKER")
    print(f"{'#'*70}")
    print(f"{'#'*70}\n")

    for ticker, success in results.items():
        status = "✅ SUCCESSO" if success else "❌ ERRORE"
        print(f"  {ticker:15s} : {status}")

    # Conclusioni
    successful = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\n{'='*70}")
    print(f"📊 STATISTICHE FINALI:")
    print(f"  • Ticker testati:   {total}")
    print(f"  • Download riusciti: {successful}")
    print(f"  • Download falliti:  {total - successful}")
    print(f"  • Tasso successo:   {successful/total*100:.1f}%")

    if successful == total:
        print(f"\n✅ TUTTI I DOWNLOAD COMPLETATI CON SUCCESSO!")
        print(f"   Yahoo Finance funziona correttamente per i ticker testati.")
    elif successful > 0:
        print(f"\n⚠️  ALCUNI DOWNLOAD FALLITI")
        print(f"   Verifica i ticker che hanno dato errore.")
    else:
        print(f"\n❌ TUTTI I DOWNLOAD FALLITI")
        print(f"   Potrebbe esserci un problema di connessione o con Yahoo Finance.")

    print("\n" + "="*70 + "\n")
