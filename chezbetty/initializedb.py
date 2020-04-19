import os
import sys
import transaction

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from pyramid.scripts.common import parse_vars


import chezbetty.models.account as account
from chezbetty.models.item import Item
from chezbetty.models.user import User
from chezbetty.models.vendor import Vendor
from chezbetty.models.box import Box
from chezbetty.models.request import Request
from chezbetty.models.item_vendor import ItemVendor
from chezbetty.models.box_vendor import BoxVendor
from chezbetty.models.box_item import BoxItem
from chezbetty.models.announcement import Announcement
from chezbetty.models.model import *
from chezbetty.models.transaction import *
from chezbetty.models.btcdeposit import BtcPendingDeposit
from chezbetty.models.receipt import Receipt
from chezbetty.models.ephemeron import *


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> [var=value]\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    options = parse_vars(argv[2:])
    setup_logging(config_uri)
    settings = get_appsettings(config_uri, options=options)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)

    with transaction.manager:
        # Setup a few initial items
        DBSession.add(Item(
           "Nutrigrain Raspberry",
           "038000358210",
           14.37,
           0.47,
           False,
           False,
           3,
           True
        ))
        DBSession.add(Item(
           "Clif Bar: Chocolate Chip",
           "722252100900",
           1.25,
           1.17,
           False,
           False,
           12,
           True
        ))
        DBSession.add(Item(
           "Clif Bar: Crunchy Peanut Butter",
           "722252101204",
           1.25,
           1.14,
           False,
           False,
           11,
           True
        ))
        coke = Item(
            "Coke (12 oz)",
            "04963406",
            0.42,
            0.37,
            True,
            False,
            8,
            True
        )
        DBSession.add(coke)

        # Add a test box
        coke_box = Box(
                "Coke 32 pack", # name
                "049000042511", # barcode
                True,           # bottle deposit
                False,          # sales tax
                32.00,          # wholesale
                # enabled implicit True
                )
        DBSession.add(coke_box)
        DBSession.flush()
        DBSession.add(BoxItem(coke_box, coke, 32, 100))


        ## users
        ## def __init__(self, uniqname, umid, name):
        # Add the betty user
        DBSession.add(coke)
        user = User(
               "betty",
               "00000000",
               "Betty"
               )
        user.role = "serviceaccount"
        user.password = "chezbetty"
        DBSession.add(user)

        # Add an admin user
        user = User(
               "admin",
               "99999999",
               "Administrator"
               )
        user.role = "administrator"
        user.password = "admin"
        DBSession.add(user)        

        # Init the accounts we need
        account.get_virt_account("chezbetty")
        account.get_cash_account("cashbox")
        account.get_cash_account("safe")
        account.get_cash_account("chezbetty")
        account.get_cash_account("btcbox")

        # Add a user
        user = User(
               "user",
               "11111111",
               "User"
               )
        user.role = "user"
        user.password = "user"
        DBSession.add(user)

if __name__ == "__main__":
    main()
