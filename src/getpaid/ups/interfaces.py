"""
$Id: $
"""

from zope import schema, interface
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

from getpaid.core.interfaces import IShippingRateService

from zope.i18nmessageid import MessageFactory
_ = MessageFactory('getpaid.ups')


UPS_URLS = SimpleVocabulary([
    SimpleTerm( 'https://wwwcie.ups.com/ups.app/xml/Rate', "sandbox", title=_(u"Sandbox") ),
    SimpleTerm( 'https://www.ups.com/ups.app/xml/Rate', "production", title=_(u"Production") )
    ])
    
UPS_SERVICES = SimpleVocabulary([
    SimpleTerm('01', 'next-day-air', _(u'UPS Next Day Air')),
    SimpleTerm('02', '2nd-day-air', _(u'UPS 2nd Day Air')),
    SimpleTerm('03', 'ground', _(u'UPS Ground')),
    SimpleTerm('07', 'worldwide-express', _(u'UPS Worldwide Express')),
    SimpleTerm('08', 'worldwide-expedited', _(u'UPS Worldwide Expedited')),
    SimpleTerm('11', 'standard', _(u'UPS Standard')), 
    SimpleTerm('12', 'three-day-select', _(u'UPS Three Day Select')),
    SimpleTerm('13', 'next-day-air-saver', _(u'UPS Next Day Air Saver')),
    SimpleTerm('14', 'next-day-early-am', _(u'UPS Next Day Air Early AM')),
    SimpleTerm('54', 'worldwide-plus', _(u'UPS Worldwide Express Plus')),
    SimpleTerm('59', '2nd-day-air-am', _(u'UPS 2nd Day Air AM')),
    SimpleTerm('65', 'saver', _(u'UPS Saver')),
    ])

UPS_PICKUP_TYPES = SimpleVocabulary([
    SimpleTerm('01', 'daily-pickup', _(u'Daily Pickup')),
    SimpleTerm('03', 'customer-counter', _(u'Customer Counter')),
    SimpleTerm('06', 'one-time-pickup', _(u'One Time Pickup')),
    SimpleTerm('07', 'on-call-air', _(u'On Call Air')),
    SimpleTerm('11', 'retail-rates', _(u'Suggested Retail Rates')),
    SimpleTerm('19', 'letter-center', _(u'Letter Center')),
    SimpleTerm('20', 'air-service-center', _(u'Air Service Center'))
    ])

CUSTOMER_CLASSIFICATION = SimpleVocabulary([
    SimpleTerm('01', 'wholesale', _(u'Wholesale') ),
    SimpleTerm('03', 'occassional', _(u'Occassional') ),
    SimpleTerm('04', 'retail', _(u'Retail') ),
    ])

UPS_CURRENCY_CODES = SimpleVocabulary([
    SimpleTerm('USD', 'us-dollars', _(u'US Dollars (USD)') ),
    SimpleTerm('GBP', 'gb-pounds', _(u'British Pounds (GBP)') ),
    SimpleTerm('CAD', 'ca-dollars', _(u'Canadian Dollars (CAD)') ),
    SimpleTerm('EUR', 'euros', _(u'Euros (EUR)') )
    ])

UPS_WEIGHT_UNITS = SimpleVocabulary([
    SimpleTerm('LBS', 'pounds',_(u'Pounds')),
    SimpleTerm('KGS', 'kilograms', _(u'Kilograms')),
    ])

UPS_STATUS_CODES = SimpleVocabulary([
    SimpleTerm( '1', 'success', _(u'Success') ),
    SimpleTerm( '0', 'failture', _(u'Failure') )
    ])


class IUPSRateService( IShippingRateService ):
    """
    UPS Rates Service
    """
    
    def getRates( order ):
        """
        given an order object, return a set of shipping method rate objects
        for available shipping options, on error raises an exception.
        """

    
class IOriginRouter( interface.Interface ):
    
    def getOrigin( ):
        """
        determine the origin shipping point for an order..
        
        return the contact and address info for origin
        
        TODO: support multiple origins for an order if someone can justify ;-)
        """

class IShippingMethodRate( interface.Interface ):
    """
     Service Code: UPS Next Day Air
     Shipment unit of measurement: LBS
     Shipment weight: 3.0
     Currency Code: USD
     Total Charge: 58.97
     Days to Delivery: 1
     Delivery Time: 10:30 A.M.
    """
    
    service_code = schema.ASCIILine( description=_(u"UPS Service Code (2 Letter)"))
    service = schema.TextLine( description=_(u"UPS Service Name"))
    
    currency = schema.ASCII( description=_(u"Currency Denomination Code"))
    cost = schema.Float( description=_(u"Cost of Delivery"))
    
    # really shouldn't show these, as they ignore store processing time
    days_to_delivery = schema.Int( description=_(u"Estimated Days to Deliver") )
    delivery_time = schema.TextLine( description=_(u"Estimated Delivery Time") ) 


def check_settings( settings ):

    if settings.pickup_type and not settings.customer_classification:
        raise schema.ValidationError("Customer Classification Code is required for Pickup Type")

class IUPSSettings( interface.Interface ):
    """
    UPS Rates Service Options
    """

    interface.invariant( check_settings )
    
    server_url = schema.Choice(
        title = _(u"UPS Shipment Processor URL"),
        vocabulary = UPS_URLS,
        description = _(u"Select Sandbox while testing your store, and switch to Production for the real thing."),
        default = UPS_URLS.getTermByToken("sandbox").value,
        required = True,
        )
    
    services = schema.List( title = _(u"UPS Services"),
                            required = True,
                            default = [],
                            description = _(u"The services to offer in your store."),
                            value_type = schema.Choice( title=u"ups_services_choice",
                                                        vocabulary=UPS_SERVICES,
                                                        )
                            )
    
    username = schema.ASCIILine( title = _(u"UPS User Name"),
        required = True,
        description = _(u"The user name you supplied when registering for your UPS access key."))
                                    
    password = schema.Password( title = _(u"UPS Password"),
        required = True,
        description = _(u"The password you supplied when registering for your UPS access key."))
                                    
    access_key = schema.ASCIILine( title = _(u"UPS Access Key"), 
        required = True,
        description = _(u"The access (not developer!) key issued to you by UPS."))

    pickup_type = schema.Choice( title=_(u"Pickup Type"),
                                 vocabulary = UPS_PICKUP_TYPES,
                                 required = False,
                                 description = _(u"Select how UPS Normally Pickups your packages"),
                                 default= UPS_PICKUP_TYPES.getTermByToken('customer-counter').value
                                 )
    customer_classification = schema.Choice( title=_(u"Customer Classification"),
                                             vocabulary = CUSTOMER_CLASSIFICATION,
                                             required = False,
                                             default = CUSTOMER_CLASSIFICATION.getTermByToken('retail').value
                                             )
    
    # ups does default association of units by country...
    # weight_unit = schema.Choice( title = _(u"Unit of weight"),
    #     vocabulary = UPS_WEIGHT_UNITS.keys(),
    #     required = True,
    #     description = _(u"Select which unit of weight to use for your products."),
    #     )
    #     
    # currency_code = schema.Choice( title = _(u"UPS Currency Code"),
    #     values = UPS_CURRENCY_CODES.keys(),
    #     required = True,
    #     description = _(u"The currency that UPS will use when calculating your rates."),
    #     )

class IUPSError( interface.Interface ):
    status_code = schema.ASCIILine()
    status_desc = schema.ASCIILine()
    error_desc  = schema.ASCIILine()
    error_serverity = schema.ASCIILine()
    error_code = schema.ASCIILine()
    error_location_elem_name = schema.ASCIILine()
    
class UPSError( Exception ):
    interface.implements( IUPSError )

    def __init__( self,
                  status_code,
                  status_desc,
                  error_code,
                  error_desc,
                  error_severity,
                  error_location_elem_name="",
                  **ignored ):

        self.status_code = status_code
        self.status_desc = status_desc
        self.error_code = error_code
        self.error_severity = error_severity
        self.error_desc = error_desc
        self.error_location_elem_name = error_location_elem_name

    def __str__( self ):
        return "< %s : %s : %s : %s>"%(
            self.__class__.__name__,
            self.status_desc,
            self.error_code,
            self.error_desc
            )
    __repr__ = __str__
    
class UPSInvalidCredentials( UPSError ):
    """ invalid credential settings """






                                            
