"""
Database Migration - Add Dividend Prediction Support
Aggiunge colonne per gestire dividendi predetti vs confermati
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Path del database
DB_PATH = 'data/dividend_recovery.db'


def migrate_database():
    """Aggiunge colonne per prediction support"""

    print("=" * 60)
    print("DATABASE MIGRATION - DIVIDEND PREDICTION SUPPORT")
    print("=" * 60)

    engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)

    with engine.connect() as conn:
        # Check if columns already exist
        result = conn.execute(text("PRAGMA table_info(dividends)")).fetchall()
        existing_columns = [row[1] for row in result]

        print(f"\n📋 Colonne esistenti: {', '.join(existing_columns)}")

        migrations_needed = []

        # 1. Add 'status' column
        if 'status' not in existing_columns:
            migrations_needed.append({
                'name': 'status',
                'sql': "ALTER TABLE dividends ADD COLUMN status VARCHAR(20) DEFAULT 'CONFIRMED'"
            })

        # 2. Add 'confidence' column
        if 'confidence' not in existing_columns:
            migrations_needed.append({
                'name': 'confidence',
                'sql': "ALTER TABLE dividends ADD COLUMN confidence FLOAT DEFAULT 1.0"
            })

        # 3. Add 'prediction_source' column
        if 'prediction_source' not in existing_columns:
            migrations_needed.append({
                'name': 'prediction_source',
                'sql': "ALTER TABLE dividends ADD COLUMN prediction_source VARCHAR(50) DEFAULT NULL"
            })

        if not migrations_needed:
            print("\n✅ Database già aggiornato - nessuna migrazione necessaria")
            return

        print(f"\n🔨 Applicazione di {len(migrations_needed)} migrazioni...\n")

        for migration in migrations_needed:
            try:
                print(f"   → Aggiunta colonna '{migration['name']}'...")
                conn.execute(text(migration['sql']))
                conn.commit()
                print(f"   ✅ Colonna '{migration['name']}' aggiunta con successo")
            except Exception as e:
                print(f"   ❌ Errore su '{migration['name']}': {str(e)}")
                conn.rollback()
                raise

        # Update existing records to have default values
        print("\n📝 Aggiornamento record esistenti...")
        conn.execute(text("""
            UPDATE dividends
            SET status = 'CONFIRMED',
                confidence = 1.0,
                prediction_source = 'HISTORICAL'
            WHERE status IS NULL OR status = ''
        """))
        conn.commit()
        print("   ✅ Record esistenti aggiornati")

        # Verify migration
        print("\n🔍 Verifica migrazione...")
        result = conn.execute(text("PRAGMA table_info(dividends)")).fetchall()
        new_columns = [row[1] for row in result]

        print(f"\n📋 Colonne dopo migrazione:")
        for col in new_columns:
            print(f"   - {col}")

        # Show sample data
        print("\n📊 Campione dati migrati:")
        sample = conn.execute(text("""
            SELECT id, stock_id, ex_date, amount, status, confidence, prediction_source
            FROM dividends
            LIMIT 5
        """)).fetchall()

        for row in sample:
            print(f"   ID={row[0]}, stock_id={row[1]}, ex_date={row[2]}, "
                  f"status={row[4]}, confidence={row[5]}, source={row[6]}")

    print("\n" + "=" * 60)
    print("✅ MIGRAZIONE COMPLETATA CON SUCCESSO")
    print("=" * 60)


if __name__ == '__main__':
    try:
        migrate_database()
    except Exception as e:
        print(f"\n❌ ERRORE DURANTE LA MIGRAZIONE:")
        print(f"   {str(e)}")
        sys.exit(1)
