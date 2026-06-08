import logging
import sys


def setup_logging() -> None:
    """
    Configure application-wide logging.

    This should be called once during application startup,
    before importing modules that emit logs.
    """

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
        force=True,  # Reconfigure existing handlers
    )

    # Optional: reduce noisy third-party logs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)