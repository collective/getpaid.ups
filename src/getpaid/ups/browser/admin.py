"""
$Id: $
"""
import StringIO, csv, time

from zope import component
from zope.app import zapi
from zope.formlib import form

from getpaid.ups import interfaces
from getpaid.ups.interfaces import _

from getpaid.core import interfaces as coreInterfaces

from ore.viewlet import core

from Products.PloneGetPaid.browser.base import EditFormViewlet
from Products.PloneGetPaid.browser.widgets import SelectWidgetFactory
from Products.PloneGetPaid.interfaces import ICountriesStates
from Products.PloneGetPaid.vocabularies import TitledVocabulary

from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

class UPSSettings( EditFormViewlet ):
    
    form_name = _(u"UPS Settings")
    form_description = _(u"Configuration of UPS Shipping")
    form_fields = form.Fields( interfaces.IUPSSettings )
    form_fields['services'].custom_widget = SelectWidgetFactory
    prefix = "ups"
    
    def setUpWidgets( self, ignore_request=False ):
        self.adapters = { interfaces.IUPSSettings : component.getUtility( interfaces.IShippingRateService, name="ups") }
        self.widgets = form.setUpEditWidgets(
            self.form_fields, self.prefix, self.context, self.request,
            adapters=self.adapters, ignore_request=ignore_request
            )


def getAddressInfo(order,field):
    if not coreInterfaces.IShippableOrder.providedBy( order ):
        return "N/A"
    utility = zapi.getUtility(ICountriesStates)
    vocab_countries = TitledVocabulary.fromTitles(utility.countries)
    vocab_states = TitledVocabulary.fromTitles(utility.states())
    infos = order.shipping_address
    #Check if the shipping info is the same that the billing one and add the resulting one
    if infos.ship_same_billing:
        infos = order.billing_address
        order_info= {'name': infos.bill_name,
                'address': "%s %s" % (infos.bill_first_line or "" , infos.bill_second_line or ""),
                'city': infos.bill_city,
                'country': vocab_countries.getTerm(infos.bill_country).title,
                'state': infos.bill_state.split("-").pop(),
                'postal_code': infos.bill_postal_code}

    else:
        order_info= {'name': infos.ship_name,
                'address': "%s %s" % (infos.ship_first_line or "", infos.ship_second_line or ""),
                'city': infos.ship_city,
                'country': vocab_countries.getTerm(infos.ship_country).title,
                'state': infos.ship_state.split("-").pop(),
                'postal_code': infos.ship_postal_code}
    #Add the contact information
    contact = order.contact_information
    order_info['contact_name'] =  contact.name
    order_info['email'] = contact.email
    order_info['phone'] = contact.phone_number
    #Finally the shipment info
    #Total Weight
    totalShipmentWeight = 0
    for eachProduct in order.shopping_cart.values():
        if coreInterfaces.IShippableLineItem.providedBy( eachProduct ):
            weightValue = eachProduct.weight * eachProduct.quantity
            totalShipmentWeight += weightValue
    order_info['weight'] = totalShipmentWeight
    #Service type
    service = component.queryUtility( coreInterfaces.IShippingRateService,
                                          order.shipping_service )
    order_info['service'] = service.getMethodName( order.shipping_method )



    return '%s' % order_info[field]

class OrderCSVWorldShipComponent( core.ComponentViewlet ):

    template = ZopeTwoPageTemplateFile('templates/orders-export-worldship-csv.pt')
    
    order = 4

    def render( self ):
        return self.template()

    @form.action(_(u"Export Search"))
    def export_search( self, action, data ):

        search = self.manager.get('orders-search')
        
        io = StringIO.StringIO()
        writer = csv.writer( io )
        
        writer.writerow( ["OrderNumber", 
                        "CompanyorName",
                        "Attention", 
                        "Street",
                        "RoomFloorAddress2",
                        "DepartmentAddress3",  
                        "City",
                        "StateProv",
                        "PostalZIPCode",
                        "Country", 
                        "Telephone",
                        "FaxNumber",  
                        "ResidentialIndicator",
                        "ShipNotifyByEmail",
                        "EMailAddress",
                        "Weight",
                        "ServiceType"])


        field_getters = []
        #OrderNumber
        field_getters.append(lambda x,y: x.order_id)
        #CompanyorName
        field_getters.append(lambda x,y: getAddressInfo(x,'name'))
        #Attention
        field_getters.append(lambda x,y: " " )
        #Street
        field_getters.append(lambda x,y: getAddressInfo(x,'address'))
        #RoomFloorAddress2
        field_getters.append(lambda x,y: " ")
        #DepartmentAddress3
        field_getters.append(lambda x,y: " ")
        #City
        field_getters.append(lambda x,y: getAddressInfo(x,'city'))
        #StateProv
        field_getters.append(lambda x,y: getAddressInfo(x,'state'))
        #PostalZIPCode
        field_getters.append(lambda x,y: getAddressInfo(x,'postal_code'))
        #Country
        field_getters.append(lambda x,y: getAddressInfo(x,'country'))
        #Telephone
        field_getters.append(lambda x,y: getAddressInfo(x,'phone'))
        #FaxNumber
        field_getters.append(lambda x,y: " ")
        #ResidentialIndicator
        field_getters.append(lambda x,y: "Y")
        #ShipNotifyByEmail
        field_getters.append(lambda x,y: "Y")
        #EMailAddress
        field_getters.append(lambda x,y: getAddressInfo(x,'email'))
        #Weight
        field_getters.append(lambda x,y: getAddressInfo(x,'weight'))
        #Service Type
        field_getters.append(lambda x,y: getAddressInfo(x,'service'))

        for order in search.results:
            writer.writerow( [getter( order, None ) for getter in field_getters ] )

        # um.. send to user, we need to inform our view, to do the appropriate thing
        # since we can't directly control the response rendering from the viewlet
        self._parent._download_content = ('text/csv',  io.getvalue(), 'WorldShipOrderExport')
 

