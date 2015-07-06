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

from openerp import models, fields, SUPERUSER_ID
from openerp.addons.market_product import mixin, utils


class StockInvoiceOnshipping(models.TransientModel):
    _name = 'stock.invoice.onshipping'
    _inherit = 'stock.invoice.onshipping'

    quantity_ids = fields.One2many('stock.invoice.onshipping.quantity',
                                   'onshipping_id', 'Quantities')

    def _get_quantity_ids(self, cr, uid, context=None):
        quantities = []
        res_id = context and context.get('active_ids', [])
        if res_id:
            picking = self.pool.get('stock.picking').browse(cr, uid, res_id[0])
            for line in picking.move_lines:
                quantities.append((0, 0, {
                                    'product_id': line.product_id.id,
                                    'quantity': line.product_uom_qty,
                                    'move_id': line.id
                                  }))
        return quantities

    _defaults = {
        'quantity_ids': _get_quantity_ids,
    }

    def open_invoice(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context)
        dict_pdt_qty = {x.product_id.id: x.quantity for x in obj.quantity_ids}

        res = super(StockInvoiceOnshipping, self).open_invoice(cr, uid, ids, context)
        res_ids = context and context.get('active_ids', [])
        if res_ids:
            picking = self.pool.get('stock.picking').browse(cr, uid, res_ids[0])
            invoice_ids = self.pool.get('account.invoice').search(cr, SUPERUSER_ID, [('origin', '=', picking.name)])
            if invoice_ids:
                to_write = []
                invoice = self.pool.get('account.invoice').browse(cr, SUPERUSER_ID, invoice_ids[0])
                for line in invoice.invoice_line:
                    if line.product_id.id in dict_pdt_qty:
                        to_write.append((1, line.id, {'quantity': dict_pdt_qty[line.product_id.id]}))
                if to_write:
                    self.pool.get('account.invoice').write(cr, SUPERUSER_ID, invoice.id, {'invoice_line': to_write})
        return res


class StockInvoiceOnshippingQuantity(models.TransientModel):
    _name = 'stock.invoice.onshipping.quantity'

    onshipping_id = fields.Many2one('stock.invoice.onshipping', 'On Shippping')
    product_id = fields.Many2one('product.product', 'Product')
    move_id = fields.Many2one('stock.move', 'Move')
    quantity = fields.Integer('Quantity to Invoice')
