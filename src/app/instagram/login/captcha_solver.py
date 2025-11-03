import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from app.core.config import get_cfg
from app.core.logger import get_logger


class CaptchaSolver:
    """Handles captcha solving using 2Captcha extension"""

    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        cfg = get_cfg()
        self.captcha_api_key = cfg["captcha"]["apiKey"]
        self.logger = get_logger()

    def handle_captcha_step(self) -> bool:
        """
        Handle captcha verification step

        Returns:
            True if captcha solved successfully, False otherwise
        """
        try:
            self.logger.info("Handling captcha step...")

            page_source = self.driver.page_source.lower()
            current_url = self.driver.current_url.lower()

            # Check if we're already on a captcha page
            already_on_captcha = self._is_on_captcha_page()
            self.logger.info(f"Already on captcha page: {already_on_captcha}")

            if not already_on_captcha:
                # Need to click Continue button first
                if not self._click_continue_button():
                    return False

            # Setup 2Captcha extension
            self.logger.info("Setting up 2Captcha extension with auto-solve...")
            if not self._setup_2captcha_extension():
                self.logger.error("Failed to setup 2Captcha extension")
                return False

            # Wait for automatic solving
            self.logger.info("Waiting for automatic captcha solving...")
            start_url = self.driver.current_url

            # Wait up to 2 minutes for automatic solving
            for i in range(120):
                time.sleep(1)
                current_url = self.driver.current_url
                page_source = self.driver.page_source.lower()

                # Check if page changed (captcha solved)
                if self._is_captcha_solved(start_url, current_url, page_source):
                    self.logger.info("Captcha solved automatically! Page changed.")
                    return True

                if (i + 1) % 10 == 0:
                    self.logger.info(f"Still waiting for automatic solving... ({i + 1}/120 seconds)")

                # Check every 30 seconds if captcha is still present
                if (i + 1) % 30 == 0:
                    if "i'm not a robot" in self.driver.page_source.lower():
                        self.logger.info("Captcha still present, continuing to wait...")
                    else:
                        self.logger.info("Captcha seems to have disappeared, checking for progress...")

            self.logger.error("Timeout waiting for automatic captcha solution")
            return False

        except Exception as e:
            self.logger.error(f"Error handling captcha step: {e}")
            return False

    def _is_on_captcha_page(self) -> bool:
        """Check if we're already on a captcha page"""
        try:
            page_source = self.driver.page_source.lower()

            captcha_indicators = [
                "i'm not a robot" in page_source,
                "solve with 2captcha" in page_source,
                len(self.driver.find_elements(By.CSS_SELECTOR, ".g-recaptcha")) > 0,
                len(self.driver.find_elements(By.XPATH, "//iframe[contains(@src, 'recaptcha')]")) > 0,
            ]

            return any(captcha_indicators)

        except Exception as e:
            self.logger.error(f"Error checking if on captcha page: {e}")
            return False

    def _click_continue_button(self) -> bool:
        """Click the Continue button to reach captcha"""
        try:
            self.logger.info("Looking for Continue button...")

            continue_selectors = [
                "//div[@role='button' and @aria-label='Continue']",
                "//div[@role='button' and contains(@class, 'wbloks_1') and @aria-label='Continue']",
                "//div[@role='button' and contains(text(), 'Continue')]",
                "//button[contains(text(), 'Continue')]",
                "//div[@role='button']//span[text()='Continue']/ancestor::div[@role='button']",
            ]

            for selector in continue_selectors:
                try:
                    continue_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    self.logger.info(f"Found Continue button")

                    try:
                        continue_button.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", continue_button)

                    self.logger.info("Successfully clicked Continue button")
                    time.sleep(5)
                    return True

                except TimeoutException:
                    continue

            self.logger.error("Could not find Continue button")
            return False

        except Exception as e:
            self.logger.error(f"Error clicking continue button: {e}")
            return False

    def _setup_2captcha_extension(self) -> bool:
        """Setup 2Captcha browser extension"""
        try:
            # Open extension options page
            extension_url = "chrome-extension://ifibfemgeogfhoebkmokieepdoobkbpo/options/options.html"

            # Store current URL to return later
            original_url = self.driver.current_url

            try:
                self.driver.execute_script(f"window.open('{extension_url}', '_blank');")
                time.sleep(2)

                # Switch to extension tab
                windows = self.driver.window_handles
                if len(windows) > 1:
                    self.driver.switch_to.window(windows[-1])
                    time.sleep(2)

                    # Enter API key
                    try:
                        api_key_input = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.ID, "apiKey"))
                        )
                        api_key_input.clear()
                        api_key_input.send_keys(self.captcha_api_key)
                        self.logger.info("Entered 2Captcha API key")
                    except:
                        self.logger.warning("Could not find API key input field")

                    # Enable auto-submit
                    try:
                        auto_submit_checkbox = self.driver.find_element(By.ID, "autoSubmitForms")
                        if not auto_submit_checkbox.is_selected():
                            auto_submit_checkbox.click()
                        self.logger.info("Enabled auto-submit")
                    except:
                        self.logger.warning("Could not find auto-submit checkbox")

                    # Click save/connect button
                    try:
                        save_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button")
                        for button in save_buttons:
                            if "connect" in button.text.lower() or "save" in button.text.lower():
                                button.click()
                                self.logger.info("Clicked save button")
                                break
                    except:
                        self.logger.warning("Could not find save button")

                    time.sleep(2)

                    # Close extension tab and return to original
                    self.driver.close()
                    self.driver.switch_to.window(windows[0])
                    time.sleep(1)

                    return True

            except Exception as e:
                self.logger.error(f"Error setting up extension: {e}")
                # Try to return to original window
                try:
                    windows = self.driver.window_handles
                    if len(windows) > 0:
                        self.driver.switch_to.window(windows[0])
                except:
                    pass
                return False

        except Exception as e:
            self.logger.error(f"Error in setup_2captcha_extension: {e}")
            return False

    def _is_captcha_solved(self, start_url: str, current_url: str, page_source: str) -> bool:
        """Check if captcha has been solved"""
        captcha_solved_indicators = [
            current_url != start_url,
            "suspended" not in current_url,
            "enter your mobile number" in page_source,
            "mobile number" in page_source,
            "upload a verification selfie" in page_source,
            "upload a photo" in page_source,
        ]

        return any(captcha_solved_indicators)
