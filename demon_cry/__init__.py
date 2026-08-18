import logging
from os import environ

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(funcName)s@%(filename)s:%(lineno)d) -> %(message)s",
    filename=environ.get("DEMON_CRY_LOG") or None,
    filemode="a",
)
