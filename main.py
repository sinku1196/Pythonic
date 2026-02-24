import logging

from utils.auth.otp import TOTPProvider
from utils.auth.credentials import Credentials
from utils.automation.core.browser_manager import BrowserManager
from utils.automation.experity.experity_base import ExperityBase
from utils.automation.experity.experity_reports import ExperityReports
from config.directory import download_directory, screenshot_directory

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")

logger = logging.getLogger("Automation Demo")

credentials = Credentials("16", "sjalan@zny01", "Graphxsys@1147", "FH2MMUESLNQUHIH2")
download_dir = download_directory(credentials.client_id)
screenshot_dir = screenshot_directory(credentials.client_id)
automation = ExperityReports(BrowserManager, ExperityBase, download_dir, screenshot_dir, headless=True)


try:
    automation.login(credentials, TOTPProvider)
    automation.clinic_data()
except Exception as e:
    automation.collect_exception()
    logger.error("Exception during automation: %s", e)
finally:
    automation.logout()
    automation.close_browser()
