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
        registered_p = bool( len( [u for u in sm.getUtilitiesFor( interfaces.IUPSRateService)] ) )
        if registered_p:
            return
        
        shipping_method = rates.UPSRateService()
         
        try:
            sm.registerUtility(component=shipping_method, provided=interfaces.IUPSRateService )
        except TypeError:
            # BBB for Zope 2.9
            sm.registerUtility(interface=interfaces.IUPSRateService, utility=shipping_method)
        
    def uninstall( self ):
        pass
        
    def status( self ):
        return component.queryUtility( interfaces.IUPSRateService ) is not None
        
def storeInstalled( object, event ):
    return UPSPlugin( object ).install()