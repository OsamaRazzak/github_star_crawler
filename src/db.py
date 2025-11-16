# src/db.py
from sqlalchemy import create_engine, Table, Column, MetaData
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import String, Integer, TIMESTAMP
from sqlalchemy.engine import Engine
import os
from dotenv import load_dotenv

load_dotenv()
# Get database URL from environment, fallback to local default
DATABASE_URL = os.getenv("DATABASE_URL")
print('============DATABASE_URL============')
print(DATABASE_URL)

# Metadata object for SQLAlchemy Table definitions
metadata = MetaData()

# Repos table definition
repos = Table(
    "repos",
    metadata,
    Column("repo_id", String, primary_key=True),           # GitHub node ID (stable)
    Column("full_name", String, nullable=False, unique=True), # owner/name
    Column("owner", String, nullable=False),
    Column("name", String, nullable=False),
    Column("url", String),
    Column("stars", Integer, nullable=False),
    Column("created_at", TIMESTAMP(timezone=True)),
    Column("repo_updated_at", TIMESTAMP(timezone=True)),
    Column("last_crawled_at", TIMESTAMP(timezone=True)),
    Column("metadata", JSONB, default={}),                # Flexible JSONB metadata
)

def get_engine() -> Engine:
    """
    Returns a SQLAlchemy Engine for Postgres.
    
    Pooling:
        pool_size=5        # max persistent connections
        max_overflow=10    # extra connections if pool exhausted
    """
    return create_engine(DATABASE_URL, pool_size=5, max_overflow=10)



# metadata object: central place to hold all table definitions — needed for migrations and table creation.
# JSONB metadata allows flexible storage of evolving repo info without schema migration.
