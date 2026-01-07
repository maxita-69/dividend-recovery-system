"""
Create Sample Data for Testing
Popola database con dati ENEL di esempio
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from database.models import Base, Stock, Dividend, PriceData

def create_sample_data():
    """Crea dati di esempio per ENEL"""
    
    # Create database
    Path('data').mkdir(exist_ok=True)
    db_path = 'data/dividend_recovery.db'
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("📊 Creazione dati esempio ENEL...")
    
    # Create ENEL stock
    enel = Stock(
        ticker='ENEL.MI',
        name='Enel SpA',
        market='Italy',
        sector='Utilities',
        currency='EUR'
    )
    session.add(enel)
    session.flush()
    
    # Add some dividends (esempio realistico)
    dividends_data = [
        ('2023-01-16', 0.19),
        ('2023-07-24', 0.20),
        ('2024-01-15', 0.21),
        ('2024-07-22', 0.21),
        ('2025-01-20', 0.22),
        ('2025-07-21', 0.23),
    ]
    
    for ex_date_str, amount in dividends_data:
        ex_date = datetime.strptime(ex_date_str, '%Y-%m-%d').date()
        div = Dividend(
            stock_id=enel.id,
            ex_date=ex_date,
            amount=amount,
            dividend_type='ordinary'
        )
        session.add(div)
    
    print(f"   ✅ Creati {len(dividends_data)} dividendi")
    
    # Add price data (esempio realistico per ultimi 2 anni)
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2026, 1, 7)
    
    current_date = start_date
    base_price = 6.50
    prices_count = 0
    
    while current_date <= end_date:
        # Skip weekends
        if current_date.weekday() < 5:
            # Simulate realistic price movement
            daily_change = (hash(str(current_date)) % 100 - 50) / 1000  # ±5%
            price = base_price * (1 + daily_change)
            
            # Check if dividend date (simulate drop)
            div_date = current_date.date()
            matching_div = [d for d in dividends_data if datetime.strptime(d[0], '%Y-%m-%d').date() == div_date]
            if matching_div:
                price = price - matching_div[0][1]  # Drop by dividend amount
            
            price_data = PriceData(
                stock_id=enel.id,
                date=current_date.date(),
                open=price * 1.002,
                high=price * 1.01,
                low=price * 0.99,
                close=price,
                volume=10000000 + (hash(str(current_date)) % 5000000),
                adjusted_close=price
            )
            session.add(price_data)
            prices_count += 1
            
            # Update base price gradually
            base_price = price
        
        current_date += timedelta(days=1)
    
    print(f"   ✅ Creati {prices_count} record prezzi")
    
    session.commit()
    print("   ✅ Database popolato con successo!")
    
    session.close()
    
    print(f"\n✅ Database creato: {db_path}")
    print("   Puoi ora eseguire: streamlit run app/Home.py")


if __name__ == '__main__':
    create_sample_data()
