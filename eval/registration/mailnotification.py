from zope.component.hooks import getSite
from email import message_from_string
from Products.CMFCore.utils import getToolByName

def handle_register(event):
    site = getSite()
    data = event.data
    encoding = site.getProperty('email_charset', 'utf-8')
    mail_text = site.registration_email(
        user=data,
        portal=site,
        charset=encoding
    )
    
    message_obj = message_from_string(mail_text)
    mTo = message_obj['To']
    mFrom = message_obj['From']
    subject = message_obj['Subject']

    site.MailHost.send(mail_text, mTo, mFrom, subject=subject, 
                        charset=encoding)

def get_role_emails(portal, role):
    local_roles = portal.get_local_roles()
    if len(local_roles) == 0:
        return []
    recipients = set()
    for user, roles in local_roles:
        rolelist = list(roles)
        if role in rolelist:
            recipients.add(user)

    # check for the acquired roles
    sharing_page = portal.unrestrictedTraverse('@@sharing')
    acquired_roles = sharing_page._inherited_roles()
    acquired_users = [r[0] for r in acquired_roles
                      if role in r[1]]
    recipients.update(acquired_users)

    # check for global roles
    pas = getToolByName(portal, 'acl_users')
    rolemanager = pas.portal_role_manager
    global_role_ids = [ p[0] for p in (
        rolemanager.listAssignedPrincipals(role)
    )]
    recipients.update(global_role_ids)

    # check to see if the recipents are users or groups
    group_recipients = []
    new_recipients = []
    group_tool = portal.portal_groups
    membertool = getToolByName(portal, "portal_membership")

    def _getGroupMemberIds(group):
        """ Helper method to support groups in groups. """
        members = []
        for member_id in group.getGroupMemberIds():
            subgroup = group_tool.getGroupById(member_id)
            if subgroup is not None:
                members.extend(_getGroupMemberIds(subgroup))
            else:
                members.append(member_id)
        return members

    for recipient in recipients:
        group = group_tool.getGroupById(recipient)
        if group is not None:
            group_recipients.append(recipient)
            [new_recipients.append(user_id)
             for user_id in _getGroupMemberIds(group)]

    for recipient in group_recipients:
        recipients.remove(recipient)

    for recipient in new_recipients:
        recipients.add(recipient)

    # look up e-mail addresses for the found users
    recipients_mail = set()
    for user in recipients:
        recipient_member = membertool.getMemberById(user)
        if not recipient_member:
            continue
        recipient_prop = recipient_member.getProperty('email')
        if recipient_prop != None and len(recipient_prop) > 0:
            recipients_mail.add(recipient_prop)

    return recipients_mail

def handle_notify_register(event):
    site = getSite()
    data = event.data
    encoding = site.getProperty('email_charset', 'utf-8')

    required_role = u'Manager'
    recipients = get_role_emails(site, required_role)

    for recipient in recipients:
        mail_text = site.registration_moderator_email(
            user=data,
            portal=site,
            charset=encoding,
            moderator=recipient
        )

        message_obj = message_from_string(mail_text)
        mTo = message_obj['To']
        mFrom = message_obj['From']
        subject = message_obj['Subject']

        site.MailHost.send(mail_text, mTo, mFrom, subject=subject, 
                        charset=encoding)



def handle_approve(event):
    site = getSite()
    data = event.data
    encoding = site.getProperty('email_charset', 'utf-8')

    mt = site.portal_membership
    member = mt.getMemberById(data['username'])

    reset_tool = site.portal_password_reset
    reset = reset_tool.requestReset(member.getId())

    mail_text = site.registration_approval_email(
        user=data,
        portal=site,
        charset=encoding,
        member=member,
        reset=reset
    )

    message_obj = message_from_string(mail_text)
    mTo = message_obj['To']
    mFrom = message_obj['From']
    subject = message_obj['Subject']
    
    site.MailHost.send(mail_text, mTo, mFrom, subject=subject, 
                        charset=encoding)