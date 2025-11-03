import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from app.core.logger import get_logger


class LoginManager:
    """Handles Instagram login process including 2FA"""

    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.logger = get_logger()

    def handle_login_process(self) -> bool:
        """
        Handle the complete login process including 2FA

        Note: This assumes AdsPower extension fills credentials automatically.
        For manual credential entry, extend this method.

        Returns:
            True if login successful, False otherwise
        """
        try:
            self.logger.info("Starting login process...")

            # Wait for AdsPower extension to fill login details
            self.logger.info("Waiting 7 seconds for AdsPower extension to fill login details...")
            time.sleep(7)

            # Click "Log in" button
            if not self._click_login_button():
                return False

            # Check if 2FA is required
            if self._is_2fa_required():
                self.logger.info("2FA required - handling 2FA process...")
                return self._handle_2fa()
            else:
                self.logger.info("No 2FA required - proceeding...")
                time.sleep(3)

            self.logger.info("Login process completed!")
            return True

        except Exception as e:
            self.logger.error(f"Error during login process: {e}")
            return False

    def _click_login_button(self) -> bool:
        """Find and click the login button"""
        try:
            self.logger.info("Looking for 'Log in' button...")

            login_button_selectors = [
                "//div[contains(@class, 'html-div') and contains(text(), 'Log in')]",
                "//button[contains(text(), 'Log in')]",
                "//button[contains(text(), 'Log In')]",
                "//button[@type='submit']",
                "//div[@role='button' and contains(., 'Log in')]",
                "//*[contains(normalize-space(.), 'Log in') and (@role='button' or @type='submit' or contains(@class, 'html-div'))]",
            ]

            login_button = None
            for selector in login_button_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            login_button = element
                            self.logger.info("Found 'Log in' button")
                            break
                    if login_button:
                        break
                except:
                    continue

            if not login_button:
                self.logger.error("Could not find 'Log in' button")
                return False

            self.logger.info("Clicking 'Log in' button...")
            try:
                login_button.click()
                time.sleep(7)
                self.logger.info("Successfully clicked 'Log in' button")
            except Exception as click_error:
                self.logger.warning(f"Normal click failed, trying JavaScript: {click_error}")
                try:
                    self.driver.execute_script("arguments[0].click();", login_button)
                    time.sleep(7)
                    self.logger.info("Successfully clicked with JavaScript")
                except Exception as js_error:
                    self.logger.error(f"JavaScript click also failed: {js_error}")
                    return False

            # Check for incorrect password error
            if self._check_for_incorrect_password():
                self.logger.error("Incorrect password error detected")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error clicking login button: {e}")
            return False

    def _check_for_incorrect_password(self) -> bool:
        """Check if incorrect password error is displayed"""
        try:
            page_source = self.driver.page_source

            # Check for incorrect password error messages
            error_indicators = [
                "Sorry, your password was incorrect" in page_source,
                "Please double-check your password" in page_source,
            ]

            if any(error_indicators):
                self.logger.error("Incorrect password error message found on page")
                return True

            # Also check for error elements
            try:
                error_elements = self.driver.find_elements(By.XPATH,
                    "//*[contains(text(), 'Sorry, your password was incorrect')] | //*[contains(text(), 'Please double-check your password')]")
                if error_elements:
                    return True
            except:
                pass

            return False

        except Exception as e:
            self.logger.error(f"Error checking for incorrect password: {e}")
            return False

    def _is_2fa_required(self) -> bool:
        """Check if 2FA is required"""
        try:
            self.logger.info("Checking if 2FA is required...")

            current_url = self.driver.current_url.lower()
            page_source = self.driver.page_source.lower()

            # Check for 2FA page indicators
            twofa_indicators = [
                "accounts/login/two_factor" in current_url,
                "two_factor" in current_url,
                "enter a 6-digit login code" in page_source,
                "enter the 6-digit code" in page_source,
                "authentication code" in page_source,
                "security code" in page_source,
            ]

            # Look for 2FA elements
            twofa_elements = []
            try:
                code_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[placeholder*='code' i]")
                confirm_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Confirm')]")
                twofa_elements = code_inputs + confirm_buttons
            except:
                pass

            is_2fa = any(twofa_indicators) or len(twofa_elements) > 0
            self.logger.info(f"2FA text indicators: {any(twofa_indicators)}")
            self.logger.info(f"2FA elements found: {len(twofa_elements)}")

            return is_2fa

        except Exception as e:
            self.logger.error(f"Error checking 2FA requirement: {e}")
            return False

    def _handle_2fa(self) -> bool:
        """Handle two-factor authentication"""
        try:
            # Wait for extension to fill 2FA code
            self.logger.info("Waiting 5 seconds for extension to fill 2FA code...")
            time.sleep(5)

            # Look for Confirm button
            confirm_button_selectors = [
                "//button[contains(@class, '_asx2') and contains(text(), 'Confirm')]",
                "//button[contains(text(), 'Confirm')]",
                "//button[@type='submit']",
                "//div[@role='button' and contains(., 'Confirm')]",
                "//*[contains(normalize-space(.), 'Confirm') and (@role='button' or @type='submit')]",
            ]

            confirm_button = None
            for selector in confirm_button_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            confirm_button = element
                            self.logger.info("Found 'Confirm' button")
                            break
                    if confirm_button:
                        break
                except:
                    continue

            if not confirm_button:
                self.logger.error("Could not find 'Confirm' button")
                return False

            self.logger.info("Clicking 'Confirm' button...")
            try:
                confirm_button.click()
                time.sleep(7)
                self.logger.info("Successfully clicked 'Confirm' button")
                return True
            except Exception as click_error:
                self.logger.warning(f"Normal click failed, trying JavaScript: {click_error}")
                try:
                    self.driver.execute_script("arguments[0].click();", confirm_button)
                    time.sleep(7)
                    self.logger.info("Successfully clicked with JavaScript")
                    return True
                except Exception as js_error:
                    self.logger.error(f"JavaScript click also failed: {js_error}")
                    return False

        except Exception as e:
            self.logger.error(f"Error handling 2FA: {e}")
            return False

    def handle_cookie_consent(self) -> bool:
        """Handle cookie consent popup if present"""
        try:
            self.logger.info("Checking for cookie consent popup...")
            time.sleep(1)

            selectors = [
                ("css", "button._a9--._ap36._asz1"),
                ("css", "button._a9--._ap36"),
                ("xpath", "//button[contains(text(), 'Allow all cookies')]"),
                ("xpath", "//button[contains(., 'Allow all cookies')]"),
                ("css", "button._a9--[tabindex='0']"),
                ("xpath", "//div[@role='button' and contains(text(), 'Allow all cookies')]"),
            ]

            for selector_type, selector in selectors:
                try:
                    if selector_type == "css":
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    else:
                        elements = self.driver.find_elements(By.XPATH, selector)

                    for element in elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                self.logger.info(f"Found cookie button ({selector_type})")
                                try:
                                    element.click()
                                except:
                                    self.driver.execute_script("arguments[0].click();", element)
                                self.logger.info("Clicked 'Allow all cookies' button")
                                time.sleep(2)
                                return True
                        except:
                            continue
                except:
                    continue

            self.logger.info("No cookie consent button found (may not be needed)")
            return True

        except Exception as e:
            self.logger.error(f"Error handling cookie consent: {e}")
            return True  # Not critical, continue anyway
