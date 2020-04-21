# NOTES on API: 
# - This code is more or less a copy from the views_terminal.py file. I'm not sure
# what large parts of the models do, so better to play it safe.
#
# - Security is handled with a token that's set locally within the Electron App's ENV 
# and in the server. Currently, I'm just letting all requests from any origin go to a
# handler which will check for the existence of the correct token and refuse the
# request otherwise. There's probably a better way of doing this with cookies or something...

# Copied the imports from views_terminal.py entirely.
from pyramid.events import subscriber
from pyramid.events import BeforeRender
from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render
from pyramid.renderers import render_to_response
from pyramid.response import Response
from pyramid.view import view_config, forbidden_view_config

from pyramid.i18n import TranslationStringFactory, get_localizer
_ = TranslationStringFactory('betty')

from sqlalchemy.sql import func
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm.exc import NoResultFound

from .models import *
from .models.model import *
from .models import user as __user
from .models.user import User
from .models.item import Item
from .models.box import Box
from .models.transaction import Transaction, BTCDeposit, PurchaseLineItem
from .models.account import Account, VirtualAccount, CashAccount
from .models.event import Event
from .models.announcement import Announcement
from .models.btcdeposit import BtcPendingDeposit
from .models.pool import Pool
from .models.tag import Tag
from .models.ephemeron import Ephemeron
from .models.badscan import BadScan

from .utility import user_password_reset
from .utility import send_email

from pyramid.security import Allow, Everyone, remember, forget

import chezbetty.datalayer as datalayer
import transaction

import math


# debt threshold at which emails start to be sent
global debtor_email_theshold
debtor_email_theshold = Decimal(-5.00)
# token used to verify requests to api
global token 
token = 'ABC123'

# custom exception
class DepositException(Exception):
    pass




# fetch data used to render /login
@view_config(
    route_name='api_terminal_login',
    renderer='json',
)
def api_terminal_login(request):
    if request.method == 'OPTIONS':
        request.response.headers.update(options_headers)
        return {}

    request.response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST',
    })

    if request.method != 'POST':
        request.response.status = 400
        return {'error': 'request-not-post'}

    body = request.json_body

    if body['token'] != token:
        request.response.status = 401
        return {}
    
    announcements = []
    for announcement in Announcement.all_enabled():
        announcements.append(announcement.announcement)

    return {
        'announcements': announcements,
        'debt': str(User.get_amount_owed()),
    }


# fetches user data. what this returns should be pushed by the electron app
# to /terminal route, then used to render that page. check vue-router documentation
# for how that works
def terminal_initial(user):
    # if cash was added before a user was logged in, credit that now
    # note, i think that this feature is currently disabled. would have
    # to check with admins to know for sure...

    deposit = None
    # TODO ALERT commenting this next bit out to avoid calling ephemeron
    #in_flight_deposit = Ephemeron.from_name('deposit')
    #if in_flight_deposit:
    #    amount = Decimal(in_flight_deposit.value)
    #    deposit = datalayer.deposit(user, user, amount)
    #    DBSession.delete(in_flight_deposit)

    # determine initial wall-of-shame fee (if applicable)
    purchase_fee_percent = Decimal(0)
    if user.balance <= Decimal('-5.00') and user.role != 'administrator':
        purchase_fee_percent = 5 + (math.floor((user.balance + 5) / -5) * 5)

    # figure out if any purchasing pools can be used to pay for this purchase
    purchase_pools = []
    for pool in Pool.all_by_owner(user, True):
        if pool.balance > (pool.credit_limit * -1):
            purchase_pools.append(pool)

    for pu in user.pools:
        if pu.enabled and pu.pool.enabled and pu.pool.balance > (pu.pool.credit_limit * -1):
            purchase_pools.append(pu.pool)

    # get the list of tags that have items without barcodes in them
    # check item_tag.py for func defs on tag functions
    tags_with_nobarcode_items = Tag.get_tags_with_nobarcode_items()

    # pull list of recently purchased items
    user_recent_items = user.get_recent_items(limit=5)

    print("--------------------==-------------1")
    temp = []
    for i in Item.all():
        print(i)
        item = {
            "id" : i.id,
            'name'            : i.name,
            'barcode'         : i.barcode,
            'cost'            : str(i.price),
            'wholesale'       : str(i.wholesale),
            'bottle_dep'      : i.bottle_dep,
            'sales_tax'       : i.sales_tax,
            'in_stock'        : i.in_stock,
            'enabled'         : i.enabled,
        }
        print(item)
        temp.append(item)
        print(temp)


            
    
    print("--------------------==-------------2")

    # return terminal data
    return {
        'user_name': user.name,
        'user_balance': str(user.balance),
        'user_umid': user.umid,
        'user_role': user.role,
        'user_recent_items': str(user_recent_items),
        'purchase_pools': purchase_pools,
        'purchase_fee_percent': str(purchase_fee_percent),
        'good_standing_discount': str(round((datalayer.good_standing_discount) * 100)),
        'good_standing_volunteer_discount': str(round((datalayer.good_standing_volunteer_discount) * 100)),
        'good_standing_manager_discount': str(round((datalayer.good_standing_manager_discount) * 100)),
        'admin_discount': str(round((datalayer.admin_discount) * 100)),
        'tags_with_nobarcode_items': tags_with_nobarcode_items,
        'nobarcode_notag_items': Item.get_nobarcode_notag_items(),
        'deposit': deposit,
        'all_items': temp
    }

    # note: testing a few of these routes is very hard because i'm not sure what they reference / return
    # i'll document what I can, but e.g. there are no existing purchasing pools in the db and i don't know 
    # how to create one, so i can't document what will be returned in 'purchase_pools'.




@view_config(
    route_name='api_terminal_get_items',
    request_method='GET',
    renderer='json',
)
def api_terminal_get_items(request):

    # allow cors request
    request.response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
    })
    print("----------------")
    print(Item.get_nobarcode_notag_items())
    print("----------------")
    print(Tag.get_tags_with_nobarcode_items())
    print("----------------")

    return {
        Tag.get_tags_with_nobarcode_items()
    }

# route to validate umid
# params: umid (str), scanned (bool), token (str)
# returns: 200 on success returning what terminal_initial fetches,
# 400 with error list on failure proccessing umid, 401 on token mismatch
#   -> on success, terminal should redirect to /terminal 
#   -> on failure, terminal should clear umid and prompt user as needed
@view_config(
    route_name='api_terminal_umid',
    request_method='POST',
    renderer='json',
)
def api_terminal_umid(request):
    print("api_terminal_umid start")

    req_body = request.json_body


    # check token match
    if req_body['token'] != token:
        request.response.status = 401
        return {}
    print("token accepted")

    # allow cors request
    #request.response.headers.update({
    #    'Access-Control-Allow-Origin': '*',
    #    'Access-Control-Allow-Methods': 'POST',
    #})

    # mcard scanned
    if req_body['scanned']:
        try:
            # check length before trying to fetch umid
            if len(req_body['umid']) != 8:
                raise __user.InvalidUserException()

            # get user, create if needed
            with transaction.manager:
                user = User.from_umid(req_body['umid'], create_if_never_seen=True)
                print(user)
            # add user to database / fetch user data
            user = DBSession.merge(user)
            print("------")
            print(user)
            # return special error if user is disabled
            if not user.enabled:
                request.response.status = 400
                return {'errors': {'user-not-enabled': 'This user is not enabled. Please contact us.'}}

            # unarchive user if previously archived
            if user.archived:
                if user.archived_balance != 0:
                    datalayer.adjust_user_balance(
                        user,
                        user.archived_balance,
                        'Reinstated archived user.',
                        request.user
                    )
                user.balance = user.archived_balance
                user.archived = False

            # umid checks out, fetch data needed to display terminal
            try:
                request.response.status = 200
                return terminal_initial(user)

            except:
                request.response.status = 400
                return {'errors': {'terminal-fetch-failed': 'Something went wrong fetching initial terminal data.'}}

        except:
            request.response.status = 400
            return {'errors': {'user-not-found': 'Failed to read UMID. Try swiping again.'}}

    # umid entered w/ keypad
    else:
        try:
            # try to fetch user, will throw exception on failure
            user = User.from_umid(req_body['umid'])
            print("keypad")
            print(user)
            # check user is valid
            if user.role == 'serviceaccount':
                raise User.InvalidUserException

            # umid checks out, fetch data needed to display terminal
            try:
                request.response.status = 200
                print("returning from umid api call")
                return terminal_initial(user)

            except:
                request.response.status = 400
                return {'errors': {'terminal-fetch-failed': 'Something went wrong fetching initial terminal data.'}}

        except:
            # tell terminal there was an error
            request.response.status = 400
            return {'errors': {'mcard-keypad-error': 'The UMID was invalid or has not been registered prior.'}}


# handle deposits into the bill acceptor. a deposit should be triggered by a listener
# function related to node-hid or something similar. 
# params: umid (str), token(str), amount (str), method (str)
# returns: 200 with some details on success, 400 on failure w/ errors
#   -> if successful when logged in, update balance
#   -> if successful when logged out, idk wtf happens. seems like it requires a manual fix
@view_config(
    route_name='api_terminal_deposit',
    request_method='POST',
    renderer='json',
)
def api_terminal_deposit(request):
    req_body = request.json_body

    # check token match
    if req_body['token'] != token:
        request.response.status = 401
        return {}

    # allow cors request
    request.response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST',
    })

    try:
        if req_body['umid'] == '':
            # User was not logged in when deposit was made. We store
            # this deposit temporarily and give it to the next user who
            # logs in.
            user = None
        else:
            user = User.from_umid(req_body['umid'])

        amount = Decimal(req_body['amount'])
        method = req_body['method']

        if amount <= 0.0:
            raise DepositException('Deposit amount must be greater than $0.00')
        
        # Now check the deposit method. We trust anything that comes from the
        # bill acceptor, but double check a manual deposit
        if method == 'manual':
            # Check if the deposit amount is too great.
            if amount > 2.0:
                # Anything above $2 is blocked
                raise DepositException('Deposit amount of ${:,.2f} exceeds the limit'.format(amount))

        elif method == 'acceptor':
            # Any amount is OK
            pass

        else:
            raise DepositException('"{}" is an unknown deposit type'.format(method))

        # At this point the deposit can go through
        ret = {}

        if user:
            response.response.status = 200
            deposit = datalayer.deposit(user, user, amount, method != 'manual')
            ret['type'] = 'user'
            ret['amount'] = float(deposit['amount'])
            ret['event_id'] = deposit['event'].id
            ret['user_balance'] = float(user.balance)

        else:
            # No one was logged in. Need to save this temporarily
            # total_stored = datalayer.temporary_deposit(amount);
            # ret['type'] = 'temporary'
            # ret['new_amount'] = float(amount)
            # ret['total_amount'] = float(total_stored)

            print('GOT NON-LOGGED IN DEPOSIT')
            print('GOT NON-LOGGED IN DEPOSIT')
            print('GOT NON-LOGGED IN DEPOSIT')
            print('AMOUNT: {}'.format(amount))
            print('IGNORING THIS FOR NOW.')
            request.response.status = 200           
            ret['error'] = 'Must be logged in to deposit'

        return ret

    except __user.InvalidUserException as e:
        request.session.flash('Invalid user error. Please try again.', 'error')
        return {'error': 'Error finding user.'}

    except ValueError as e:
        return {'error': 'Error understanding deposit amount.'}

    except DepositException as e:
        return {'error': str(e)}

    except Exception as e:
        return {'error': str(e)}


# handles going from barcode to item (the db interactions needed for that)
def get_item_from_barcode(barcode):
    try:
        item = Item.from_barcode(barcode)
    except:
        # Could not find the item. Check to see if the user scanned a box
        # instead. This could lead to two cases: a) the box only has 1 item in it
        # in which case we just add that item to the cart. This likely occurred
        # because the individual items do not have barcodes so we just use
        # the box. b) The box has multiple items in it in which case we throw
        # an error for now.
        try:
            box = Box.from_barcode(barcode)
            if box.subitem_number == 1:
                item = box.items[0].item
            else:
                return 'Cannot add that entire box to your order. Please scan an individual item.'
        except:
            badscan = BadScan(barcode)
            DBSession.add(badscan)
            DBSession.flush()

            return 'Could not find that item.'

    if not item.enabled:
        return 'That product is not currently for sale.'

    return item


# Get details about an item based on a barcode. This can be used to add to a
# cart or as a price check.
# params: token (str), barcode (str)
# returns: 200 with item info on success, 400 with errors on failure.
@view_config(
    route_name='api_terminal_item_barcode',
    request_method='POST',
    renderer='json',
)
def api_terminal_item_barcode(request):
    req_body = request.json_body

    # check token match
    if req_body['token'] != token:
        request.response.status = 401
        return {}
    
    # allow cors request
    request.response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST',
    })

    item = get_item_from_barcode(req_body['barcode'])

    if type(item) is str:
        request.response.status = 400
        return {'error': item}

    request.response.status = 200
    return {
        'id': item.id,
        'name': item.name,
        'price': float(item.price),
    }


# Get details about an item based on an item ID. This can be used to add to a
# cart or as a price check.
# params: token (str), item_id (str)
# returns: 200 with item info on success, 400 with errors on failure.
@view_config(
    route_name='api_terminal_item_id',
    request_method='POST',
    renderer='json',
)
def api_terminal_item_id(request):
    req_body = request.json_body

    # check token match
    #if req_body['token'] != token:
        #request.response.status = 401
        #return {}

    # allow cors request
    request.response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST',
    })

    try:
        item = Item.from_id(req_body['item_id'])

    except:
        request.response.status = 400
        return {'error': 'Could not find that item.'}

    if not item.enabled:
        request.response.status = 400
        return {'error': 'That product is not currently for sale.'}
    print('\n' + str(item) + '\n')
    request.response.status = 200
    return {
        'id': item.id,
        'name': item.name,
        'price': float(item.price),
    }


# Make a purchase from the terminal.
# params: token (str), umid (str), pool_id (int/str, IF SELECTED), item(s)_id (int/str), item(s)_quantity (int)
# returns: 200 with order summary, new balance on success. 400 with errors if not
@view_config(
    route_name='api_terminal_purchase',
    request_method='POST',
    renderer='json',
)
def api_terminal_purchase(request):
    req_body = request.json_body

    # check token match
    if req_body['token'] != token:
        request.response.status = 401
        return {}

    # allow cors request
    request.response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST',
    })

    try:
        user = User.from_umid(req_body['umid'])

        ignored_keys = ['umid', 'pool_id']

        # Bundle all purchase items
        items = {}
        for item_id, quantity in req_body.items():
            if item_id in ignored_keys:
                continue
            item = Item.from_id(int(item_id))
            items[item] = int(quantity)

        # What should pay for this?
        # Note: should do a bunch of checking to make sure all of this
        # is kosher. But given our locked down single terminal, we're just
        # going to skip all of that.
        if 'pool_id' in req_body:
            pool = Pool.from_id(int(req_body['pool_id']))
            purchase = datalayer.purchase(user, pool, items)
        else:
            purchase = datalayer.purchase(user, user, items)

        # Create a order complete view
        order = {'total': purchase.amount,
                 'discount': purchase.discount,
                 'items': []}
        for subtrans in purchase.subtransactions:
            item = {}
            item['name'] = subtrans.item.name
            item['quantity'] = subtrans.quantity
            item['price'] = subtrans.item.price
            item['total_price'] = subtrans.amount
            order['items'].append(item)

        if purchase.fr_account_virt_id == user.id:
            account_type = 'user'
            pool = None
        else:
            account_type = 'pool'
            pool = Pool.from_id(purchase.fr_account_virt_id)

        # Email the user if they are currently in debt
        if float(user.balance) < debtor_email_theshold:
            send_email(
                TO=user.uniqname+'@umich.edu',
                SUBJECT='Please Pay Your Chez Betty Balance',
                body=render('templates/terminal/email_user_in_debt.jinja2',
                {'user': user})
            )

        summary = {
            'user': user,
            'event': purchase.event,
            'order': order,
            'transaction': purchase,
            'account_type': account_type,
            'pool': pool
        }

        # Return the committed transaction ID
        request.response.status = 200
        return {
            'order_table': summary,
            'user_balance': float(user.balance)
        }

    except __user.InvalidUserException as e:
        request.response.status = 400
        return {'error': get_localizer(request).translate(_('invalid-user-error',
                           default='Invalid user error. Please try again.'))
               }

    except ValueError as e:
        request.response.status = 400
        return {'error': 'Unable to parse Item ID or quantity'}

    except NoResultFound as e:
        # Could not find an item
        request.response.status = 400
        return {'error': 'Unable to identify an item.'}


# Delete a just completed purchase.
# params: token (string), umid (str), event_id(str / int)
# returns: new user balance or errors
@view_config(
    route_name='api_terminal_purchase_delete',
    request_method='POST',
    renderer='json',
)
def api_terminal_purchase_delete(request):
    req_body = request.json_body

    # check token match
    if req_body['token'] != token:
        request.response.status = 401
        return {}

    # allow cors request
    request.response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST',
    })

    try:
        user = User.from_umid(req_body['umid'])
        old_event = Event.from_id(req_body['old_event_id'])

        if old_event.type != 'purchase' or \
           old_event.transactions[0].type != 'purchase' or \
           (old_event.transactions[0].fr_account_virt_id != user.id and \
            old_event.user_id != user.id):
           # Something went wrong, can't undo this purchase
           raise DepositException('Cannot undo that purchase')

        # Now undo old deposit
        datalayer.undo_event(old_event, user)

        request.response.status = 200
        return {'user_balance': float(user.balance)}

    except __user.InvalidUserException as e:
        request.response.status = 400
        return {'error': 'Invalid user error. Please try again.'}

    except DepositException as e:
        request.response.status = 400
        return {'error': str(e)}
