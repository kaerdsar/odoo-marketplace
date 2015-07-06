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

from openerp import models, fields, api


class RequestToQuotation(models.TransientModel):
    _name = 'request.to.quotation'

    name = fields.Char('Name', size=128)
    request_id = fields.Many2one('market.request', 'Request')
    line_ids = fields.One2many('request.to.quotation.line', 'request_id',
                               'Lines')

    @api.model
    def create_quotation(self, ids):
        args = (self.env.cr, self.env.uid, ids[0])
        obj = self.pool.get('request.to.quotation').browse(*args)
        lines = []
        for x in obj.line_ids:
            if x.product_id:
                vals = {
                    'product_tmpl_id': x.product_id.product_tmpl_id.id,
                    'product_id': x.product_id.id,
                    'name': x.product_id.name,
                    'product_uom_qty': x.request_line_id.quantity,
                    'product_uom': 1,
                    'price_unit': x.product_id.lst_price,
                    'state': 'draft'
                }
                lines.append((0, 0, vals))
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'context': {
                'partner_id': obj.request_id.partner_id.id,
                'default_partner_id': obj.request_id.partner_id.id,
                'default_pricelist_id': obj.request_id.partner_id.property_product_pricelist.id,
                'default_currency_id': obj.request_id.partner_id.property_product_pricelist.currency_id.id,
                'default_origin': obj.request_id.name,
                'default_order_line': lines
            }
        }


class RequestToQuotationLine(models.TransientModel):
    _name = 'request.to.quotation.line'

    request_line_id = fields.Many2one('market.request.line', 'Request')
    product_id = fields.Many2one('product.product', 'Variant')
    request_id = fields.Many2one('request.to.quotation', 'Request')
