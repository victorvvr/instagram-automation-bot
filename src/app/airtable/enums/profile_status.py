from enum import Enum


class AirtableProfileStatus(str, Enum):
    LoggedIn = "Logged In"
    LoggedOut = "Logged Out"
    WaitingForAppeal = "Waiting for Appeal"
    CantLogIn = "Can't Log in"
    IncorrectPassword = "Incorrect Password"
    Bad2FA = "Bad 2FA"
    SomethingWentWrongCheckpoint = "Something went wrong Checkpoint"
    ChangePasswordCheckpoint = "Change Password Checkpoint"
    BadProxy = "Bad Proxy"
    Banned = "Banned 🔴"
