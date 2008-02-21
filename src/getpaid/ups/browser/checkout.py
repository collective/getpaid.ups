"""
$Id: $
"""

import Acquisition
from AccessControl import getSecurityManager
from cPickle import loads, dumps

from zope import component, schema
from zope.app.i18n import ZopeMessageFactory as _
from zope.formlib import form

from getpaid.core import interfaces, options, payment
from getpaid.core.order import Order
from getpaid.ups.interfaces import IUPSRateService, IShippingMethodRate
from getpaid.wizard import ListViewController, interfaces as wizard_interfaces

from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.PloneGetPaid.browser import checkout

class CheckoutController( ListViewController ):

    conditions = {'checkout-select-shipping' : 'checkShippableCart'}
    steps = [ 'checkout-address-info',
              'checkout-select-shipping',
              'checkout-review-pay']

    def checkShippableCart( self ):
        cart_utility = component.getUtility( interfaces.IShoppingCartUtility )
        cart = cart_utility.get( self.wizard.context )
        return bool( filter(  interfaces.IShippableLineItem.providedBy, cart.values() ) )
                 
    def getNextStepName( self, step_name ):
        step_name = super( CheckoutController, self).getNextStepName( step_name )
        condition_method = self.conditions.get( step_name )
        if not condition_method:
            return step_name
        condition = getattr( self, condition_method )
        if condition():
            return step_name
        return self.getNextStepName( step_name )

    def getStep( self, step_name ):
        step = component.getMultiAdapter(
                    ( self.wizard.context, self.wizard.request ),
                    name=step_name
                    )
        return step.__of__( Acquisition.aq_inner( self.wizard.context ) )
    
class ShippingRate( options.PropertyBag ):
    title = "Shipping Rate"
    
ShippingRate.initclass( IShippingMethodRate )

class CheckoutSelectShipping( checkout.BaseCheckoutForm ):
    """
    browser view for collecting credit card information and submitting it to
    a processor.
    """

    form_fields = form.Fields( IShippingMethodRate )
    
    #form_fields = form.Fields(IShippingMethodRate)
    #form_fields['shipping_rate'].custom_widget = StateSelectionWidget
    #form_fields['shipping_price'].custom_widget = StateSelectionWidget

    template = ZopeTwoPageTemplateFile("templates/checkout-shiping-method.pt")
    shipping_methods = {}


    def getShippingMethods( self ):
        """
        Queries the getpaid.ups utility to get the available shipping methods and returns a list
        of them for the template to display and the user to choose among.
        """
        ups_service = component.getUtility( IUPSRateService )
        available_shipping_methods = ups_service.getRates( self.createTransientOrder() )
        for method in available_shipping_methods:
            self.shipping_methods[method.service_code] = method
        return available_shipping_methods

    def setShippingMethods( self, data ):
        """
        Set the shipping methods chosen by the user
        """
        # "what we do with the shipping method selected?"
        # set it in the request, so that we can restore it in the
        # print self.shipping_rate[data]
        pass

    def setUpWidgets( self, ignore_request=False ):
        self.adapters = self.adapters is not None and self.adapters or {}

        # grab all the adapters and fields from the entire wizard form sequence (till the current step)
        adapters = self.getSchemaAdapters()
        self.widgets = form.setUpEditWidgets(
            self.form_fields.select( *schema.getFieldNames(IShippingMethodRate)),
            self.prefix, self.context, self.request,
            adapters=adapters, ignore_request=ignore_request
            )
        

    def createTransientOrder( self ):
        order_manager = component.getUtility( interfaces.IOrderManager )
        order = Order()
        
        shopping_cart = component.getUtility( interfaces.IShoppingCartUtility ).get( self.context )
        
        # shopping cart is attached to the session, but we want to switch the storage to the persistent
        # zodb, we pickle to get a clean copy to store.
        adapters = self.wizard.data_manager.adapters
        
        if not filter(interfaces.IShippableLineItem.providedBy, shopping_cart.values() ): 
            raise SyntaxError( "No Shippable Items")

        order.shopping_cart = loads( dumps( shopping_cart ) )
        order.shipping_address = payment.ShippingAddress.frominstance( adapters[ interfaces.IShippingAddress ] )
        order.billing_address = payment.BillingAddress.frominstance( adapters[ interfaces.IBillingAddress ] )
        order.contact_information = payment.ContactInformation.frominstance( adapters[ interfaces.IUserContactInformation ] )

        order.order_id = self.wizard.data_manager.get('order_id')
        order.user_id = getSecurityManager().getUser().getId()

        return order
    
    def update( self ):
        if not self.adapters:
            self.adapters = self.getSchemaAdapters()
        super( CheckoutSelectShipping, self).update()
    
    def getSchemaAdapters( self ):
        adapters = {}
        adapters[ IShippingMethodRate ] = ShippingRate()
        return adapters

    @form.action(_(u"Cancel"), name="cancel", validator=checkout.null_condition)
    def handle_cancel( self, action, data):
        return self.request.response.redirect( self.context.portal_url.getPortalObject().absolute_url() )

    @form.action(_(u"Back"), name="back")
    def handle_back( self, action, data, validator=checkout.null_condition):
        self.next_step_name = wizard_interfaces.WIZARD_PREVIOUS_STEP

    @form.action(_(u"Continue"), name="continue")
    def handle_continue( self, action, data ):
        self.setShippingMethods( data )
        self.next_step_name = wizard_interfaces.WIZARD_NEXT_STEP

    
