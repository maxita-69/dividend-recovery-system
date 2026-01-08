"""
Dividend Predictor - Predice prossimi dividendi basandosi su pattern storici
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List
from statistics import median, mean
from sqlalchemy.orm import Session
from database.models import Stock, Dividend


class DividendPattern:
    """Rappresenta il pattern di dividendi di uno stock"""

    QUARTERLY = 'quarterly'
    MONTHLY = 'monthly'
    SEMI_ANNUAL = 'semi_annual'
    ANNUAL = 'annual'
    IRREGULAR = 'irregular'

    def __init__(self, pattern_type: str, avg_days: float, avg_amount: float, consistency: float):
        self.pattern_type = pattern_type
        self.avg_days = avg_days  # Giorni medi tra dividendi
        self.avg_amount = avg_amount
        self.consistency = consistency  # 0.0-1.0 quanto è consistente


def analyze_dividend_pattern(dividends: List[Dividend]) -> Optional[DividendPattern]:
    """
    Analizza pattern storico dei dividendi

    Args:
        dividends: Lista di dividendi storici (ordinati per ex_date)

    Returns:
        DividendPattern o None se non abbastanza dati
    """

    if len(dividends) < 4:
        return None  # Servono almeno 4 dividendi per analisi

    # Calcola intervalli tra dividendi
    intervals = []
    amounts = []

    for i in range(1, len(dividends)):
        prev_date = dividends[i-1].ex_date
        curr_date = dividends[i].ex_date
        days = (curr_date - prev_date).days
        intervals.append(days)
        amounts.append(dividends[i].amount)

    if not intervals:
        return None

    avg_interval = mean(intervals)
    avg_amount = mean(amounts)

    # Calcola consistenza (quanto sono simili gli intervalli)
    interval_variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
    interval_std = interval_variance ** 0.5
    consistency = max(0.0, 1.0 - (interval_std / avg_interval))

    # Determina pattern type
    if 25 <= avg_interval <= 35:
        pattern_type = DividendPattern.MONTHLY
    elif 85 <= avg_interval <= 95:
        pattern_type = DividendPattern.QUARTERLY
    elif 175 <= avg_interval <= 190:
        pattern_type = DividendPattern.SEMI_ANNUAL
    elif 355 <= avg_interval <= 375:
        pattern_type = DividendPattern.ANNUAL
    else:
        pattern_type = DividendPattern.IRREGULAR

    return DividendPattern(
        pattern_type=pattern_type,
        avg_days=avg_interval,
        avg_amount=avg_amount,
        consistency=consistency
    )


def predict_next_dividend(
    stock: Stock,
    session: Session,
    use_last_n: int = 8
) -> Optional[Dict]:
    """
    Predice il prossimo dividendo basandosi su pattern storico

    Args:
        stock: Stock object
        session: Database session
        use_last_n: Usa ultimi N dividendi per predizione

    Returns:
        Dict con predizione o None se non possibile
    """

    # Ottieni dividendi storici CONFERMATI
    dividends = (
        session.query(Dividend)
        .filter_by(stock_id=stock.id)
        .filter(Dividend.status == 'CONFIRMED')
        .order_by(Dividend.ex_date.asc())
        .all()
    )

    if len(dividends) < 4:
        return None  # Non abbastanza dati

    # Usa ultimi N dividendi per pattern più recente
    recent_dividends = dividends[-use_last_n:]

    # Analizza pattern
    pattern = analyze_dividend_pattern(recent_dividends)

    if not pattern:
        return None

    # Predici prossimo ex_date
    last_ex_date = recent_dividends[-1].ex_date
    next_ex_date = last_ex_date + timedelta(days=int(pattern.avg_days))

    # Predici amount (conservativo: usa mediana degli ultimi 4)
    recent_amounts = [d.amount for d in recent_dividends[-4:]]
    predicted_amount = median(recent_amounts)

    # Calcola confidence basata su:
    # 1. Consistency del pattern (0.0-1.0)
    # 2. Numero di dividendi storici (più = meglio)
    # 3. Quanto recenti sono i dati

    data_quality = min(1.0, len(dividends) / 20.0)  # Max confidence con 20+ dividendi

    # Penalizza se ultimo dividendo è vecchio (>180 giorni)
    days_since_last = (datetime.now().date() - last_ex_date).days
    recency_factor = 1.0 if days_since_last < 180 else 0.7

    confidence = pattern.consistency * 0.6 + data_quality * 0.3 + recency_factor * 0.1
    confidence = max(0.0, min(1.0, confidence))

    return {
        'ticker': stock.ticker,
        'predicted_ex_date': next_ex_date,
        'predicted_amount': predicted_amount,
        'confidence': confidence,
        'pattern_type': pattern.pattern_type,
        'avg_interval_days': pattern.avg_days,
        'last_ex_date': last_ex_date,
        'last_amount': recent_dividends[-1].amount,
        'dividends_analyzed': len(recent_dividends),
        'status': 'PREDICTED',
        'prediction_source': 'HISTORICAL_PATTERN'
    }


def get_stocks_needing_prediction(session: Session, days_ahead: int = 120) -> List[Stock]:
    """
    Ritorna stock che potrebbero avere un dividendo nei prossimi N giorni
    ma non hanno ancora dividendo predetto

    Args:
        session: Database session
        days_ahead: Giorni da guardare avanti

    Returns:
        Lista di Stock
    """

    cutoff_date = datetime.now().date() + timedelta(days=days_ahead)

    # Trova stock con dividendi storici
    stocks_with_dividends = (
        session.query(Stock)
        .join(Dividend)
        .filter(Dividend.status == 'CONFIRMED')
        .distinct()
        .all()
    )

    stocks_needing_prediction = []

    for stock in stocks_with_dividends:
        # Check se ha già dividendo PREDICTED o CONFIRMED nel futuro
        future_dividend = (
            session.query(Dividend)
            .filter_by(stock_id=stock.id)
            .filter(Dividend.ex_date > datetime.now().date())
            .filter(Dividend.status.in_(['PREDICTED', 'CONFIRMED']))
            .first()
        )

        if not future_dividend:
            # Predici per vedere se dovrebbe averne uno
            prediction = predict_next_dividend(stock, session)

            if prediction and prediction['predicted_ex_date'] <= cutoff_date:
                stocks_needing_prediction.append(stock)

    return stocks_needing_prediction


def save_prediction_to_db(session: Session, prediction: Dict) -> Dividend:
    """
    Salva una predizione nel database

    Args:
        session: Database session
        prediction: Dict dalla funzione predict_next_dividend()

    Returns:
        Dividend object creato
    """

    stock = session.query(Stock).filter_by(ticker=prediction['ticker']).first()

    if not stock:
        raise ValueError(f"Stock {prediction['ticker']} non trovato nel database")

    # Check se esiste già predizione per questa data
    existing = (
        session.query(Dividend)
        .filter_by(stock_id=stock.id, ex_date=prediction['predicted_ex_date'])
        .first()
    )

    if existing:
        # Update esistente
        existing.amount = prediction['predicted_amount']
        existing.status = prediction['status']
        existing.confidence = prediction['confidence']
        existing.prediction_source = prediction['prediction_source']
        session.commit()
        return existing

    # Crea nuovo dividendo predetto
    dividend = Dividend(
        stock_id=stock.id,
        ex_date=prediction['predicted_ex_date'],
        amount=prediction['predicted_amount'],
        status=prediction['status'],
        confidence=prediction['confidence'],
        prediction_source=prediction['prediction_source'],
        dividend_type='predicted'
    )

    session.add(dividend)
    session.commit()

    return dividend
