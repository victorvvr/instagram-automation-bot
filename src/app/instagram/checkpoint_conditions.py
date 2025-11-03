from app.instagram.enums.checkpoint import Checkpoint
from selenium import webdriver
from selenium.webdriver.common.by import By
from typing import Callable
from dataclasses import dataclass
import operator


@dataclass
class CheckpointCondition:
    checkpoint: Checkpoint
    condition_url: str = ""
    xpath_query: str = ""
    xpath_item_len: int = 0
    cond_operator: Callable[[int, int], bool] = None
    before_action_checkpoint: Checkpoint = None

    def is_active(self, driver: webdriver.Chrome):
        if (
            len(self.condition_url) > 0
            and self.condition_url in driver.current_url
        ):
            return True

        if len(self.xpath_query) <= 0:
            return False

        return self.cond_operator(
            len(driver.find_elements(By.XPATH, self.xpath_query)),
            self.xpath_item_len,
        )

    def get_cp(self, before_action: bool = False):
        if (
            before_action is True
            and self.before_action_checkpoint is not None
        ):
            return self.before_action_checkpoint

        return self.checkpoint


CONDITIONS = {
    Checkpoint.AccountLoggedOut: CheckpointCondition(
        checkpoint=Checkpoint.AccountLoggedOut,
        xpath_item_len=0,
        xpath_query="//div[@role='button' and text()='Log in'] | //div[text()='Log in'] | //div[text()='Sign up for Instagram'] | //button[text()='Log In']",
        cond_operator=operator.gt,
    ),
    Checkpoint.AccountSuspended: CheckpointCondition(
        checkpoint=Checkpoint.AccountSuspended,
        condition_url="/accounts/suspended",
    ),
    Checkpoint.AccountBanned: CheckpointCondition(
        checkpoint=Checkpoint.AccountBanned,
        condition_url="/accounts/disabled",
    ),
    Checkpoint.AutomaticBehaviourSuspected: CheckpointCondition(
        checkpoint=Checkpoint.AutomaticBehaviourSuspected,
        xpath_item_len=0,
        xpath_query="//*[text()='We suspect automated behavior on your account']",
        cond_operator=operator.gt,
    ),
    Checkpoint.BadProxy: CheckpointCondition(
        checkpoint=Checkpoint.BadProxy,
        xpath_item_len=2,
        xpath_query="//span[text()='This page isn’t working'] | //div[text()='HTTP ERROR 429']",
        cond_operator=operator.ge,
    ),
    Checkpoint.SaveLoginInfo: CheckpointCondition(
        checkpoint=Checkpoint.SaveLoginInfo,
        xpath_item_len=0,
        xpath_query="//*[text()='Save info']",
        cond_operator=operator.gt,
    ),
    Checkpoint.SomethingWentWrongCheckpoint: CheckpointCondition(
        checkpoint=Checkpoint.SomethingWentWrongCheckpoint,
        xpath_item_len=2,
        xpath_query="//h3[text()='Something went wrong'] | //div[text()='Reload page']",
        cond_operator=operator.eq,
    ),
    Checkpoint.AccountCompromised: CheckpointCondition(
        checkpoint=Checkpoint.AccountCompromised,
        xpath_item_len=2,
        xpath_query="//h3[text()='Your Account Was Compromised'] | //div[text()='Change Password']",
        cond_operator=operator.eq,
    ),
    Checkpoint.PageUnavailable: CheckpointCondition(
        checkpoint=Checkpoint.PageUnavailable,
        xpath_item_len=0,
        xpath_query='//*[text()="Sorry, this page isn\'t available."]',
        cond_operator=operator.gt,
    ),
    Checkpoint.PageFollowed: CheckpointCondition(
        before_action_checkpoint=Checkpoint.AlreadyFollowedOrRequested,
        checkpoint=Checkpoint.PageFollowed,
        xpath_item_len=0,
        xpath_query="//div[text()='Following']",
        cond_operator=operator.gt,
    ),
    Checkpoint.PageRequested: CheckpointCondition(
        before_action_checkpoint=Checkpoint.AlreadyFollowedOrRequested,
        checkpoint=Checkpoint.PageRequested,
        xpath_item_len=0,
        xpath_query="//div[text()='Requested'] | //h3[text()='Your request is pending']",
        cond_operator=operator.gt,
    ),
    Checkpoint.PageFollowedOrRequested: CheckpointCondition(
        before_action_checkpoint=Checkpoint.AlreadyFollowedOrRequested,
        checkpoint=Checkpoint.PageFollowedOrRequested,
        xpath_item_len=0,
        xpath_query="//div[text()='Following'] | //div[text()='Requested'] | //h3[text()='Your request is pending']",
        cond_operator=operator.gt,
    ),
}

logged_in_condition = CheckpointCondition(
    checkpoint=Checkpoint.AccountLoggedIn,
    xpath_item_len=0,
    xpath_query="//div[@role='button' and text()='Log in'] | //div[text()='Log in'] | //div[text()='Sign up for Instagram'] | //button[text()='Log In'] | //*[text()='Log In'] | //*[text()='Log in']",
    cond_operator=operator.le,
)

logged_out_condition = CheckpointCondition(
    checkpoint=Checkpoint.AccountLoggedOut,
    xpath_item_len=0,
    xpath_query="//div[@role='button' and text()='Log in'] | //div[text()='Log in'] | //div[text()='Sign up for Instagram'] | //button[text()='Log In']",
    cond_operator=operator.gt,
)

is_page_private_condition = CheckpointCondition(
    checkpoint=Checkpoint.PageIsPrivate,
    xpath_item_len=0,
    xpath_query="//*[text()='This account is private']",
    cond_operator=operator.gt,
)
