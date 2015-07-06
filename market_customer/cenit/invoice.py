# -*- coding: utf-8 -*-
import openerp
from openerp import models
from openerp.osv import fields
from openerp.addons.market_product.cenit.invoice import AccountInvoice as AI


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = 'account.invoice'
    _columns = {
        'billing_address': fields.function(AI._get_company, method=True,
                                           fnct_inv=AI._set_company,
                                           type='char', priority=1)
    }
