from eval.registration.interfaces import IRegistrationApproval
from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
import copy

class ListPendingApproval(BrowserView):

    def items(self):
        ratool = getToolByName(self.context, 'eval_membership_registration_approval')
        return copy.copy(ratool.values())

    def __call__(self):
        if self.request.method == 'POST':
            ratool = getToolByName(self.context, 'eval_membership_registration_approval')
            users = self.request.get('member')
            if self.request.get('approve'):
                for user in users:
                    ratool.approve(user)
            elif self.request.get('reject'):
                for user in users:
                    ratool.reject(user)
        return super(ListPendingApproval, self).__call__()
