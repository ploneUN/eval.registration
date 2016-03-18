from collective.grok import gs
from eval.registration import MessageFactory as _

@gs.importstep(
    name=u'eval.registration', 
    title=_('eval.registration import handler'),
    description=_(''))
def setupVarious(context):
    if context.readDataFile('eval.registration.marker.txt') is None:
        return
    portal = context.getSite()

    # do anything here
