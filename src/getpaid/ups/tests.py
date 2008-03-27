"""
$Id: $

"""
import unittest, doctest
from zope import interface
from zope.testing.doctestunit import DocFileSuite
from zope.app.testing import placelesssetup, ztapi
from getpaid.ups import rates, interfaces
from getpaid.core.interfaces import IStoreSettings, IOrder, IOriginRouter
from getpaid.core import router



class MockStoreSettings( object ):
    interface.implements( IStoreSettings )
    store_name = "Rabbit Furs"
    contact_company = "Furs, LLC"
    contact_name = "Mr. Wolf"
    contact_phone = "5102928662"
    contact_fax = "9032131012"
    contact_address = "120 Pierce St."
    contact_address2 = ""
    contact_email = "mrwolf@example.com"
    contact_city = "San Francisco"
    contact_state = "CA"
    contact_postalcode = "94117"
    contact_country = "US"
                             
def setUp( test ):
    placelesssetup.setUp()

    ztapi.provideAdapter( IOrder, IOriginRouter, router.OriginRouter )
    ztapi.provideUtility( IStoreSettings, MockStoreSettings() )

def test_suite():
    import os
    globs = dict( UPS_PASSWORD=os.environ.get('UPS_PASSWORD'),
                  UPS_USERNAME=os.environ.get('UPS_USERNAME'),
                  UPS_ACCESS_KEY=os.environ.get('UPS_ACCESS_KEY') )
    
    return unittest.TestSuite((
        DocFileSuite('readme.txt',
                     setUp=setUp,
                     tearDown=placelesssetup.tearDown,
                     optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS,
                     globs=globs
                     ),    
        ))



