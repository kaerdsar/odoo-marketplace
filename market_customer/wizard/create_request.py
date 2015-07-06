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
from datetime import datetime as dt

from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DF


class PartnerToRequest(models.TransientModel):
    _name = 'partner.to.request'

    name = fields.Char('Name', size=128)
    partner_id = fields.Many2one('res.partner', 'Partner')
    line_ids = fields.One2many('partner.to.request.line', 'request_id',
                               'Lines')

    @api.model
    def create_request(self, ids):
        args = (self.env.cr, self.env.uid, ids[0])
        obj = self.pool.get('partner.to.request').browse(*args)
        lines = [(0, 0, {
                    'product_tmpl_id': x.product_commodity_id.product_template_id.id,
                    'product_id': x.variant_commodity_id.product_product_id.id,
                    'name': x.variant_commodity_id.product_product_id.name,
                    'product_qty': x.quantity,
                    'date_planned': dt.strftime(dt.today(), DF),
                    'product_uom': 1,
                    'price_unit': x.variant_commodity_id.lst_price,
                    'state': 'draft'})
                for x in obj.line_ids]
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'context': {
                'catalog_db': False,
                'commodity_environment': True,
                'default_partner_id': obj.partner_id.id,
                'default_pricelist_id': obj.partner_id.property_product_pricelist.id,
                'default_order_line': lines
            }
        }


class PartnerToRequestLine(models.TransientModel):
    _name = 'partner.to.request.line'

    product_commodity_id = fields.Many2one('product.template.commodity',
                                           'Commodity')
    variant_commodity_id = fields.Many2one('product.commodity.variant',
                                           'Variety')
    request_id = fields.Many2one('partner.to.request', 'Request')
    quantity = fields.Integer('Quantity', default=1)
    
    @api.onchange('variant_commodity_id')
    def onchange_variant(self):
        if self.variant_commodity_id:
            self.quantity = self.variant_commodity_id.moq
