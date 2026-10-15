import logging
import sys


logger = logging.getLogger("industrial_automation")
logger.setLevel(logging.DEBUG)

logger.handlers = []

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
