import logging

from utils.auth.otp import TOTPProvider
from utils.auth.credentials import Credentials
from utils.automation.experity.experity_base import ExperityBase
from utils.automation.core.browser_manager import BrowserManager


class ExperityReports:
    def __init__(
        self,
        browser_manager_cls: type[BrowserManager],
        experity_base_cls: type[ExperityBase],
        download_dir: str = "downloads",
        screenshot_dir: str = "screenshots",
        headless: bool = False,
        debug: bool = True,
        timeout: int = 300_000,
    ):
        self.debug = debug
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        self.manager = browser_manager_cls(headless=headless, timeout=timeout)
        self.page = self.manager.launch()
        self.experity = experity_base_cls(page=self.page)

        self.download_dir = download_dir
        self.screenshot_dir = screenshot_dir

    def login(self, credentails: Credentials, totp_cls: type[TOTPProvider]):
        try:
            user_cred = credentails
            self.experity.open_portal(download_dir=self.download_dir, screenshot_dir=self.screenshot_dir)
            self.experity.user_login(user_cred.username, user_cred.password)
            if user_cred.auth_passphrase:
                totp = totp_cls(user_cred.auth_passphrase)
                self.experity.enter_otp(totp.generate_otp())
        except Exception as e:
            self.logger.error("Unable to login: %s", e)

    def logout(self):
        try:
            self.experity.user_logout()
        except Exception as e:
            self.logger.error("Unable to logout: %s", e)

    def close_browser(self):
        try:
            self.manager.close()
        except Exception as e:
            self.logger.error("Unable to close browser: %s", e)

    def collect_exception(self):
        try:
            self.experity.collect_exception_artifacts()
        except Exception as e:
            self.logger.error("Unable to collect exception artifacts from experity: %s", e)

    def clinic_data(self, file_name: str = "ClinicData.html"):
        try:
            self.experity.navigate_page("clinic")
            self.experity.clinic_data(file_name)
        except Exception as e:
            self.logger.error("Unable to download clinic report: %s", e)
            raise

    def report_data(self, file_name: str = "ClinicReport.html"):
        try:
            self.experity.navigate_page("report")
            self.experity.report_data(file_name)
        except Exception as e:
            self.logger.error("Unable to download report data: %s", e)
            raise

    def date_range_report(self, report_name: str, report_title: str, from_date: str, to_date: str):
        try:
            file_name = report_name + "_" + from_date + "_" + to_date
            file_name = file_name.replace(" ", "_").replace("/", "_")
            self.experity.navigate_page("report")
            self.experity.search_report(report_name)
            self.experity.select_report(report_title)
            self.experity.select_dates(from_date, to_date)
            page = self.experity.run_report()
            self.experity.download_report(page, file_name)
            self.experity.download_report(page, file_name, report_format="xlsx")
            page.close()
        except Exception as e:
            self.logger.error("Unable to download %s report: %s", report_name, e)
            raise

    def month_report(self, report_name: str, report_title: str, month_year: list[str]):
        try:
            self.experity.navigate_page("report")
            self.experity.search_report(report_name)
            self.experity.select_report(report_title)
            for month in month_year:
                try:
                    file_name = report_name + "_" + month
                    file_name = file_name.replace(" ", "_")
                    self.experity.select_month(month)
                    page = self.experity.run_report()
                    self.experity.download_report(page, file_name)
                    self.experity.download_report(page, file_name, report_format="xlsx")
                    page.close()
                except Exception as e:
                    self.logger.error("Unable to download %s report for %s month.\nError: \n%s", report_name, month, e)
                    continue
        except Exception as e:
            self.logger.error("Unable to download %s report: %s", report_name, e)
            raise

    def month_range_report(self, report_name: str, report_title: str, from_month_year: str, to_month_year: str):
        try:
            file_name = report_name + "_" + from_month_year + "_" + to_month_year
            file_name = file_name.replace(" ", "_")
            self.experity.navigate_page("report")
            self.experity.search_report(report_name)
            self.experity.select_report(report_title)
            self.experity.select_months(from_month_year, to_month_year)
            page = self.experity.run_report()
            self.experity.download_report(page, file_name)
            self.experity.download_report(page, file_name, report_format="xlsx")
            page.close()
        except Exception as e:
            self.logger.error("Unable to download %s report: %s", report_name, e)
            raise

    def month_range_report_monthly(self, report_name: str, report_title: str, months: list[str]):
        try:
            for month in months:
                try:
                    self.month_range_report(report_name, report_title, month, month)
                except Exception as e:
                    self.logger.error("Unable to download %s report for %s month.\nError: \n%s", report_name, month, e)
                    continue
        except Exception as e:
            self.logger.error("Unable to download %s report: %s", report_name, e)
            raise


if __name__ == "__main__":
    import logging
    from utils.automation.core.browser_manager import BrowserManager
    from utils.automation.experity.experity_base import ExperityBase
    from utils.auth.otp import TOTPProvider
    from utils.auth.credentials import Credentials

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")

    credentials = Credentials("16", "username", "password", "authkey")
    logger = logging.getLogger("Automation Demo")
    automation = ExperityReports(BrowserManager, ExperityBase)
    try:
        automation.login(credentials, TOTPProvider)
        automation.clinic_data()
        automation.month_report("CNT 4", "Practice, CNT 4", ["August 2024"])
        automation.month_range_report("CNT 9 DW", "Practice, CNT 9 DW", "January 2025", "December 2025")
        automation.date_range_report("CNT 17", "Practice, CNT 17", "1/1/2026", "1/16/2026")
    except Exception as e:
        automation.collect_exception()
        logger.error("Exception during automation: %s", e)
    finally:
        automation.logout()
        automation.close_browser()
