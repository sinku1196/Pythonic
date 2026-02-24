import logging

from utils.auth.otp import TOTPProvider
from utils.auth.credentials import Credentials
from utils.report_dates import get_months_between
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

FROM_DATE = "05/01/2022"
TO_DATE = "02/24/2026"

months = get_months_between(FROM_DATE, TO_DATE)

try:
    automation.login(credentials, TOTPProvider)
    automation.clinic_data()
    automation.report_data()
    automation.month_range_report("PAY 28", "Expected AR, PAY 28", months[0], months[-2])
    automation.month_report("PAY 29", "Expected AR, PAY 29", months[:-2])
    automation.date_range_report("PAY 30", "Expected AR, PAY 30", FROM_DATE, TO_DATE)
    automation.date_range_report("PHY 9", "Expected AR, PHY 9", FROM_DATE, TO_DATE)
    automation.month_report("PHY 10", "Expected AR, PHY 10", months[-2])
except Exception as e:
    automation.collect_exception()
    logger.error("Exception during automation: %s", e)
finally:
    automation.logout()
    automation.close_browser()
"""
("PAY 28", "Expected AR, PAY 28", "January 2022", "January 2026")
("PAY 29", "Expected AR, PAY 29", ["January 2022"])
("PAY 30", "Expected AR, PAY 30", FROM_DATE, TO_DATE)
("PHY 9", "Expected AR, PHY 9", FROM_DATE, TO_DATE)
("PHY 10", "Expected AR, PHY 10", "January 2022")
"""
