"""
$Id: $
"""

from Products.PloneGetPaid.browser.base import BaseFormView, ViewPageTemplateFile


from getpaid.ups import interfaces
from zope import component
from zope.formlib import form

class SettingsForm( BaseFormView ):

    template = ViewPageTemplateFile("settings-page.pt")
    
    form_fields = form.Fields( interfaces.IUPSSettings )
    
    def __call__( self ):
        settings = interfaces.IUPSSettings(  component.getUtility( interfaces.IUPSRateService ) )
        self.adapters = { interfaces.IUPSSettings : settings }
        return super( SettingsForm, self).__call__()