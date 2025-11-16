# src/crawl_stars.py
import os
import time
from datetime import datetime, timedelta
import pandas as pd

from src.github_client import GithubGraphQLClient
from src.db import get_engine
from src.models import bulk_upsert
from src.logger import get_logger


# Initialize logger
logger = get_logger(__name__)
# Initialize GitHub client
client = GithubGraphQLClient()


def repo_node_to_dict(node):
    """
    Convert GitHub API node to DB-ready dict.
    """
    return {
        "repo_id": node["id"],
        "full_name": f"{node['owner']['login']}/{node['name']}",
        "owner": node["owner"]["login"],
        "name": node["name"],
        "url": node.get("url"),
        "stars": node.get("stargazerCount", 0),
        "created_at": node.get("createdAt"),
        "repo_updated_at": node.get("updatedAt"),
        "metadata": {}
    }


def generate_date_partitions(start_date, end_date, step_days=7):
    """
    Yield (from,to) date ranges to avoid GitHub search 1000-result limit.
    """
    cur = start_date
    while cur < end_date:
        nxt = min(end_date, cur + timedelta(days=step_days))
        yield cur.date().isoformat(), nxt.date().isoformat()
        cur = nxt


def search_and_store(query_string, max_repos, engine):
    """
    Search GitHub repos with a query string and store results in Postgres.
    Handles pagination, rate-limit sleeping, and batch upserts.
    """
    collected = 0
    after = None
    results = []

    while True:
        data = client.search_repos_page(query_string, first=100, after=after)
        rl = data.get("data", {}).get("rateLimit", {})
        search = data["data"]["search"]
        nodes = search["nodes"]

        for n in nodes:
            results.append(repo_node_to_dict(n))
            collected += 1
            if collected >= max_repos:
                break

        # Store in DB in batches
        if len(results) >= 200:
            logger.info("Upsert 200 record in Database")
            bulk_upsert(engine, results)
            results = []

        page_info = search["pageInfo"]
        if collected >= max_repos or not page_info["hasNextPage"]:
            break

        after = page_info["endCursor"]
        logger.info(f"Collected {collected}, continuing to next page...{after}")
        

        # Rate-limit check
        remaining = rl.get("remaining")
        logger.info(f"Remaining GraphQL limit: {remaining}")
        resetAt = rl.get("resetAt")
        logger.info(f"Reset-Time : {resetAt}")
        if remaining is not None and remaining < 100:
            if resetAt:
                reset_ts = datetime.fromisoformat(resetAt.replace("Z", "+00:00"))
                pkt_offset = timedelta(hours=5)
                logger.info("reset time is ",reset_ts + pkt_offset)
                delta = (reset_ts - datetime.utcnow()).total_seconds()
                if delta > 0:
                    logger.info(f"Approaching rate limit. Sleeping {int(delta)+5}s until resetAt {resetAt}")
                    time.sleep(int(delta) + 5)

    # Final flush
    if results:
        bulk_upsert(engine, results)

    return collected

