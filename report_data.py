import os
import logging
from datetime import datetime
from dotenv import load_dotenv

from utils.automation import ExperityAutomation
from parser import automation_parser

load_dotenv()

parser = automation_parser()
args = parser.parse_args()


if args.terminal_output:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
else:
    logs_dir = os.path.join("logs", str(datetime.now().strftime("%Y-%m-%d")))
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, f"automation_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.log")
    logging.basicConfig(filename=log_file, filemode="a", level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")

logger = logging.getLogger("Experity_Automation")

CLIENT_ID = args.client_id

logger.critical("Client ID: %s - START", CLIENT_ID)
automation = ExperityAutomation(headless=args.headless, debug=False, timeout=30_000)
try:
    automation.login(client_id=CLIENT_ID)
    automation.clinic_data()
    automation.report_data()
except Exception as e:
    automation.collect_exception()
    logger.error("Exception during automation: %s", e)
finally:
    automation.logout()
    automation.close_browser()
    logger.critical("Client ID: %s - END", CLIENT_ID)
