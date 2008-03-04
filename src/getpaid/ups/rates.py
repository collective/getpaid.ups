"""
$Id:
"""

from urllib2 import Request, urlopen, URLError
import elementtree.ElementTree as etree
from zope import interface, schema, component
from zope.app.container.contained import Contained
from persistent import Persistent
from getpaid.core import interfaces as igetpaid
from getpaid.core.interfaces import IShippableLineItem, IStoreSettings, IOrder, IShippingMethodRate
from getpaid.core.payment import ShippingAddress, ContactInformation
import interfaces

class OriginRouter( object ):
    # TODO : move this to getpaid.core
    # 
    component.adapts( IOrder )
    
    interface.implements( interfaces.IOriginRouter )
    
    def __init__( self, context ):
        self.context = context
        
    def getOrigin( self ):
        store_settings = component.getUtility( IStoreSettings )
        
        contact = ContactInformation( name = ( store_settings.contact_company or store_settings.store_name ),
                                      phone_number = store_settings.contact_phone,
                                      email = store_settings.contact_email )
                                         
        address = ShippingAddress( ship_first_line = store_settings.contact_address,
                                   ship_second_line = store_settings.contact_address2,
                                   ship_city = store_settings.contact_city,
                                   ship_state = store_settings.contact_state,
                                   ship_postal_code = store_settings.contact_postalcode,
                                   ship_country = store_settings.contact_country,
                                   )
        
        return contact, address

class UPSRateService( Persistent, Contained ):

    interface.implements(interfaces.IUPSRateService, interfaces.IUPSSettings)
    
    def __init__( self ):
        # initialize defaults from schema
        for name, field in schema.getFields( interfaces.IUPSSettings ).items():
            field.set( self, field.query( self, field.default ) )
        super( UPSRateService, self).__init__()
    
    def getSettingsInterface( self ):
        return interfaces.IUPSSettings
        
    def getRates( self, order ):
        settings = interfaces.IUPSSettings( self )
        store_contact = component.getUtility( IStoreSettings )
        origin_contact, origin_address = interfaces.IOriginRouter( order ).getOrigin()


        request = CreateRequest( settings,       # ups settings
                                 store_contact,  # store contact information 
                                 origin_contact, # origin contact information
                                 origin_address, # origin location
                                 order,          # destination contact and location
                                 pretty=True)
        
        try:
            response_text = SendRequest( settings.server_url, request ).read()
        except URLError:
            return []
        response = ParseResponse( etree.fromstring( response_text ) )
        # make sure to filter out options that we aren't offering in our store
        response.shipments = [service for service in response.shipments if service.service_code in settings.services]
        return response

class ShippingMethodRate( object ):
    """A Shipment Option and Price"""
    interface.implements( IShippingMethodRate )

    service_code = ""
    service = ""
    currency = ""
    cost = 0
    days_to_delivery = 0
    delivery_time = ""
    
    def __repr__( self ):
        return  "<UPS Method %s>"%(str(self.__dict__))
    
class UPSResponse:
    """An object representing a response from UPS...will contain status/error info and possibly a list of shipments"""
    shipments = []
    error = None
    
def SendRequest(url, request):
    
    req = Request(url, request)
    response = ''
    try:
        response = urlopen(req)
    except URLError, e:
        if hasattr(e, 'reason'):
            print 'We failed to reach a server.'
            print 'Reason: ', e.reason
        elif hasattr(e, 'code'):
            print 'The server couldn\'t fulfill the request.'
            print 'Error code: ', e.code
        raise
    return response

def CreateAccessRequest( license_number, user_id, psswrd):
    """Generates and returns the etree version of the access request"""
    accessrequest = etree.Element("AccessRequest")
    accessrequest.set(u'{http://www.w3.org/XML/1998/namespace}lang', u'en-US')
    etree.SubElement(accessrequest, "AccessLicenseNumber").text = license_number
    etree.SubElement(accessrequest, "UserId").text = user_id
    etree.SubElement(accessrequest, "Password").text = psswrd

    
    return accessrequest

def sanitize_state( state ):
    if '-' in state:
        return state.split('-')[-1]
    return state
    
def sanitize_field( address, name):
    value = getattr( address, "ship_%s"%name, None)
    return value or getattr( address, "bill_%s"%name, '')
    
    
def CreateServiceRequest(settings,
                         store_contact,
                         origin_contact,
                         origin_address,
                         order, 
                         method = "Rate",
                         description = "Rate Shopping"):
                         
    """Generates and returns the etree version of the service request"""

    items = filter( IShippableLineItem.providedBy, order.shopping_cart.values() )
    
    servicerequest = etree.Element("RatingServiceSelectionRequest")
    request = etree.SubElement(servicerequest, "Request")
    

    #transaction reference
    trans_reference = etree.SubElement(request, "TransactionReference")
    customercontext = etree.SubElement(trans_reference, "CustomerContext").text = 'Rating and Service'
    xpciversion = etree.SubElement(trans_reference, "XpciVersion").text = "1.0"
    
    etree.SubElement(request, "RequestAction").text = "rate"
    etree.SubElement(request, "RequestOption").text = "Shop"
    
    #pickup type
    if getattr( settings, 'pickup_type', None):
        pickuptype = etree.SubElement(servicerequest, "PickupType")
        description = interfaces.UPS_PICKUP_TYPES.getTerm( settings.pickup_type ).token
        etree.SubElement(pickuptype, "Code").text = settings.pickup_type
        etree.SubElement(pickuptype, "Description").text = description

    if getattr( settings, 'customer_classification', None):
        etree.SubElement(
            etree.SubElement( servicerequest, "CustomerClassification"),
            "Code").text = settings.customer_classification
        
    #Shipment
    shipment = etree.SubElement(servicerequest, "Shipment")
    etree.SubElement(shipment, "Description").text = description
    
    #shipment - shipper
    shipment_shipper = etree.SubElement(shipment, "Shipper")
    
    if store_contact.contact_company:
        etree.SubElement(shipment_shipper, "Name").text = store_contact.contact_company
    else:
        etree.SubElement(shipment_shipper, "Name").text = store_contact.store_name
        
    if store_contact.contact_name:
        etree.SubElement(shipment_shipper, "AttentionName").text = store_contact.contact_name 
    
    etree.SubElement(shipment_shipper, "TaxIdentificationNumber")

    if store_contact.contact_phone:
        etree.SubElement(shipment_shipper, "PhoneNumber").text = store_contact.contact_phone
    if store_contact.contact_fax:
        etree.SubElement(shipment_shipper, "FaxNumber").text = store_contact.contact_fax
        
    # required for negotiated rates
    #if settings.shipper_number:
    #    etree.SubElement(shipment_shipper, "ShipperNumber").text = settings.shipper_number
    
    shipper_address = etree.SubElement(shipment_shipper, "Address")
    
    etree.SubElement(shipper_address, "AddressLine1").text = store_contact.contact_address
    etree.SubElement(shipper_address, "AddressLine2").text = store_contact.contact_address2
    etree.SubElement(shipper_address, "AddressLine3")
    etree.SubElement(shipper_address, "City").text = store_contact.contact_city

    etree.SubElement(shipper_address, "StateProvinceCode").text = sanitize_state( store_contact.contact_state )
    etree.SubElement(shipper_address, "PostalCode").text = store_contact.contact_postalcode
    etree.SubElement(shipper_address, "CountryCode").text = store_contact.contact_country
    
    # shipment - shipto    
    shipment_shipto = etree.SubElement(shipment, "ShipTo")
    addr = order.shipping_address
    if addr.ship_same_billing:
        addr = order.billing_address
    
    contact = order.contact_information
    
    etree.SubElement(shipment_shipto, "CompanyName").text = contact.name
    etree.SubElement(shipment_shipto, "AttentionName").text = contact.name
    etree.SubElement(shipment_shipto, "Name").text = contact.name
                     
    if contact.phone_number:
        etree.SubElement(shipment_shipto, "PhoneNumber").text = contact.phone_number
    
    shipto_address = etree.SubElement(shipment_shipto, "Address")
    etree.SubElement(shipto_address, "AddressLine1").text = sanitize_field( addr, 'first_line')
    
    if getattr( addr, 'ship_second_line', None):
        etree.SubElement(shipto_address, "AddressLine2").text = sanitize_field( addr, 'second_line')
        
    etree.SubElement(shipto_address, "City").text = sanitize_field( addr, 'city')
    etree.SubElement(shipto_address, "State").text = sanitize_field( addr, "state" )
    etree.SubElement(shipto_address, "CountryCode").text = sanitize_field( addr, 'country' )
    etree.SubElement(shipto_address, "PostalCode").text = sanitize_field( addr, 'postal_code')
    
    #shipment - shipfrom (same as shipper)
    if origin_contact:
        shipment_shipfrom = etree.SubElement(shipment, "ShipFrom")
        etree.SubElement(shipment_shipfrom, "CompanyName").text = origin_contact.name
        etree.SubElement(shipment_shipfrom, "AttentionName").text = origin_contact.name
        etree.SubElement(shipment_shipfrom, "PhoneNumber").text = origin_contact.phone_number
        #etree.SubElement(shipment_shipfrom, "FaxNumber").text = origin_contact
    
    if origin_address:
        shipfrom_address = etree.SubElement(shipment_shipfrom, "Address")
        etree.SubElement(shipfrom_address, "AddressLine1").text = origin_address.ship_first_line
        etree.SubElement(shipfrom_address, "AddressLine2").text = origin_address.ship_second_line
        etree.SubElement(shipfrom_address, "AddressLine3")
        etree.SubElement(shipfrom_address, "City").text = origin_address.ship_city
        etree.SubElement(shipfrom_address, "StateProvinceCode").text = sanitize_state( origin_address.ship_state )
        etree.SubElement(shipfrom_address, "PostalCode").text = origin_address.ship_postal_code
        etree.SubElement(shipfrom_address, "CountryCode").text = origin_address.ship_country
    
    #Service Code
    if method == "Rate":
        shipment_service = etree.SubElement(shipment, "Service")
        etree.SubElement(shipment_service, "Code").text = str(65)
        
    #payment information
    payment = etree.SubElement(shipment, "PaymentInformation")
    prepaid = etree.SubElement(shipment, "Prepaid")
    
    #Package Information
    total_weight = 0
    for item in items:
        total_weight += float(item.weight) * int(item.quantity)
    
    # UPS only respects one decimal place for weights
    if total_weight > 0 and total_weight < 0.1:
        total_weight = 0.1
    
    package = etree.SubElement(shipment, "Package")
    package_type = etree.SubElement(package, "PackagingType")
    etree.SubElement(package_type, "Code").text = '04' # Generic 'PAK' description
    etree.SubElement( package, "Description").text = "Rate"
    package_weight = etree.SubElement(package, "PackageWeight")
    package_weight_unit = etree.SubElement(package_weight, "UnitOfMeasurement")
    etree.SubElement(package_weight_unit, "Code").text = "LBS"
    etree.SubElement(package_weight, "Weight").text = str( total_weight )
    
    etree.SubElement(shipment, "ShipmentServiceOptions")
    
    return servicerequest


def CreateRequest( settings,
                   store_contact,
                   origin_contact,
                   origin_address,
                   order,
                   pretty=False ):

    """Returns the text version of the xml request"""
    accessreq = CreateAccessRequest( settings.access_key, settings.username, settings.password)
    servicereq = CreateServiceRequest( settings, store_contact, origin_contact, origin_address, order )
    
    xml_text = '<?xml version="1.0"?>' + etree.tostring(accessreq) + '<?xml version="1.0"?>' + etree.tostring(servicereq)
    return xml_text

def FakeResponse( something ):
    """This is to save the devels the pain of ups registering """
    ups_response = UPSResponse()
    ups_response.shipments = []
    shipment = ShippingMethodRate()
    shipment.service_code = "CTRL"
    shipment.service = "ASERVICE"
    shipment.currency = "$"
    shipment.cost = 10
    shipment.days_to_delivery = 20
    shipment.delivery_time = "A lot of days"

    ups_response.shipments.append( shipment )
    shipment1 = ShippingMethodRate()
    shipment1.service_code = "ALT"
    shipment1.service = "ANOTHERSERVICE"
    shipment1.currency = "$"
    shipment1.cost = 20
    shipment1.days_to_delivery = 30
    shipment1.delivery_time = "A lot more of days"

    ups_response.shipments.append( shipment1 )

    return ups_response 

def ParseResponse( root ):
    """extract the shipping options from the response from UPS"""
    ups_response = UPSResponse()
    ups_response.shipments = []
    if root.tag != "RatingServiceSelectionResponse":
        print 'error...RatingServiceSelectionResponse'
        return
    for elem in root:
        if elem.tag == "Response":
            for child in elem:
                if child.tag == "ResponseStatusCode":
                    ups_response.status_code = child.text
                elif child.tag == "ResponseStatusDescription":
                    ups_response.status_desc = child.text
                elif child.tag == "Error":
                    for child2 in child:
                        if child2.tag == "ErrorSeverity":
                            ups_response.error_severity = child2.text
                        elif child2.tag == "ErrorCode":
                            ups_response.error_code = child2.text
                        elif child2.tag == "ErrorDescription":
                            ups_response.error = child2.text
                        elif child2.tag == "MinimumRetrySeconds":
                            ups_response.minimum_retry_seconds = child2.text
                        elif child2.tag == "ErrorLocation":
                            for child3 in child2:
                                if child3.tag == "ErrorLocationElementName":
                                    ups_response.error_location_elem_name = child3.text
                                elif child3.tag == "ErrorLocationElementReference":
                                    ups_response.error_location_elem_ref = child3.text
                                elif child3.tag == "ErrorLocationAttributeName":
                                    ups_response.error_location_atrr_name = child3.text
                        elif child2.tag == "ErrorDigest":
                            ups_response.error_digest = child2.text
        elif elem.tag == "RatedShipment":
            shipment = ParseShipment( elem )
            ups_response.shipments.append( shipment )
    
    return ups_response

def ParseShipment( elem ):
    """grab the info for a single shipment within a response, and add that shipment to the list of all shipments"""
    current_shipment = ShippingMethodRate()
    for child in elem:
        if child.tag == "Service":
            for child2 in child:
                if child2.tag == "Code":
                    current_shipment.service_code = child2.text
                elif child2.tag == "Description":
                    current_shipment.service = child2.text
            if not getattr( current_shipment, 'service'):
                current_shipment.service = \
                    interfaces.UPS_SERVICES.getTerm( current_shipment.service_code ).title
        elif child.tag == "BillingWeight":
            for child2 in child:
                if child2.tag == "UnitOfMeasurement":
                    current_shipment.unit = child2[0].text
                elif child2.tag == "Weight":
                    current_shipment.weight = child2.text
        elif child.tag == "TransportationCharges":
            for child2 in child:
                if child2.tag == "CurrencyCode":
                    current_shipment.transport_charge_currency = child2.text
                elif child2.tag == "MonetaryValue":
                    current_shipment.transport_charge_value = child2.text
        elif child.tag == "ServiceOptionsCharges":
            for child2 in child:
                if child2.tag == "CurrencyCode":
                    current_shipment.service_charge_currency = child2.text
                elif child2.tag == "MonetaryValue":
                    current_shipment.service_charge_value = child2.text
        elif child.tag == "HandlingChargeAmount":
            for child2 in child:
                if child2.tag == "CurrencyCode":
                    current_shipment.handling_charge_currency = child2.text
                elif child2.tag == "MonetaryValue":
                    current_shipment.handling_charge_value = child2.text
        elif child.tag == "TotalCharges":
            for child2 in child:
                if child2.tag == "CurrencyCode":
                    current_shipment.currency = child2.text
                elif child2.tag == "MonetaryValue":
                    current_shipment.cost = float( child2.text )
        elif child.tag == "GuaranteedDaysToDelivery":
            current_shipment.days_to_delivery = child.text
        elif child.tag == "ScheduledDeliveryTime":
            current_shipment.delivery_time = child.text
    return current_shipment


def PrintResponse( response ):
    print 'Response Status Code: %s' % response.status_code
    print 'Response Status Description: %s' % response.status_desc
    if hasattr( response, 'error_code' ):
        print 'Error...severity: %(severity)s, code: %(code)s, description: %(desc)s' % \
        {'severity' : response.error_severity, 'code' : response.error_code, 'desc' : response.error }
    print
    
    #l_services = dict( [ (v,k) for k,v in interfaces.UPS_SERVICES.items() ])
    
    for shipment in response.shipments:
        #print ' Service Code: %s' % ( l_services[shipment.service_code] )
        if hasattr(shipment, 'service_desc'):
            print ' Service Description %s' % shipment.service_desc
        print ' Shipment unit of measurement: %s' % shipment.unit
        print ' Shipment weight: %s' % shipment.weight
        print ' Currency Code: %s' % shipment.currency
        print ' Total Charge: %s' % shipment.cost
        print ' Days to Delivery: %s' % shipment.days_to_delivery
        print ' Delivery Time: %s' % shipment.delivery_time
        print ' Unit : %s '% shipment.unit
        print ' Weight : %s '% shipment.unit        
        print


