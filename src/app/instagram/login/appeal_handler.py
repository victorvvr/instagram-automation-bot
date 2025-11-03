import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from app.core.logger import get_logger
from .captcha_solver import CaptchaSolver
from .phone_verification import PhoneVerification


class AppealHandler:
    """Handles Instagram account suspension appeals"""

    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.logger = get_logger()
        self.captcha_solver = CaptchaSolver(driver)
        self.phone_verification = PhoneVerification(driver)

    def handle_suspended_account(self) -> bool:
        """
        Handle suspended account appeal process

        Returns:
            True if appeal process completed successfully, False otherwise
        """
        try:
            self.logger.info("Account is suspended - starting appeal process...")

            # Check if we need to click the Appeal button first
            if self._click_appeal_button_if_present():
                self.logger.info("Clicked Appeal button, waiting for next page...")
                time.sleep(3)

            # Check for manual intervention requirements
            if self._check_for_manual_intervention():
                return False

            # Detect which step of the appeal we're on
            appeal_step = self._detect_appeal_step()
            self.logger.info(f"Detected appeal step: {appeal_step}")

            if appeal_step == "captcha":
                # Handle captcha first
                if self.captcha_solver.handle_captcha_step():
                    self.logger.info("Captcha solved, proceeding to next step...")
                    time.sleep(5)

                    # Check for manual intervention after captcha
                    if self._check_for_manual_intervention():
                        return False

                    # Check what comes after captcha
                    next_step = self._detect_appeal_step()
                    if next_step == "phone":
                        return self.phone_verification.handle_phone_verification()
                    elif next_step == "selfie":
                        return self._handle_verification_selfie()
                    else:
                        # Try phone verification as default
                        return self.phone_verification.handle_phone_verification()
                else:
                    return False

            elif appeal_step == "phone":
                return self.phone_verification.handle_phone_verification()

            elif appeal_step == "selfie":
                return self._handle_verification_selfie()

            else:
                self.logger.warning("Unknown appeal step, attempting phone verification...")
                return self.phone_verification.handle_phone_verification()

        except Exception as e:
            self.logger.error(f"Error handling suspended account: {e}")
            return False

    def _click_appeal_button_if_present(self) -> bool:
        """Click the Appeal button if present on suspension page"""
        try:
            appeal_button_selectors = [
                "//div[@role='button' and contains(@aria-label, 'Appeal')]",
                "//div[@role='button' and contains(text(), 'Appeal')]",
                "//button[contains(text(), 'Appeal')]",
                "//div[@role='button']//span[contains(text(), 'Appeal')]",
            ]

            for selector in appeal_button_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            self.logger.info("Found Appeal button")
                            try:
                                button.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", button)
                            return True
                except:
                    continue

            self.logger.info("No Appeal button found")
            return False

        except Exception as e:
            self.logger.error(f"Error clicking appeal button: {e}")
            return False

    def _check_for_manual_intervention(self) -> bool:
        """Check if manual intervention is required (email checkpoint or manual captcha)"""
        try:
            # Check for email checkpoint
            if self._check_for_email_checkpoint():
                self.logger.warning("Email checkpoint detected - manual intervention required")
                return True

            # Check for manual captcha (image code entry)
            if self._check_for_manual_captcha():
                self.logger.warning("Manual captcha detected - manual intervention required")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error checking for manual intervention: {e}")
            return False

    def _check_for_email_checkpoint(self) -> bool:
        """Check for email checkpoint requiring manual intervention"""
        try:
            email_checkpoint_selectors = [
                "textarea[placeholder='Email']",
                "textarea[placeholder*='email' i]",
                "input[placeholder='Email']",
                "input[placeholder*='email' i]",
            ]

            for selector in email_checkpoint_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and any(element.is_displayed() for element in elements):
                        current_url = self.driver.current_url.lower()
                        if 'suspended' in current_url or 'challenge' in current_url or 'checkpoint' in current_url:
                            self.logger.info("Found email checkpoint input field")
                            return True
                except:
                    continue

            return False

        except Exception as e:
            self.logger.error(f"Error checking for email checkpoint: {e}")
            return False

    def _check_for_manual_captcha(self) -> bool:
        """Check for manual captcha requiring human intervention"""
        try:
            manual_captcha_selectors = [
                "textarea[placeholder='Enter the code from the image']",
                "textarea[placeholder*='code from the image']",
                "input[placeholder='Enter the code from the image']",
                "input[placeholder*='code from the image']",
            ]

            for selector in manual_captcha_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and any(element.is_displayed() for element in elements):
                        self.logger.info("Found manual captcha input field")
                        return True
                except:
                    continue

            # Check for "Can't read this text?" indicator
            page_source = self.driver.page_source.lower()
            if "can't read this text?" in page_source or "enter the code from the image" in page_source:
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error checking for manual captcha: {e}")
            return False

    def _detect_appeal_step(self) -> str:
        """
        Detect which step of the appeal process we're on

        Returns:
            "phone", "selfie", "captcha", or "unknown"
        """
        try:
            page_source = self.driver.page_source.lower()
            current_url = self.driver.current_url.lower()

            # Check for phone verification indicators
            phone_text_indicators = [
                "enter your mobile number" in page_source,
                "add your mobile number" in page_source,
                "mobile number" in page_source and "enter" in page_source,
                "phone number" in page_source,
            ]

            phone_elements = self.driver.find_elements(By.CSS_SELECTOR, "input[type='tel']")
            send_code_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Send code')] | //button[contains(text(), 'Text me')]")

            # Check for selfie verification indicators
            selfie_text_indicators = [
                "upload a verification selfie" in page_source,
                "upload a photo" in page_source and "face" in page_source,
                "verification selfie" in page_source,
                "selfie that clearly shows your face" in page_source,
            ]

            selfie_elements = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Upload')] | //input[@type='file']")

            # Check for captcha indicators
            captcha_text_indicators = [
                "confirm you're human" in page_source,
                "i'm not a robot" in page_source,
                "continue" in page_source and "suspended" in current_url,
            ]

            captcha_elements = self.driver.find_elements(By.CSS_SELECTOR, ".g-recaptcha")
            captcha_elements += self.driver.find_elements(By.XPATH, "//iframe[contains(@src, 'recaptcha')]")
            continue_buttons = self.driver.find_elements(By.XPATH, "//div[@role='button' and @aria-label='Continue']")

            # Calculate evidence scores
            phone_evidence = sum([
                any(phone_text_indicators),
                len(phone_elements) > 0,
                len(send_code_buttons) > 0,
            ])

            selfie_evidence = sum([
                any(selfie_text_indicators),
                len(selfie_elements) > 0,
            ])

            captcha_evidence = sum([
                any(captcha_text_indicators),
                len(captcha_elements) > 0,
                len(continue_buttons) > 0,
            ])

            self.logger.info(f"Evidence scores - Phone: {phone_evidence}, Selfie: {selfie_evidence}, Captcha: {captcha_evidence}")

            # Priority: Phone > Selfie > Captcha
            if phone_evidence >= 2:
                return "phone"
            elif selfie_evidence >= 2:
                return "selfie"
            elif captcha_evidence > 0:
                return "captcha"
            else:
                return "unknown"

        except Exception as e:
            self.logger.error(f"Error detecting appeal step: {e}")
            return "unknown"

    def _handle_verification_selfie(self) -> bool:
        """Handle verification selfie upload"""
        try:
            self.logger.info("Handling verification selfie upload...")

            # Find upload button
            upload_button_selectors = [
                "//button[contains(text(), 'Upload a photo')]",
                "//button[contains(text(), 'Upload')]",
                "//div[@role='button' and contains(text(), 'Upload a photo')]",
                "//div[@role='button' and contains(text(), 'Upload')]",
            ]

            upload_button = None
            for selector in upload_button_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            upload_button = button
                            self.logger.info("Found upload button")
                            break
                    if upload_button:
                        break
                except:
                    continue

            if upload_button:
                self.logger.info("Clicking 'Upload a photo' button...")
                try:
                    upload_button.click()
                except:
                    self.driver.execute_script("arguments[0].click();", upload_button)
                time.sleep(3)

            # Look for selfie image in project root
            photo_path = os.path.join(os.getcwd(), "verification_selfie.jpg")
            if not os.path.exists(photo_path):
                # Try alternate location
                photo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "verification_selfie.jpg")

            if not os.path.exists(photo_path):
                self.logger.error(f"Verification selfie not found at: {photo_path}")
                self.logger.error("Please place verification_selfie.jpg in the project root directory")
                return False

            self.logger.info(f"Using verification selfie: {photo_path}")

            # Upload via file input
            time.sleep(2)
            file_inputs = self.driver.find_elements(By.XPATH, "//input[@type='file']")
            if file_inputs:
                file_input = file_inputs[0]
                file_input.send_keys(photo_path)
                self.logger.info("Photo uploaded successfully")
                time.sleep(3)
            else:
                self.logger.error("Could not find file input element")
                return False

            # Click Submit button
            submit_button_selectors = [
                "//div[@role='button' and @aria-label='Submit']",
                "//div[@role='button' and contains(text(), 'Submit')]",
                "//button[contains(text(), 'Submit')]",
                "//button[@type='submit']",
            ]

            submit_button = None
            for selector in submit_button_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            submit_button = button
                            self.logger.info("Found Submit button")
                            break
                    if submit_button:
                        break
                except:
                    continue

            if submit_button:
                self.logger.info("Clicking Submit button...")
                try:
                    submit_button.click()
                except:
                    self.driver.execute_script("arguments[0].click();", submit_button)
                time.sleep(5)

                # Check for submission confirmation
                page_source = self.driver.page_source.lower()
                appeal_indicators = [
                    "you submitted an appeal" in page_source,
                    "appeal submitted" in page_source,
                    "we'll review your appeal" in page_source,
                ]

                if any(appeal_indicators):
                    self.logger.info("Appeal submitted successfully!")
                    return True
                else:
                    self.logger.warning("Could not confirm appeal submission")
                    return True  # Assume success if no error

            else:
                self.logger.error("Could not find Submit button")
                return False

        except Exception as e:
            self.logger.error(f"Error handling verification selfie: {e}")
            return False
