from app.instagram.enums.checkpoint import Checkpoint
from selenium.webdriver.common.by import By
from selenium import webdriver
from dataclasses import dataclass


@dataclass
class CheckpointBypass:
    xpath_btn_query: str = ""

    def do_bypass(self, driver: webdriver.Chrome) -> bool:
        elems = driver.find_elements(By.XPATH, self.xpath_btn_query)
        if len(elems) <= 0:
            return False

        elems[0].click()

        return True


BYPASSES = {
    Checkpoint.SaveLoginInfo: CheckpointBypass("//*[text()='Save info']"),
    Checkpoint.AutomaticBehaviourSuspected: CheckpointBypass(
        "//*[@role='button' and @aria-label='Dismiss'] | //div[@role='button' and contains(@aria-label, 'Dismiss')] | //*[text()='Dismiss']"
    ),
    Checkpoint.SomethingWentWrongCheckpoint: CheckpointBypass(
        "//div[text()='Reload page']"
    ),
}
