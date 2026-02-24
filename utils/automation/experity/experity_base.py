"""
experity_base
=============

Base automation utilities for interacting with the Experity / Practice Velocity
web portal using Playwright.

This module provides a reusable, class-based abstraction for:
- Authenticating users (including MFA/OTP flows)
- Navigating portal pages
- Locating and managing report frames
- Running reports and downloading CSV exports
- Capturing diagnostic artifacts on failure

It is intended to be used as a foundational component for higher-level
reporting and data extraction workflows.

:Date: 2025-12-29
:Author(s): Sinku Kumar
"""

import os
import logging
import datetime
from typing import Optional, Literal
from playwright.sync_api import Page, Frame


class ExperityBase:
    """
    Base class encapsulating Experity portal automation behaviors.

    This class manages authentication, navigation, frame resolution,
    report execution, downloads, and exception artifact collection using
    Playwright's synchronous API.

    Instances of this class are stateful and tied to a single browser page
    and client context.
    """

    def __init__(self, page: Page) -> None:
        """
        Initialize the ExperityBase automation context.

        This constructor configures directory paths, logging, timestamps,
        and core Playwright objects required for portal interaction.

        :param page: Active Playwright page instance.
        :type page: playwright.sync_api.Page
        """
        self.page = page
        self.base_url = None
        self.download_dir = None
        self.screenshot_dir = None
        self.main_frame: Optional[Frame] = None
        self.nav_frame: Optional[Frame] = None
        self.report_frame: Optional[Frame] = None
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.current_page = None
        self.current_report_search = None
        self.current_report_select = None

    def _time_stamp(self) -> str:
        """
        Generate a high-resolution timestamp string.

        Used primarily for naming screenshots and diagnostic artifacts.

        :return: Timestamp formatted as ``HH_MM_SS_microseconds``.
        :rtype: str
        """
        return datetime.datetime.now().strftime("%H_%M_%S_%f")

    def open_portal(self, url: str = "https://pvpm.practicevelocity.com/", download_dir: str = "downloads", screenshot_dir: str = "screenshots") -> None:
        """
        Open the Experity portal landing page.

        On success, the base portal URL is extracted and stored for
        subsequent navigation.

        :param url: Portal login URL.
        :type url: str
        :raises Exception: If navigation fails.
        """
        try:
            self.download_dir = download_dir
            self.screenshot_dir = screenshot_dir
            os.makedirs(self.download_dir, exist_ok=True)
            os.makedirs(self.screenshot_dir, exist_ok=True)
            self.logger.info("Download directory: %s", self.download_dir)
            self.logger.info("Screenshot directory: %s", self.screenshot_dir)
            self.page.goto(url)
            self.base_url = (self.page.url).split("loginpage.aspx")[0]
            self.logger.info("Portal opened: %s", self.base_url)
        except Exception as e:
            self.logger.error("Unable to open portal: %s", e)
            raise

    def user_login(self, username: str, password: str) -> None:
        """
        Perform user authentication against the portal.

        Supports both standard login and Okta-based MFA workflows.
        If MFA is detected, the method returns ``False`` to signal
        that OTP input is required.

        :param username: Portal username.
        :type username: str
        :param password: Portal password.
        :type password: str
        :rtype: bool
        :raises Exception: If authentication fails or credentials are invalid.
        """
        try:
            self.page.wait_for_selector("#txtLogin")
            self.page.type("#txtLogin", username, delay=100)
            self.logger.info("Entered username: %s", username)
            self.page.click("#btnNext")
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_load_state("domcontentloaded")

            if self.page.url == "https://experityhealth-external.okta.com/":
                self.page.type("#okta-signin-password", password, delay=100)
                self.logger.info("Entered password: %s", "•" * len(username))
                self.page.click("#okta-signin-submit")
                return

            self.page.wait_for_selector("#txtPassword")
            self.page.fill("#txtPassword", password)
            self.page.click("#btnSubmit")
            self.page.wait_for_load_state("domcontentloaded")
            title = self.page.title()
            if title == "PVM > Login":
                raise Exception("Check user credentails.")
            self._verify_login()
            return
        except Exception as e:
            logging.error("Login exception: %s", e)
            raise

    def enter_otp(self, otp: str) -> None:
        """
        Submit a one-time password for MFA authentication.

        This method should be called only when ``user_login`` indicates
        that MFA is required.

        :param otp: One-time password value.
        :type otp: str
        :raises Exception: If OTP submission or verification fails.
        """
        try:
            self.logger.info("Entering 2FA OTP")
            self.page.type("#input71", otp, delay=100)
            self.page.press("#input71", "Enter")
            self.logger.info("OTP entered: %s", "•" * len(otp))
            self._verify_login()
        except Exception as e:
            self.logger.error("Login exception: %s", e)
            raise

    def _verify_login(self):
        """
        Verify successful authentication by validating the landing URL.

        :raises Exception: If the expected post-login URL is not reached.
        """
        expected_url = f"{self.base_url}LogBook.aspx"
        self.page.wait_for_url(expected_url)
        # Final safety check
        if self.page.url != expected_url:
            raise Exception(f"Unable to verify user login. Expected title {expected_url}, got {self.page.url}")

        self.logger.info("Login verified successfully")

    def user_logout(self) -> None:
        """
        Log the user out of the Experity portal.

        :raises Exception: If logout fails or the logout element is unavailable.
        """
        try:
            logout_btn = self.page.locator("#tdMenuBarItemlogout")
            logout_btn.wait_for(state="visible")
            logout_btn.click()
            self.page.wait_for_load_state("load")
            self.logger.info("Logout successful.")
        except Exception as e:
            self.logger.error("Unable to logout: %s", e)
            raise

    def navigate_page(self, page_name: Literal["report", "clinic"]) -> None:
        """
        Navigate to a supported portal page.

        Supported pages include:
        - ``report``: Report execution and export interface
        - ``clinic``: Clinic information listing

        :param page_name: Target page identifier.
        :type page_name: Literal["report", "clinic"]
        :raises ValueError: If an unsupported page name is supplied.
        :raises Exception: If navigation fails.
        """
        pages = {
            "report": "Reports.aspx",
            "clinic": "ClinicInfo.aspx",
        }

        try:
            target = pages[page_name]
            if self.current_page == target:
                return
            self.page.goto(f"{self.base_url}{target}")
            self.page.wait_for_load_state("networkidle")
            self.logger.info("Navigated to %s", self.page.url)
            self.current_page = target
            if page_name == "report":
                self._get_frames()
        except KeyError:
            self.logger.error("Unknown page name: %s", page_name)
            raise ValueError(f"Unsupported page name: {page_name}") from None
        except Exception as e:
            self.logger.error("Unable to navigate page: %s", e)
            raise

    def _get_frames(self) -> None:
        """
        Resolve and cache report-related frames.

        Identifies and stores references to the main, navigation,
        and report content frames used throughout report workflows.

        :raises ValueError: If required frames cannot be located.
        :raises Exception: For general frame resolution failures.
        """
        try:
            self.main_frame = self.page.frame(name="reportMainWindow")
            if not self.main_frame:
                raise ValueError("Main frame 'reportMainWindow' not found")

            self.nav_frame = self.page.frame(name="NavFrame")
            self.report_frame = self.page.frame(name="PVRC_MainStage")

            self.logger.info("Frames assigned: main=%s, nav=%s, report=%s", bool(self.main_frame), bool(self.nav_frame), bool(self.report_frame))

        except Exception as e:
            self.logger.error("Unable to get frames: %s", e)
            raise

    def search_report(self, report_name: str) -> None:
        """
        Search for a report by name within the report navigation frame.

        :param report_name: Name or partial name of the report.
        :type report_name: str
        :raises Exception: If the search operation fails.
        """
        try:
            if self.current_report_search == report_name:
                return
            self.nav_frame.locator("#userSearch").fill(report_name)
            self.nav_frame.locator("#dosearch").click()
            self.logger.info("Searched report: %s", report_name)
            self.current_report_search = report_name
        except Exception as e:
            self.logger.error("Unable to search report: %s", e)
            raise

    def select_report(self, report_title: str) -> None:
        """
        Select a report from the report results list.

        :param report_title: Exact report title text.
        :type report_title: str
        :raises Exception: If the report cannot be selected.
        """
        try:
            if self.current_report_select == report_title:
                return
            self.report_frame.wait_for_load_state("networkidle")
            report_button = self.report_frame.locator("#mainbutton1")
            report_button.locator(f"text={report_title}").wait_for()
            report_button.click()
            self.logger.info("Selected report: %s", report_title)
            self.current_report_select = report_title
        except Exception as e:
            self.logger.error("Unable to select report: %s", e)
            raise

    def select_month(self, month_year: str) -> None:
        """
        Select a single reporting month.

        :param month_year: Month label (e.g., ``"August 2022"``).
        :type month_year: str
        """
        try:
            self.report_frame.select_option("select[name='ClosingDate']", label=month_year)
            self.logger.info("Selected month: %s", month_year)
        except Exception as e:
            self.logger.error("Unable to select month %s: %s", month_year, e)

    def select_months(self, from_month: str, to_month: str) -> None:
        """
        Select a reporting month range.

        :param from_month: Starting month label.
        :type from_month: str
        :param to_month: Ending month label.
        :type to_month: str
        """
        try:
            self.report_frame.select_option("select[name='FromClosingDate']", label=from_month)
            self.logger.info("Selected from month: %s", from_month)
            self.report_frame.select_option("select[name='ToClosingDate']", label=to_month)
            self.logger.info("Selected to month: %s", to_month)
        except Exception as e:
            self.logger.error("Unable to select from month %s or to month %s: %s", from_month, to_month, e)

    def select_dates(self, from_date: str, to_date: str) -> None:
        """
        Select a reporting date range.

        :param from_date: Start date value.
        :type from_date: str
        :param to_date: End date value.
        :type to_date: str
        """
        try:
            self.report_frame.locator("#FromServiceDate").fill(from_date)
            self.logger.info("Selected from date: %s", from_date)
            self.report_frame.locator("#ToServiceDate").fill(to_date)
            self.logger.info("Selected to date: %s", to_date)
        except Exception as e:
            self.logger.error("Unable to select from date %s or to date %s: %s", from_date, to_date, e)

    def select_date(self, date: str) -> None:
        """
        Select a single reporting date.

        :param date: Date value.
        :type date: str
        """
        try:
            self.report_frame.locator("#ServiceDate").fill(date)
            self.logger.info("Selected date: %s", date)
        except Exception as e:
            self.logger.error("Unable to select date %s: %s", date, e)

    def parameter_filter(self, mapping: dict) -> None:
        """
        Apply parameter filters using checkbox mappings.

        The mapping should associate uncheck selectors with
        corresponding select-all selectors.

        :param mapping: Locator mapping for parameter controls.
        :type mapping: dict
        """
        try:
            for uncheck_button, select_all in mapping.items():
                self.report_frame.locator(uncheck_button).click()
                self.report_frame.locator(select_all).click()
            self.logger.info("Parameter filter applied.")
        except Exception as e:
            self.logger.error("Unable to apply parameter filter: %s", e)

    def run_report(self) -> Page:
        """
        Execute the selected report.

        Triggers report execution and captures the popup page
        containing the report output.

        :return: Playwright page instance for the report popup.
        :rtype: playwright.sync_api.Page
        :raises Exception: If report execution fails.
        """
        try:
            with self.page.context.expect_page() as popup_info:
                self.report_frame.locator("input[name='submitbtn']").click()
            popup = popup_info.value
            self.page.bring_to_front()
            self.logger.info("Run report triggered, popup opened and brought to front.")
            return popup
        except Exception as e:
            self.logger.error("Unable to run report: %s", e)
            raise

    def report_status(self, popup: Page, timeout: int = 3000_000) -> dict:
        """
        Evaluate the report execution status.

        Detects report errors, captures screenshots when failures
        occur, and returns a structured status response.

        :param popup: Report popup page.
        :type popup: playwright.sync_api.Page
        :return: Status dictionary containing execution results.
        :rtype: dict
        :raises Exception: If report loading fails unexpectedly.
        """
        try:
            popup.wait_for_load_state("networkidle", timeout=timeout)
            popup.bring_to_front()
            error_locator = popup.locator("#ctl02_ctl00")
            if error_locator.is_visible():
                error_text = error_locator.inner_text()
                raise Exception(f"Error occured during loading report: {error_text}")
            self.logger.debug("Report loaded successfully")
            return {"status": "loaded"}

        except Exception as e:
            self.logger.error("Unable to load report: %s", e)
            raise

    def download_report(self, popup: Page, file_name: str, timeout: int = 1_200_000, report_format: Literal["xml", "csv", "pdf", "mhtml", "xlsx", "tiff", "docx", "txt"] = "csv") -> None:
        """
        Download the report output in specified format.

        :param popup: Report popup page.
        :type popup: playwright.sync_api.Page
        :param file_name: Relative output file name.
        :type file_name: str
        :param report_format: report format in "xml", `csv`, `pdf`, `mhtml`, `xlsx`, `tiff`, `docx`, `txt`
        :type report_format: str
        :raises Exception: If download fails.
        """
        try:
            report_locator_title = {
                "xml": "XML file with report data",
                "csv": "CSV (comma delimited)",
                "pdf": "PDF",
                "mhtml": "MHTML (web archive)",
                "xlsx": "Excel",
                "tiff": "TIFF file",
                "docx": "Word",
                "txt": "TXT (Pipe delimited)",
            }
            status = self.report_status(popup, timeout=timeout)
            if status["status"] == "loaded":
                export_btn = popup.locator("#ReportViewerControl_ctl05_ctl04_ctl00_ButtonLink")
                export_btn.wait_for(state="visible")
                export_btn.click()

                menu = popup.locator("#ReportViewerControl_ctl05_ctl04_ctl00_Menu")
                menu.wait_for(state="visible")

                csv_link = menu.locator(f"a[title='{report_locator_title[report_format]}']")
                csv_link.wait_for(state="visible")

                with popup.expect_download(timeout=1200_000) as download_info:
                    csv_link.click()
                download = download_info.value
                file_name += f".{report_format}"
                download_path = os.path.join(self.download_dir, file_name)
                download.save_as(download_path)

                self.logger.info("CSV report downloaded successfully to %s", download_path)
        except Exception as e:
            self.logger.error("Unable to download report: %s", e)
            raise

    def clinic_data(self, file_name: str = "clinic_data.html") -> None:
        """
        Extract and persist clinic data as an HTML artifact.

        :param file_name: html file name where data will be saved.
        :type file_name: str

        :raises Exception: If clinic data cannot be retrieved.
        """
        try:
            self.page.wait_for_selector("#gvClinicList")
            self.logger.info("Clinic table loaded; returning data.")
            clinic_data = self.page.locator("#gvClinicList").evaluate("el => el.outerHTML")
            clinic_data_path = os.path.join(self.download_dir, file_name)
            with open(clinic_data_path, "w", encoding="utf-8") as f:
                f.write(clinic_data)
        except Exception as e:
            self.logger.error("Unable to get clinic data: %s", e)
            raise

    def report_data(self, file_name: str = "report_data.html") -> None:
        try:
            # Wait until form exists in DOM (not necessarily visible)
            self.nav_frame.wait_for_selector("#form1", state="attached")

            report_data = self.nav_frame.locator("#form1").evaluate("el => el.outerHTML")

            report_data_path = os.path.join(self.download_dir, file_name)
            with open(report_data_path, "w", encoding="utf-8") as f:
                f.write(report_data)

            self.logger.info("Report data captured successfully.")

        except Exception as e:
            self.logger.error("Unable to get report data: %s", e)
            raise

    def collect_exception_artifacts(self, label: str = "Exception") -> None:
        """
        Capture screenshots for all active browser pages.

        This method is intended for diagnostic use during exception handling
        and captures full-page screenshots for each open tab/window.

        :param label: Prefix label for screenshot filenames.
        :type label: str
        """
        ts = self._time_stamp()

        pages = self.page.context.pages
        if not pages:
            self.logger.warning("No pages found in browser context")
            return

        for index, page in enumerate(pages):
            try:
                screenshot_path = os.path.join(self.screenshot_dir, f"{label}_Window_{index}_{ts}.png")

                page.screenshot(path=screenshot_path, full_page=True)

                self.logger.info(
                    "Captured screenshot for window %s: %s",
                    index,
                    screenshot_path,
                )

            except Exception as exc:
                self.logger.exception(
                    "Failed to capture screenshot for window %s: %s",
                    index,
                    exc,
                )


if __name__ == "__main__":
    from utils.automation.core.browser_manager import BrowserManager

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
    logger = logging.getLogger("Experity Base Example")
    manager = BrowserManager(browser_name="chromium", headless=False)
    page = manager.launch()
    experity = ExperityBase(page=page)
    try:
        experity.open_portal()
    except Exception:
        experity.collect_exception_artifacts()
    finally:
        manager.close()
