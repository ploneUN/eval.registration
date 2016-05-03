from Products.Five import BrowserView
from zope import schema
from zope.interface import Interface
from plone.z3cform import layout
from plone.app.users.browser.register import RegistrationForm, BaseRegistrationForm
from zope.formlib import form
from Products.statusmessages.interfaces import IStatusMessage
from Products.CMFCore.utils import getToolByName
from zope.component.hooks import getSite
from plone.app.users.userdataschema import IUserDataSchemaProvider
from zope.component import getUtility
from zope.app.form.interfaces import WidgetInputError, InputErrors
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.schema.interfaces import ValidationError
from eval.registration.interfaces import IExtendRegistrationForm, ExtendRegistrationForm
from zope.interface import implements
from quintagroup.formlib.captcha import CaptchaWidget

from zope.component import getUtility, getAdapter
from zope.component.hooks import getSite
from zope.globalrequest import getRequest
import logging
from plone.app.users.userdataschema import IUserDataSchemaProvider
from eval.registration.events import (
    UserApprovedEvent, UserRegisteredEvent,
    UserRejectedEvent
)
from zope.schema import getFieldNamesInOrder
from zope.event import notify

class RegisterForm(RegistrationForm):
    implements(IExtendRegistrationForm)
    template = ViewPageTemplateFile('register_form.pt')

    @property
    def form_fields(self):
        #defaultFields = super(RegisterForm, self).form_fields
        defaultFields = BaseRegistrationForm(self, self.context).form_fields
        defaultFields += form.Fields(ExtendRegistrationForm)
        defaultFields['captcha'].custom_widget = CaptchaWidget
        schema = getUtility(IUserDataSchemaProvider).getSchema()
        
        #registrationfields = getUtility(
        #    IUserDataSchemaProvider
        #).getRegistrationFields()
        #return (defaultFields.omit('password', 'password_ctl', 'mail_me') + 
        #        form.Fields(schema).select(*registrationfields))
        return defaultFields.omit('password', 'password_ctl', 'mail_me')

    def validate_registration(self, action, data):
        errors = super(RegisterForm, self).validate_registration(action,data)

        #if not self.context.restrictedTraverse('@@captcha').verify():
        #    err_str = u'Invalid captcha'
        #    errors.append(ValidationError(err_str))

        portal_props = getToolByName(self.context, 'portal_properties')
        props = portal_props.site_properties
        use_email_as_login = props.getProperty('use_email_as_login')

        error_keys = [error.field_name for error in errors
                      if hasattr(error, 'field_name')]

        username = ''
        email = ''
        try:
            email = self.widgets['email'].getInputValue()
        except InputErrors, exc:
            # WrongType?
            errors.append(exc)
        if use_email_as_login:
            username_field = 'email'
            username = email
        else:
            username_field = 'username'
            try:
                username = self.widgets['username'].getInputValue()
            except InputErrors, exc:
                errors.append(exc)
        
        ratool = getToolByName(self.context, 'eval_membership_registration_approval')

        # check if username is allowed
        if not username_field in error_keys:
            if not ratool.is_memberid_allowed(username):
                err_str = (u"The login name you selected is already in use "
                            "or is not valid. Please choose another.")
                errors.append(WidgetInputError(
                        username_field, u'label_username', err_str))
                self.widgets[username_field].error = err_str
 
        return errors 

    def handle_join_success(self, data):
        portal_props = getToolByName(self.context, 'portal_properties')
        props = portal_props.site_properties
        use_email_as_login = props.getProperty('use_email_as_login')

        username = ''
        email = ''
        email = self.widgets['email'].getInputValue()
        if use_email_as_login:
            username = email
            data['username'] = data['email']
        else:
            username = self.widgets['username'].getInputValue()
        if data['email'].endswith('ilo.org'):
            self.approve(data, self.request)
        else:
            ratool = getToolByName(self.context, 'eval_membership_registration_approval')
    
            ratool.add(username, data)

    @form.action(u'Register',
                 validator='validate_registration', name=u'register')
    def action_join(self, action, data):
        self.handle_join_success(data)
        
        if data.has_key('email'):
            if data['email'].endswith('ilo.org'):
                return self.request.response.redirect(getSite().absolute_url() +
                '/registration_successful')
                
            else:
                return self.request.response.redirect(getSite().absolute_url() +
                '/registration_success')
    
    def approve(self, data, request):
        portal = getSite()
        
        registration = getToolByName(self, 'portal_registration')
        portal_props = getToolByName(self, 'portal_properties')
        mt = getToolByName(self, 'portal_membership')
        props = portal_props.site_properties
        use_email_as_login = props.getProperty('use_email_as_login')
        
        if use_email_as_login:
            data['username'] = data['email']
        user_id = data['username']
        password = registration.generatePassword()
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
