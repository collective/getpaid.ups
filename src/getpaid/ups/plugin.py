"""
$Id: $
"""

from zope import component, interface
from getpaid.core.interfaces import IPluginManager
from getpaid.ups import interfaces 
from getpaid.ups import rates

class UPSPlugin( object ):

    interface.implements( IPluginManager )
    
    title = "UPS Shipping Method"
    description = "Provides for realtime price estimation for shipping via UPS, requires a UPS account"
    
    def __init__(self, context ):
        self.context = context
        
    def install( self ):
        sm = self.context.getSiteManager()
        utility = sm.queryUtility( interfaces.IShippingRateService, name="ups")
        if utility is not None:
            return

        shipping_service = rates.UPSRateService()
         
        try:
            sm.registerUtility(component=shipping_service, provided=interfaces.IShippingRateService, name="ups" )
        except TypeError:
            # BBB for Zope 2.9
            sm.registerUtility(interface=interfaces.IUPSRateService, utility=shipping_service)
        
    def uninstall( self ):
        pass
        
    def status( self ):
        return component.queryUtility( interfaces.IShippingRateService, name="ups" ) is not None
        
def storeInstalled( object, event ):
    return UPSPlugin( object ).install()