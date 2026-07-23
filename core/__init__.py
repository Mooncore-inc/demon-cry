import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(funcName)s@%(filename)s:%(lineno)d) -> %(message)s",
    filename="demon-cry.log",
    filemode="a",
)
