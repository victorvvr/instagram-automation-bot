from enum import Enum


class Checkpoint(str, Enum):
    BadProxy = "BadProxy"
    AccountCompromised = "AccountCompromised"
    SomethingWentWrongCheckpoint = "SomethingWentWrongCheckpoint"
    AutomaticBehaviourSuspected = "AutomaticBehaviourSuspected"
    AccountBanned = "AccountBanned"
    AccountSuspended = "AccountSuspended"
    AccountLoggedIn = "AccountLoggedIn"
    AccountLoggedOut = "AccountLoggedOut"
    IncorrectPassword = "IncorrectPassword"
    SaveLoginInfo = "SaveLoginInfo"
    PageFollowedOrRequested = "PageFollowedOrRequested"
    PageFollowed = "PageFollowed"
    PageRequested = "PageRequested"
    AlreadyFollowedOrRequested = "AlreadyFollowedOrRequested"
    PageUnavailable = "PageUnavailable"
    FailedToFollow = "FailedToFollow"
    FollowBlocked = "FollowBlocked"
    PageIsPrivate = "PageIsPrivate"
