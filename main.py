from src.crawl_stars import generate_date_partitions, search_and_store
from src.db import get_engine
import os
from datetime import timedelta, datetime
import pandas as pd
from dotenv import load_dotenv
from src.db import metadata, get_engine
from src.logger import get_logger

# Initialize logger
logger = get_logger(__name__)
engine = get_engine()
metadata.create_all(engine)


load_dotenv(override=True)

def main():
    engine = get_engine()
    target_total = int(os.getenv("TARGET_TOTAL"))
    start = datetime(2008, 1, 1)
    end = datetime.utcnow()
    step_days = int(os.getenv("STEP_DAYS"))

    total_collected = 0

    for frm, to in generate_date_partitions(start, end, step_days):
        if total_collected >= target_total:
            break

        q = f"created:{frm}..{to} stars:>0"
        remaining_needed = target_total - total_collected
        try:
            logger.info(f"Searching range {frm}..{to} need {remaining_needed} repos")
            got = search_and_store(q, remaining_needed, engine)
            total_collected += got
            logger.info(f"Got {got} from {frm}..{to} (total {total_collected})")
        except Exception as e:
            logger.info("Error searching range:", e)
            continue

    logger.info(f"Finished. Collected {total_collected}")

    # Export CSV artifact
    with engine.connect() as conn:
        df = pd.read_sql(
            "SELECT repo_id, full_name, owner, name, stars, url, created_at, repo_updated_at, last_crawled_at FROM repos",
            conn
        )
        out = "export/repos_dump.csv"
        df.to_csv(out, index=False)
        logger.info("Exported to", out)


if __name__ == "__main__":
    main()
