from selenium import webdriver
import time
from app.instagram.enums.checkpoint import Checkpoint
from app.instagram.checkpoint_conditions import (
    CONDITIONS,
    logged_in_condition,
    is_page_private_condition,
    logged_out_condition
)
from app.instagram.checkpoint_bypass import BYPASSES
from app.instagram.actions import (
    create_follow_action,
    AcceptRequestsAction,
    create_unfollow_action,
)
from app.selenium_utils.utils import navigate_to
from app.core.logger import get_logger


class InstagramWrapper:
    driver: webdriver.Chrome

    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver

    def is_logged_in(self):
        return logged_in_condition.is_active(self.driver)

    def accept_follow_requests(self) -> list[str]:
        navigate_to(self.driver, f"https://instagram.com")
        time.sleep(2)
        if self.is_logged_in() is False:
            return None

        action = AcceptRequestsAction()
        if action.run(self.driver) is False:
            get_logger().error(
                "[INSTAWRAPPER]: Accepting requests failed"
            )
            return []
        get_logger().info("[INSTAWRAPPER]: Accepting requests success")
        return action.accepted_users

    def unfollow_user(self, user: str):
        create_unfollow_action(user).run(self.driver)

    def get_cp(self, before_action: bool = False) -> Checkpoint:
        for cond in CONDITIONS.keys():
            if CONDITIONS[cond].is_active(self.driver):
                return CONDITIONS[cond].get_cp(before_action)
        return None

    def bypass_cp(self, cp: Checkpoint) -> bool:
        if cp in BYPASSES:
            return BYPASSES[cp].do_bypass(self.driver)
        return False

    def dismiss_automated_behavior_popup(self) -> bool:
        """Proactively check for and dismiss automated behavior popup"""
        try:
            # Check if the popup is present
            if CONDITIONS[Checkpoint.AutomaticBehaviourSuspected].is_active(self.driver):
                get_logger().info("Automated behavior popup detected, attempting to dismiss...")
                return self.bypass_cp(Checkpoint.AutomaticBehaviourSuspected)
        except:
            pass
        return False

    def visit_user_page(self, target: str):
        navigate_to(self.driver, f"https://instagram.com/{target}")
        # Check for and dismiss automated behavior popup after navigation
        self.dismiss_automated_behavior_popup()

    def follow_action(self, target: str) -> Checkpoint:
        # Navigate home page first
        self.visit_user_page("")

        # Check for incorrect password FIRST (before checking logged out)
        # This handles the case where login failed with wrong password
        if CONDITIONS[Checkpoint.IncorrectPassword].is_active(self.driver):
            return Checkpoint.IncorrectPassword

        # Check if user is logged out
        if logged_out_condition.is_active(self.driver):
            return Checkpoint.AccountLoggedOut

        # Proceed as normal
        self.visit_user_page(target)

        cp = self.get_cp(True)
        get_logger().info(
            f"[INSTAWRAPPER, TARGET: {target}]: Processing Checkpoint: {cp}"
        )
        if cp is not None:
            if self.bypass_cp(cp) is False:
                get_logger().info(
                    f"[INSTAWRAPPER, TARGET: {target}]: Bypass for {cp} non-existing or failed"
                )
                return cp

        get_logger().info(
            f"[INSTAWRAPPER, TARGET: {target}]: Executing Follow Action..."
        )

        is_page_private = is_page_private_condition.is_active(self.driver)

        create_follow_action().run(self.driver)

        cp = self.get_cp()
        if cp is None:
            return Checkpoint.FollowBlocked

        # Try to bypass checkpoint if it appears after follow action
        if cp is not None:
            bypass_attempted = self.bypass_cp(cp)
            if bypass_attempted:
                get_logger().info(
                    f"[INSTAWRAPPER, TARGET: {target}]: Bypass attempted after follow action for {cp}"
                )
                # Re-check checkpoint after bypass
                cp = self.get_cp()
                if cp is None:
                    return Checkpoint.FollowBlocked

        return cp
