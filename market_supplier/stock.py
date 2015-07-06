# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010, 2014 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import openerp
from openerp import models, fields, api
from openerp import SUPERUSER_ID as SI
from openerp.addons.saas_utils import connector
from openerp.exceptions import ValidationError


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = 'stock.picking'

    def get_commercial_invoice(self, cr, uid, ids, context=None):
        picking = self.browse(cr, uid, ids[0])
        order_obj = self.pool.get('sale.order')
        order_ids = order_obj.search(cr, uid, [('name', '=', picking.origin)])
        if order_ids:
            order = order_obj.browse(cr, uid, order_ids[0])
            ci = self.pool.get('commercial.invoice')
            invoice = ci.get_commercial_invoice_from_order(cr, uid, order)
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'commercial.invoice',
                'res_id': invoice.id
            }
