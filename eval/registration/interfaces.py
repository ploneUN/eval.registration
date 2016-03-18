from zope.interface import Interface
from zope import schema
from quintagroup.formlib.captcha import Captcha

class IProductSpecific(Interface):
    pass

class IUserApprovedEvent(Interface):
    pass

class IUserRejectedEvent(Interface):
    pass

class IUserRegisteredEvent(Interface):
    pass

class IRegistrationApproval(Interface):

    def get(key):
        pass

    def add(key, data):
        pass

    def approve(key):
        pass

    def reject(key):
        pass
    
class IExtendRegistrationForm(Interface):
    """Marker interface for my custom registration form
    """


class ExtendRegistrationForm(Interface):
    
    
    captcha = Captcha(
        title=(u'Type the code'),
        description=(u'Type the code from the picture shown below.'))