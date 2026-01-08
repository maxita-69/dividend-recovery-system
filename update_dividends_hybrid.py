"""
Hybrid Dividend Update System
Combina dati IBKR (ufficiali) con predizioni storiche

Strategia:
1. Controlla IBKR per dividendi ufficiali annunciati
2. Se non disponibile, usa predizione basata su storico
3. Marca confidence level e source
"""

import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from database.models import Stock, Dividend, DataCollectionLog
from dividend_predictor import predict_next_dividend, save_prediction_to_db

# Import IBKR se disponibile
try:
    from ibkr_dividend_downloader import download_dividend_data
    IBKR_AVAILABLE = True
except ImportError:
    IBKR_AVAILABLE = False
    print("⚠️ IBKR API non disponibile - si userà solo predizione storica")


# ============================================================
# Database Connection
# ============================================================

def create_database_session(db_path='data/dividend_recovery.db'):
    """Crea sessione database"""
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


# ============================================================
# Hybrid Strategy
# ============================================================

def get_next_dividend_hybrid(stock: Stock, session) -> dict:
    """
    Strategy ibrida: IBKR first, poi historical prediction

    Args:
        stock: Stock object
        session: Database session

    Returns:
        Dict con dividendo info e metadata
    """

    result = {
        'ticker': stock.ticker,
        'has_data': False,
        'source': None,
        'data': None
    }

    # STEP 1: Prova con IBKR (se disponibile)
    if IBKR_AVAILABLE:
        try:
            print(f"   🔍 Querying IBKR for {stock.ticker}...")
            ibkr_data = download_dividend_data(stock.ticker)

            if ibkr_data and ibkr_data.get('ex_date'):
                result['has_data'] = True
                result['source'] = 'IBKR'
                result['data'] = {
                    'ticker': stock.ticker,
                    'predicted_ex_date': datetime.strptime(ibkr_data['ex_date'], '%Y-%m-%d').date(),
                    'predicted_amount': ibkr_data['last_dividend'],
                    'confidence': 1.0,  # IBKR = ufficiale
                    'status': 'CONFIRMED',
                    'prediction_source': 'IBKR',
                    'pay_date': ibkr_data.get('pay_date'),
                    'projected_dividend': ibkr_data.get('projected_dividend')
                }
                print(f"   ✅ IBKR data found: {ibkr_data['last_dividend']} on {ibkr_data['ex_date']}")
                return result

        except Exception as e:
            print(f"   ⚠️ IBKR query failed: {str(e)}")

    # STEP 2: Fallback su predizione storica
    print(f"   🔮 Using historical pattern prediction...")
    prediction = predict_next_dividend(stock, session, use_last_n=8)

    if prediction:
        result['has_data'] = True
        result['source'] = 'HISTORICAL_PATTERN'
        result['data'] = prediction
        print(f"   ✅ Predicted: {prediction['predicted_amount']:.4f} on {prediction['predicted_ex_date']} "
              f"(confidence: {prediction['confidence']:.2%})")
    else:
        print(f"   ❌ No prediction possible - not enough historical data")

    return result


# ============================================================
# Update Functions
# ============================================================

def update_dividend_for_stock(stock: Stock, session):
    """
    Aggiorna/predice prossimo dividendo per uno stock

    Args:
        stock: Stock object
        session: Database session
    """

    print(f"\n{'='*60}")
    print(f"📊 Processing: {stock.ticker} - {stock.name}")
    print(f"{'='*60}")

    # Check se ha già dividendo futuro
    future_dividend = (
        session.query(Dividend)
        .filter_by(stock_id=stock.id)
        .filter(Dividend.ex_date > datetime.now().date())
        .filter(Dividend.status.in_(['PREDICTED', 'CONFIRMED']))
        .first()
    )

    if future_dividend:
        print(f"   ℹ️ Already has future dividend: {future_dividend.ex_date} "
              f"({future_dividend.status}, confidence: {future_dividend.confidence:.2%})")
        print(f"   ⏭️ Skipping...")
        return

    # Ottieni prossimo dividendo con strategy ibrida
    result = get_next_dividend_hybrid(stock, session)

    if not result['has_data']:
        print(f"   ⚠️ No dividend data available")

        # Log
        log = DataCollectionLog(
            source='HYBRID',
            operation='dividend_prediction',
            stock_ticker=stock.ticker,
            status='no_data',
            message='Not enough historical data for prediction'
        )
        session.add(log)
        session.commit()
        return

    # Salva nel database
    try:
        dividend = save_prediction_to_db(session, result['data'])
        print(f"   💾 Saved to database (ID: {dividend.id})")

        # Log success
        log = DataCollectionLog(
            source=result['source'],
            operation='dividend_prediction',
            stock_ticker=stock.ticker,
            status='success',
            records_processed=1,
            message=f"Dividend predicted/confirmed via {result['source']}"
        )
        session.add(log)
        session.commit()

    except Exception as e:
        print(f"   ❌ Error saving to database: {str(e)}")

        # Log error
        log = DataCollectionLog(
            source='HYBRID',
            operation='dividend_prediction',
            stock_ticker=stock.ticker,
            status='error',
            message=str(e)
        )
        session.add(log)
        session.commit()


# ============================================================
# Main
# ============================================================

def main():
    """Main execution"""

    print("=" * 70)
    print("HYBRID DIVIDEND UPDATE SYSTEM")
    print("IBKR (official) + Historical Pattern Prediction")
    print("=" * 70)
    print()

    if IBKR_AVAILABLE:
        print("✅ IBKR API available - will query official data first")
    else:
        print("⚠️ IBKR API not available - using historical prediction only")

    print()

    session = create_database_session()

    # Ottieni tutti gli stock
    stocks = session.query(Stock).order_by(Stock.ticker).all()

    print(f"\n📋 Found {len(stocks)} stocks in database")
    print(f"🎯 Processing each stock for dividend prediction...\n")

    success_count = 0
    skip_count = 0
    error_count = 0

    for i, stock in enumerate(stocks, 1):
        print(f"\n[{i}/{len(stocks)}] ", end='')

        try:
            # Check before
            had_future = session.query(Dividend).filter_by(stock_id=stock.id).filter(
                Dividend.ex_date > datetime.now().date()
            ).count() > 0

            update_dividend_for_stock(stock, session)

            # Check after
            has_future = session.query(Dividend).filter_by(stock_id=stock.id).filter(
                Dividend.ex_date > datetime.now().date()
            ).count() > 0

            if has_future and not had_future:
                success_count += 1
            elif had_future:
                skip_count += 1

        except Exception as e:
            print(f"   ❌ Unexpected error: {str(e)}")
            error_count += 1

    # Summary
    print("\n" + "=" * 70)
    print("✅ PROCESS COMPLETED")
    print("=" * 70)
    print(f"\n📊 SUMMARY:")
    print(f"   Total stocks: {len(stocks)}")
    print(f"   ✅ New predictions: {success_count}")
    print(f"   ⏭️ Skipped (already had): {skip_count}")
    print(f"   ❌ Errors: {error_count}")
    print()

    # Stats finali
    total_dividends = session.query(Dividend).count()
    confirmed = session.query(Dividend).filter_by(status='CONFIRMED').count()
    predicted = session.query(Dividend).filter_by(status='PREDICTED').count()

    print(f"📈 DATABASE STATS:")
    print(f"   Total dividends: {total_dividends}")
    print(f"   └─ Confirmed: {confirmed}")
    print(f"   └─ Predicted: {predicted}")
    print()

    session.close()


if __name__ == '__main__':
    main()
