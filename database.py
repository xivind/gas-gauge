import os
from peewee import SqliteDatabase
from dotenv import load_dotenv

load_dotenv()

DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/gas_gauge.db")

# Ensure data directory exists
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

db = SqliteDatabase(DATABASE_PATH)

def init_db():
    """Initialize database tables"""
    from models import CanisterType, Canister, Weighing
    db.connect()
    db.create_tables([CanisterType, Canister, Weighing], safe=True)
    db.close()
