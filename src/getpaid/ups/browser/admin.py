"""
$Id: $
"""

from zope import component
from zope.formlib import form

from getpaid.ups import interfaces
from getpaid.ups.interfaces import _

from Products.PloneGetPaid.browser.base import EditFormViewlet

class UPSSettings( EditFormViewlet ):
    
    form_name = _(u"UPS Settings")
    form_description = _(u"Configuration of UPS Shipping")
    form_fields = form.Fields( interfaces.IUPSSettings )
    prefix = "ups"
    
    def setUpWidgets( self, ignore_request=False ):
        self.adapters = { interfaces.IUPSSettings : component.getUtility( interfaces.IShippingRateService, name="ups")}
        self.widgets = form.setUpEditWidgets(
            self.form_fields, self.prefix, self.context, self.request,
            adapters=self.adapters, ignore_request=ignore_request
            )
