from Products.PloneGetPaid.browser.checkout import BaseCheckoutForm, null_condition, BillingInfo, ShipAddressInfo, BillAddressInfo, ContactInfo

from AccessControl import getSecurityManager

from getpaid.wizard import Wizard, ListViewController, interfaces as wizard_interfaces
from getpaid.core import interfaces, options, payment
from getpaid.core.order import Order
from getpaid.wizard import ListViewController

from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from zope import component, schema, interface
from zope.app.event.objectevent import ObjectCreatedEvent
from zope.app.i18n import ZopeMessageFactory as _
from zope.formlib import form

import Acquisition
from Products.PloneGetPaid.browser.widgets import CountrySelectionWidget, StateSelectionWidget, CCExpirationDateWidget
from getpaid.ups.rates import UPSRateService
from cPickle import loads, dumps
from zope.event import notify

from getpaid.ups.interfaces import IUPSRateService

class ShippingForm( BaseCheckoutForm ):

    def update( self ):
        self.setupHiddenFormVariables()

        
class CheckoutController( ListViewController ):

    steps = ['checkout-address-info', 'checkout-select-shipping','checkout-review-pay']
    #steps = ['checkout-address-info','checkout-review-pay']
    
    def getStep( self, step_name ):
        step = component.getMultiAdapter(
                    ( self.wizard.context, self.wizard.request ),
                    name=step_name
                    )
        return step.__of__( Acquisition.aq_inner( self.wizard.context ) )

class CheckoutSelectShipping( BaseCheckoutForm ):
    """
    browser view for collecting credit card information and submitting it to
    a processor.
    """
    
    form_fields = form.Fields( interfaces.IBillingAddress,
                               interfaces.IShippingAddress,
                               interfaces.IUserContactInformation )
    
    form_fields['ship_country'].custom_widget = CountrySelectionWidget
    form_fields['bill_country'].custom_widget = CountrySelectionWidget
    form_fields['ship_state'].custom_widget = StateSelectionWidget
    form_fields['bill_state'].custom_widget = StateSelectionWidget
    
    
    template = ZopeTwoPageTemplateFile("templates/checkout-shiping-method.pt")
    
    
    def getShippingMethods( self ):
        """'checkout-select-shipping'
        Queries the getpaid.ups utility to get the available shipping methods and returns a list
        of them for the template to display and the user to choose among.
        """
        ups_service = UPSRateService()
        available_shipping_methods = ups_service.getRates(self.createOrder())
        return available_shipping_methods

    def setShippingMethods( self ):
        """
        Set the shipping methods chossed by the user
        """
        # "what we do with the shipping method selected?"
        pass
    
    def setUpWidgets( self, ignore_request=False ):
        self.adapters = self.adapters is not None and self.adapters or {}
        
        # grab all the adapters and fields from the entire wizard form sequence (till the current step)
        self.wizard.data_manager['cur_step'] = 'checkout-select-shipping'
        adapters = self.wizard.data_manager.adapters
        adapters.update( self.getSchemaAdapters() )
        fields   = self.wizard.data_manager.fields
        # edit widgets for payment info
        self.widgets = form.setUpEditWidgets(
            self.form_fields.select( *schema.getFieldNames( interfaces.IBillingAddress)),
            self.prefix, self.context, self.request,
            adapters=adapters, ignore_request=ignore_request
            )
        
        # display widgets for bill/ship address
        bill_ship_fields = fields.select( *schema.getFieldNamesInOrder( interfaces.IBillingAddress ) ) + \
                           fields.select( *schema.getFieldNamesInOrder( interfaces.IShippingAddress ) )
                           
        # clear custom widgets.. (typically for edit, we want display)
        for field in bill_ship_fields:
            if field.custom_widget is not None:
                field.custom_widget = None
        
        self.widgets += form.setUpEditWidgets(
            bill_ship_fields,  self.prefix, self.context, self.request,
            adapters=adapters, for_display=True, ignore_request=ignore_request
            )
    def createOrder( self ):
        order_manager = component.getUtility( interfaces.IOrderManager )
        order = Order()
        
        shopping_cart = component.getUtility( interfaces.IShoppingCartUtility ).get( self.context )
        
        # shopping cart is attached to the session, but we want to switch the storage to the persistent
        # zodb, we pickle to get a clean copy to store.
        adapters = self.wizard.data_manager.adapters
                
        order.shopping_cart = loads( dumps( shopping_cart ) )
        order.shipping_address = payment.ShippingAddress.frominstance( adapters[ interfaces.IShippingAddress ] )
        order.billing_address = payment.BillingAddress.frominstance( adapters[ interfaces.IBillingAddress ] )
        order.contact_information = payment.ContactInformation.frominstance( adapters[ interfaces.IUserContactInformation ] )

        order.order_id = self.wizard.data_manager.get('order_id')
        order.user_id = getSecurityManager().getUser().getId()
        notify( ObjectCreatedEvent( order ) )

        return order
    
    def update( self ):
        if not self.adapters:
            self.adapters = self.getSchemaAdapters()
        super( CheckoutSelectShipping, self).update()
    
    def getSchemaAdapters( self ):
        adapters = {}
        adapters[ interfaces.IUserPaymentInformation ] = BillingInfo(self.context)
        return adapters

    @form.action(_(u"Cancel"), name="cancel", validator=null_condition)
    def handle_cancel( self, action, data):
        print "checkoutSelectShiping Cancel >"
        return self.request.response.redirect( self.context.portal_url.getPortalObject().absolute_url() )

    @form.action(_(u"Back"), name="back")
    def handle_back( self, action, data):
        print "checkoutSelectShiping Back >"
        self.next_step_name = wizard_interfaces.WIZARD_PREVIOUS_STEP

    @form.action(_(u"Continue"), name="continue_s")
    def handle_continue_s( self, action, data ):
        print "checkoutSelectShiping Continue >"
        self.setShippingMethods()
        self.next_step_name = wizard_interfaces.WIZARD_NEXT_STEP

    
