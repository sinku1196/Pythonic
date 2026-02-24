"""
.. module:: browser_manager
   :platform: Python
   :synopsis: A utility module to manage Playwright browser instances with context and page management.

:Date: 2025-12-29
:Author(s): Sinku

Module `browser_manager` provides the `BrowserManager` class for launching, managing, and closing
browser instances using Playwright in a synchronous context. It supports Chromium, Firefox, and WebKit
browsers with configurable headless mode and timeouts.

"""

import logging
from playwright.sync_api import sync_playwright, Error as PlaywrightError


class BrowserManager:
    """
    Manages browser lifecycle and provides a convenient interface to interact with Playwright browser instances.

    :Example:

    .. code-block:: python

        from browser_manager import BrowserManager

        manager = BrowserManager(browser_name="chromium", headless=False)
        try:
            page = manager.launch()
            page.goto("https://example.com")
            print(page.title())
        finally:
            manager.close()
    """

    def __init__(
        self,
        browser_name: str = "chromium",
        headless: bool = True,
        timeout: int = 30000,
    ):
        """
        Initializes a new instance of the BrowserManager.

        :param browser_name: Name of the browser to launch ('chromium', 'firefox', 'webkit').
        :type browser_name: str
        :param headless: Whether to launch the browser in headless mode.
        :type headless: bool
        :param timeout: Default timeout in milliseconds for page operations.
        :type timeout: int
        :return: None
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.browser_name = browser_name.lower()
        self.headless = headless
        self.timeout = timeout
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def launch(self):
        """
        Launches the specified browser and creates a new page in a browser context.

        :returns: A Playwright `Page` object for interacting with the browser page.
        :rtype: playwright.sync_api._generated.Page
        :raises ValueError: If an invalid browser name is provided.
        :raises playwright.sync_api.Error: If Playwright encounters an error during launch.
        :raises Exception: For any unexpected errors during browser startup.

        :Example:

        .. code-block:: python

            manager = BrowserManager(browser_name="firefox")
            try:
                page = manager.launch()
                page.goto("https://example.com")
                print(page.title())
            finally:
                manager.close()
        """
        self.logger.info(
            "Attempting to launch browser: %s (headless=%s)",
            self.browser_name,
            self.headless,
        )
        try:
            self.playwright = sync_playwright().start()
            if self.browser_name == "chromium":
                self.browser = self.playwright.chromium.launch(headless=self.headless)
            elif self.browser_name == "firefox":
                self.browser = self.playwright.firefox.launch(headless=self.headless)
            elif self.browser_name == "webkit":
                self.browser = self.playwright.webkit.launch(headless=self.headless)
            else:
                raise ValueError(f"Invalid browser name '{self.browser_name}'. Choose 'chromium', 'firefox', or 'webkit'.")

            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            self.page.set_default_timeout(self.timeout)
            self.logger.info("Browser launched successfully with timeout = %dms", self.timeout)
            return self.page

        except ValueError as ve:
            self.logger.error("Invalid browser configuration: %s", ve, exc_info=True)
            self.close()
            raise
        except PlaywrightError as pe:
            self.logger.error(
                "Playwright encountered an error during browser launch: %s",
                pe,
                exc_info=True,
            )
            self.close()
            raise
        except Exception as e:
            self.logger.exception("Unexpected error while launching browser: %s", e)
            self.close()
            raise

    def close(self):
        """
        Closes the browser, context, and stops Playwright, releasing all resources. Safe to call even if
        launch() failed or was never called.

        :returns: None
        :rtype: None
        :raises playwright.sync_api.Error: If Playwright encounters an error during cleanup (logged internally).
        :raises Exception: For any unexpected cleanup errors (logged internally).

        :Example:

        .. code-block:: python

            manager = BrowserManager()
            manager.close()  # safely closes any resources if open
        """
        self.logger.info("Closing browser and cleaning up Playwright resources...")
        try:
            if self.context:
                self.context.close()
                self.logger.debug("Browser context closed successfully.")
            if self.browser:
                self.browser.close()
                self.logger.debug("Browser instance closed successfully.")
            if self.playwright:
                self.playwright.stop()
                self.logger.debug("Playwright stopped successfully.")
            self.logger.info("All Playwright resources cleaned up.")
        except PlaywrightError as pe:
            self.logger.warning("Playwright error during cleanup: %s", pe, exc_info=True)
        except Exception as e:
            self.logger.exception("Unexpected error during cleanup: %s", e)
        finally:
            self.context = None
            self.browser = None
            self.playwright = None
            self.page = None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
    logger = logging.getLogger("BrowserManagerExample")
    manager = BrowserManager(browser_name="chromium", headless=False)
    try:
        page = manager.launch()
        page.goto("https://example.com")
        logger.info("Page title: %s", page.title())
    finally:
        manager.close()
