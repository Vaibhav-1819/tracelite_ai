"""
TraceLite AI - Demo Application
A deliberately broken sample billing calculation service that produces a ZeroDivisionError.
Run this script to observe the crash or pipe output to a log file:
    python demo_app.py > fixtures/live_run.log 2>&1
"""

import sys
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("billing_service")


def calculate_average_discount(invoices, total_units):
    """Calculates effective discount ratio per unit sold."""
    logger.debug(f"Calculating discount for {len(invoices)} invoices across {total_units} units")
    total_discount_amount = sum(inv.get("discount", 0.0) for inv in invoices)
    
    # Deliberate bug: no guard against total_units == 0
    discount_ratio = total_discount_amount / total_units
    return discount_ratio


def process_batch(batch_id: int):
    logger.info(f"Starting billing calculation service for batch_id={batch_id}...")
    
    # Mock invoices with zero physical units sold (e.g., pure service credit adjustments)
    invoices = [
        {"id": 101, "units": 0, "discount": 25.0},
        {"id": 102, "units": 0, "discount": 50.0},
    ]
    
    total_units = sum(inv["units"] for inv in invoices)
    logger.info(f"Loaded {len(invoices)} invoices for Acme Corp (total_units={total_units})")
    
    # Simulated sensitive token that TraceLite will automatically redact
    logger.debug("Acquired authorization context auth_token=sk-9f82a7b3c4d5e6f1a2b3c4d5e6f7a8b9")
    
    try:
        avg_rate = calculate_average_discount(invoices, total_units)
        logger.info(f"Batch {batch_id} completed successfully with average rate {avg_rate}")
    except Exception as exc:
        logger.error("Unexpected crash during invoice discount calculation!", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        process_batch(74829)
    except Exception:
        logger.critical("Worker encountered fatal unhandled exception. Terminating transaction.")
        sys.exit(1)
