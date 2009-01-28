===========
getpaid ups
===========

This modules provides an integration package for getpaid and UPS 
( www.ups.com ). 

Usage
-----

First we need to create an instance of a UPS rating utility and configure 
it with our UPS Account Information. In order to run the unit tests in this
package the values for UPS_USERNAME, UPS_PASSWORD, UPS_ACCESS_KEY need to
be setup in the shell/process environment.

Also note that rates.py currently returns FakeResponse( ) to these requests.
To get a real response from the server, simply comment that line (#66) out.

   >>> from getpaid.ups import interfaces
   >>> from getpaid.ups.rates import UPSRateService
   >>> ups = UPSRateService()
   >>> ups.username = UPS_USERNAME
   >>> ups.password = UPS_PASSWORD
   >>> ups.access_key = UPS_ACCESS_KEY
   >>> ups.pickup_type = '01'
   
We need to explicitly specify which ups services we're allowing for a store.

   >>> ups.services = interfaces.UPS_SERVICES.by_value.keys()

Origin Information
------------------

We also need to configure our store to setup a default origin location for
packages to originate from. for brevity, we've done configured the store 
settings in the test setup with a san francisco address.

Creating an Order to Ship
-------------------------

Let's create an order with some items we'd like to have shipped.

  >>> from getpaid.core import order, item, cart
  >>> myorder = order.Order()
  >>> myorder.shopping_cart = mycart = cart.ShoppingCart()
  >>> mycart
  <getpaid.core.cart.ShoppingCart object at ...>  

  >>> line_item = item.ShippableLineItem()
  >>> line_item.item_id = "sku-code-1"
  >>> line_item.quantity = 2
  >>> line_item.weight = 5.5
  >>> mycart[ line_item.item_id ] = line_item

Destination Information
-----------------------

We need some additional information for an order to successfully
process it, first some contact information:

  >>> from getpaid.core import payment
  >>> user_contact = payment.ContactInformation()
  >>> user_contact.name = "John Smith"
  >>> user_contact.email = "js@example.org"
  >>> user_contact.phone_number = '7033291513'
  >>> myorder.contact_information = user_contact

and of course a place to ship to:

  >>> ship_address = payment.ShippingAddress()
  >>> ship_address.ship_same_billing = False
  >>> ship_address.ship_first_line = '2702 Occidental Dr'
  >>> ship_address.ship_city = 'Vienna'
  >>> ship_address.ship_state = "VA"
  >>> ship_address.ship_country = "US"
  >>> ship_address.ship_postal_code = '22180'
  >>> myorder.shipping_address = ship_address

Getting Shipping Options
------------------------

Now we can query UPS to find out the various services, delivery windows, and
 prices that UPS can offer for transit.
 
  >>> results = ups.getRates( myorder )
  >>> results.shipments.sort( lambda x,y:cmp(x.cost,y.cost) )
  >>> methods = results.shipments  
  >>> len(methods)
  6

Prices will vary over time, for testing purposes, we sort and compare
the expected serices types by cost (low to high)

  >>> methods[0].service
  u'UPS Ground'
  >>> methods[1].service
  u'UPS Three Day Select'
  >>> methods[2].service
  u'UPS 2nd Day Air'
  >>> methods[3].service
  u'UPS Next Day Air Saver'

Failure Modes
-------------

if the store shipping information isn't setup correctly we get a type
error asking to look at the store settings.

  >>> from zope.component import getUtility
  >>> from getpaid.core.interfaces import IStoreSettings
  >>> settings = getUtility( IStoreSettings )
  >>> settings.contact_state = ""
  >>> ups.getRates( myorder )
  Traceback (most recent call last):
  ...
  TypeError: Invalid Store Address Settings in Store Admin


TODO: Test

status available on results objects

  


