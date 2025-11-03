from app.instagram.enums.checkpoint import Checkpoint
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dataclasses import dataclass
import time
from app.core.logger import get_logger


@dataclass
class CheckpointBypass:
    xpath_btn_query: str = ""

    def do_bypass(self, driver: webdriver.Chrome) -> bool:
        logger = get_logger()
        logger.info(f"Attempting bypass with XPath: {self.xpath_btn_query}")

        try:
            # Try to find elements with a short wait
            elems = driver.find_elements(By.XPATH, self.xpath_btn_query)
            if len(elems) <= 0:
                logger.warning("No elements found for bypass")
                return False

            elem = elems[0]
            logger.info(f"Found element to click: {elem.tag_name}")

            # Scroll element into view
            driver.execute_script("arguments[0].scrollIntoView(true);", elem)
            time.sleep(0.5)

            # Try regular click first
            try:
                elem.click()
                logger.info("Successfully clicked element with regular click")
                time.sleep(2)
                return True
            except Exception as e:
                logger.warning(f"Regular click failed: {e}, trying JavaScript click...")
                try:
                    driver.execute_script("arguments[0].click();", elem)
                    logger.info("Successfully clicked element with JavaScript")
                    time.sleep(2)
                    return True
                except Exception as js_error:
                    logger.error(f"JavaScript click also failed: {js_error}")
                    return False

        except Exception as e:
            logger.error(f"Error in bypass: {e}")
            return False


BYPASSES = {
    Checkpoint.SaveLoginInfo: CheckpointBypass("//*[text()='Save info']"),
    Checkpoint.AutomaticBehaviourSuspected: CheckpointBypass(
        "//*[@role='button' and @aria-label='Dismiss'] | //div[@role='button' and contains(@aria-label, 'Dismiss')] | //*[text()='Dismiss']"
    ),
    Checkpoint.SomethingWentWrongCheckpoint: CheckpointBypass(
        "//div[text()='Reload page']"
    ),
}
