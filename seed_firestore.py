import datetime
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-01-549c7ea1926b"

def seed_database():
    db = firestore.Client(project=PROJECT_ID)
    print(f"Connecting to Firestore database for project: {PROJECT_ID}")

    # Seed Portfolio Holdings
    holdings_ref = db.collection("holdings")
    initial_holdings = [
        {
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "shares": 15.0,
            "avg_price": 182.50,
            "asset_class": "Equities"
        },
        {
            "ticker": "GOOGL",
            "name": "Alphabet Inc.",
            "shares": 25.0,
            "avg_price": 155.00,
            "asset_class": "Equities"
        },
        {
            "ticker": "NVDA",
            "name": "NVIDIA Corporation",
            "shares": 10.0,
            "avg_price": 118.20,
            "asset_class": "Equities"
        },
        {
            "ticker": "VTI",
            "name": "Vanguard Total Stock Market ETF",
            "shares": 40.0,
            "avg_price": 240.00,
            "asset_class": "ETF"
        }
    ]

    for holding in initial_holdings:
        doc_id = holding["ticker"]
        holdings_ref.document(doc_id).set(holding)
        print(f"Seeded holding: {doc_id}")

    # Seed Transactions
    transactions_ref = db.collection("transactions")
    initial_transactions = [
        {
            "amount": 250.00,
            "category": "Groceries",
            "description": "Weekly supermarket shopping",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        },
        {
            "amount": 120.00,
            "category": "Utilities",
            "description": "Electric bill payment",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        },
        {
            "amount": 1500.00,
            "category": "Investment",
            "description": "Monthly portfolio contribution",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
    ]

    for tx in initial_transactions:
        doc_ref = transactions_ref.add(tx)
        print(f"Seeded transaction: {doc_ref[1].id}")

    print("Firestore database seeded successfully!")

if __name__ == "__main__":
    seed_database()
