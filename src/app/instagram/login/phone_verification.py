import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from app.core.config import get_cfg
from app.core.logger import get_logger


class PhoneVerification:
    """Handles phone verification using DaisySMS API"""

    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        cfg = get_cfg()
        self.daisysms_api_key = cfg["daisysms"]["apiKey"]
        self.daisysms_base_url = cfg["daisysms"]["baseUrl"]
        self.logger = get_logger()

    def handle_phone_verification(self, max_attempts: int = 5) -> bool:
        """
        Handle phone verification with multiple retry attempts

        Args:
            max_attempts: Maximum number of phone numbers to try

        Returns:
            True if verification successful, False otherwise
        """
        self.logger.info(f"Starting phone verification process (max {max_attempts} attempts)")

        for attempt in range(max_attempts):
            self.logger.info(f"Phone verification attempt {attempt + 1}/{max_attempts}")

            # Rent a phone number
            result = self._rent_phone_number()
            if not result:
                self.logger.error("Failed to rent phone number")
                time.sleep(5)
                continue

            activation_id, phone = result
            self.logger.info(f"Using phone number: {phone} (Activation ID: {activation_id})")

            # Remove country code if present
            phone_input = phone[1:] if phone.startswith('1') and len(phone) == 11 else phone

            # Enter phone number
            if not self._enter_phone_number(phone_input):
                self._cancel_phone_number(activation_id)
                continue

            # Click send code button
            time.sleep(2)
            if not self._click_send_code_button():
                self._cancel_phone_number(activation_id)
                continue

            # Wait for SMS code
            code = self._wait_for_sms_code(activation_id, timeout=60)

            if code:
                self.logger.info(f"Received SMS code: {code}")

                # Enter the verification code
                if self._enter_verification_code(code):
                    self._complete_phone_number(activation_id)
                    self.logger.info("Phone verification successful!")
                    return True
                else:
                    self.logger.warning("Failed to enter verification code")
            else:
                self.logger.warning("No SMS code received, trying another number")
                self._cancel_phone_number(activation_id)

        self.logger.error("Phone verification failed after all attempts")
        return False

    def _rent_phone_number(self):
        """Rent a phone number from DaisySMS"""
        try:
            params = {
                'api_key': self.daisysms_api_key,
                'action': 'getNumber',
                'service': 'ig',  # Instagram
                'country': '187'  # USA
            }

            response = requests.get(self.daisysms_base_url, params=params, timeout=30)
            response_text = response.text.strip()

            self.logger.info(f"DaisySMS rent response: {response_text}")

            if response_text.startswith('ACCESS_NUMBER'):
                parts = response_text.split(':')
                if len(parts) >= 3:
                    activation_id = parts[1]
                    phone = parts[2]
                    return (activation_id, phone)

            self.logger.error(f"Failed to rent number: {response_text}")
            return None

        except Exception as e:
            self.logger.error(f"Error renting phone number: {e}")
            return None

    def _enter_phone_number(self, phone: str) -> bool:
        """Enter phone number into input field"""
        try:
            # Try multiple selectors to find phone input
            phone_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='tel']")
            if not phone_inputs:
                phone_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[name*='phone']")
            if not phone_inputs:
                phone_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[aria-label*='phone' i]")
            if not phone_inputs:
                phone_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[placeholder*='phone' i]")

            if phone_inputs:
                phone_input_elem = phone_inputs[0]
                phone_input_elem.clear()
                time.sleep(1)
                phone_input_elem.send_keys(phone)
                self.logger.info(f"Entered phone number: {phone}")
                return True
            else:
                self.logger.error("Could not find phone input field")
                return False

        except Exception as e:
            self.logger.error(f"Error entering phone number: {e}")
            return False

    def _click_send_code_button(self) -> bool:
        """Click the send code button"""
        try:
            send_code_selectors = [
                "//button[contains(text(), 'Send code')]",
                "//button[contains(., 'Send code')]",
                "//div[@role='button' and contains(., 'Send code')]",
                "//button[contains(text(), 'Text me')]",
                "//button[contains(., 'Text me')]",
                "//div[@role='button' and contains(., 'Text me')]",
                "//button[contains(@aria-label, 'Send code')]",
                "//button[contains(text(), 'Send')]",
            ]

            for selector in send_code_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                            time.sleep(1)
                            try:
                                button.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", button)
                            self.logger.info("Clicked send code button")
                            time.sleep(3)
                            return True
                except:
                    continue

            self.logger.error("Could not find send code button")
            return False

        except Exception as e:
            self.logger.error(f"Error clicking send code button: {e}")
            return False

    def _wait_for_sms_code(self, activation_id: str, timeout: int = 60):
        """Wait for SMS code from DaisySMS"""
        try:
            start_time = time.time()

            while time.time() - start_time < timeout:
                params = {
                    'api_key': self.daisysms_api_key,
                    'action': 'getStatus',
                    'id': activation_id
                }

                response = requests.get(self.daisysms_base_url, params=params, timeout=10)
                response_text = response.text.strip()

                self.logger.debug(f"SMS status check: {response_text}")

                if response_text.startswith('STATUS_OK'):
                    parts = response_text.split(':')
                    if len(parts) >= 2:
                        code = parts[1].strip()
                        return code

                time.sleep(5)

            self.logger.warning("Timeout waiting for SMS code")
            return None

        except Exception as e:
            self.logger.error(f"Error waiting for SMS code: {e}")
            return None

    def _enter_verification_code(self, code: str) -> bool:
        """Enter the verification code"""
        try:
            # Find code input field
            code_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[aria-label*='code' i]")
            if not code_inputs:
                code_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[name*='code' i]")
            if not code_inputs:
                code_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='number']")
            if not code_inputs:
                code_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='tel']")

            if code_inputs:
                code_input = code_inputs[0]
                code_input.clear()
                time.sleep(1)
                code_input.send_keys(code)
                self.logger.info(f"Entered verification code")

                # Click submit/next button
                time.sleep(2)
                submit_selectors = [
                    "//button[contains(text(), 'Next')]",
                    "//button[contains(text(), 'Submit')]",
                    "//button[contains(text(), 'Verify')]",
                    "//button[contains(text(), 'Confirm')]",
                    "//div[@role='button' and contains(., 'Next')]",
                    "//div[@role='button' and contains(., 'Submit')]",
                ]

                for selector in submit_selectors:
                    try:
                        buttons = self.driver.find_elements(By.XPATH, selector)
                        for button in buttons:
                            if button.is_displayed() and button.is_enabled():
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                                time.sleep(1)
                                try:
                                    button.click()
                                except:
                                    self.driver.execute_script("arguments[0].click();", button)
                                self.logger.info("Clicked submit button")
                                time.sleep(5)
                                return True
                    except:
                        continue

                self.logger.warning("Could not find submit button, code may auto-submit")
                time.sleep(5)
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error entering verification code: {e}")
            return False

    def _complete_phone_number(self, activation_id: str):
        """Mark phone number as completed in DaisySMS"""
        try:
            params = {
                'api_key': self.daisysms_api_key,
                'action': 'setStatus',
                'status': '6',  # 6 = completed successfully
                'id': activation_id
            }

            response = requests.get(self.daisysms_base_url, params=params, timeout=10)
            self.logger.info(f"Marked phone as complete: {response.text}")

        except Exception as e:
            self.logger.error(f"Error completing phone number: {e}")

    def _cancel_phone_number(self, activation_id: str):
        """Cancel phone number rental in DaisySMS"""
        try:
            params = {
                'api_key': self.daisysms_api_key,
                'action': 'setStatus',
                'status': '8',  # 8 = cancel
                'id': activation_id
            }

            response = requests.get(self.daisysms_base_url, params=params, timeout=10)
            self.logger.info(f"Cancelled phone number: {response.text}")

        except Exception as e:
            self.logger.error(f"Error cancelling phone number: {e}")
