from Products.CMFCore.utils import (UniqueObject, registerToolInterface,
                                    getToolByName)
from OFS.SimpleItem import SimpleItem
from persistent.dict import PersistentDict
from eval.registration.interfaces import IRegistrationApproval
from eval.registration.events import (
    UserApprovedEvent, UserRegisteredEvent,
    UserRejectedEvent
)
from Products.CMFPlone.PloneBaseTool import PloneBaseTool
from Globals import InitializeClass 
from AccessControl import ClassSecurityInfo
from zope.interface import implements
import logging
from plone.app.users.userdataschema import IUserDataSchemaProvider
from zope.component import getUtility, getAdapter
from zope.component.hooks import getSite
from zope.event import notify
from Products.statusmessages.interfaces import IStatusMessage
from zope.globalrequest import getRequest
from zope.schema import getFieldNamesInOrder

class ConflictError(Exception):
    pass

class RegistrationApproval(PloneBaseTool, UniqueObject, SimpleItem):
    implements(IRegistrationApproval)

    id = 'eval_membership_registration_approval'
    meta_type = 'EVAL Registration Approval Tool'
    toolicon = 'skins/plone_images/site_icon.png'
    security = ClassSecurityInfo()

    def __init__(self):
        self._data = PersistentDict()
    
    def is_memberid_allowed(self, key):
        return not (key in self._data.keys())

    def values(self):
        for x in self._data.values():
            if not x.has_key('username'):
                x['username'] = x['email']
        return sorted(self._data.values(), key=(lambda x: x['username']))

    def add(self, key, data):
        if key in self._data.keys():
            raise ConflictError(u'User already exist in pending')
        data['username'] = key
        self._data[key] = data
        notify(UserRegisteredEvent(data))

    def get(self, key):
        return self._data[key]

    def approve(self, key):
        if key not in self._data.keys():
            raise KeyError(key)

        portal = getSite()
        registration = getToolByName(self, 'portal_registration')
        portal_props = getToolByName(self, 'portal_properties')
        mt = getToolByName(self, 'portal_membership')
        props = portal_props.site_properties
        use_email_as_login = props.getProperty('use_email_as_login')

        data = self._data[key]

        if use_email_as_login:
            data['username'] = data['email']

        user_id = data['username']
        password = registration.generatePassword()
        request = getRequest()
        try:
            registration.addMember(user_id, password, REQUEST=request)
        except (AttributeError, ValueError), err:
            logging.exception(err)
            IStatusMessage(request).addStatusMessage(err, type="error")
            return

        # set additional properties using the user schema adapter
        schema = getUtility(IUserDataSchemaProvider).getSchema()

        adapter = getAdapter(portal, schema)
        adapter.context = mt.getMemberById(user_id)

        for name in getFieldNamesInOrder(schema):
            if name in data:
                setattr(adapter, name, data[name])

        notify(UserApprovedEvent(data)) 
        del self._data[key]


    def reject(self, key):
        if key not in self._data.keys():
            return
        data = self._data[key]
        notify(UserRejectedEvent(data))
        del self._data[key]

InitializeClass(RegistrationApproval)
registerToolInterface('eval_membership_registration_approval', IRegistrationApproval)