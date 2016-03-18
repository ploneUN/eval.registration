from zope.interface import implements
from eval.registration.interfaces import (
    IUserApprovedEvent, IUserRejectedEvent,
    IUserRegisteredEvent
)
class UserApprovedEvent(object):
    implements(IUserApprovedEvent)

    def __init__(self, data):
        self.data = data

class UserRejectedEvent(object):
    implements(IUserRejectedEvent)

    def __init__(self, data):
        self.data = data

class UserRegisteredEvent(object):
    implements(IUserRegisteredEvent)

    def __init__(self, data):
        self.data = data