# src/models.py
from sqlalchemy.dialects.postgresql import insert
from src.db import repos, get_engine
from datetime import datetime
import sqlalchemy

def upsert_repo(conn, repo):
    """
    Upsert a single repo into Postgres.
    Only updates fields that can change:
      - stars
      - repo_updated_at
      - url
      - metadata (merged with existing)
      - last_crawled_at (always set to now)
    """
    stmt = insert(repos).values(**repo)

    # Update columns on conflict
    update_cols = {
        
        # Update with new values from the insert attempt:
        "stars": stmt.excluded.stars,                    # New star count
        "repo_updated_at": stmt.excluded.repo_updated_at, # New update timestamp
        "url": stmt.excluded.url,                        # New URL
        
        # METADATA BEHAVIOR: Preserves existing, ignores new
        # This uses COALESCE to keep existing metadata if present,
        # or empty object if null. NOTE: This does NOT merge with new metadata.

        "metadata": sqlalchemy.func.coalesce(
            repos.c.metadata,
            sqlalchemy.cast('{}', sqlalchemy.dialects.postgresql.JSONB)
        )  # keeps existing metadata if present
    }
    # Always update last_crawled_at to now
    update_cols["last_crawled_at"] = sqlalchemy.sql.func.now()

    
    # Convert INSERT statement to UPSERT (INSERT ON CONFLICT UPDATE)
    # When repo_id conflict occurs, update the specified columns instead of failing
    upsert = stmt.on_conflict_do_update(
        index_elements=["repo_id"],  # Unique constraint to check for conflicts
        set_=update_cols             # Columns to update when conflict occurs
    )
    
    conn.execute(upsert)


def bulk_upsert(engine, repo_dicts, batch=500):
    """
    Upsert multiple repos in a single transaction.
    Currently iterates per repo; can be optimized with bulk insert.
    """
    with engine.begin() as conn:
        for r in repo_dicts:
            upsert_repo(conn, r)
