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
from openerp.exceptions import ValidationError
import openerp.addons.decimal_precision as dp
from openerp.osv import fields as old_fields
#from openerp.addons.market_product import utils, mixin


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = ['publish.mixin', 'product.template']

    price_from = fields.Char(compute='_get_min_price', string='Price From',
                             size=64)
    country_id = fields.Many2one(compute='_get_country',
                                 comodel_name='res.country',
                                 string='Country')

    @api.one
    def _get_min_price(self):
        numbers = [x.variant_price for x in self.variant_ids]
        min_price = numbers and min(numbers) or 0
        if min_price:
            self.price_from = '$%s' % str(round(min_price, 2))
            
    @api.one
    def _get_country(self):
        country = False
        attribute_line = [x for x in self.attribute_line_ids
                                        if x.attribute_id.name == 'Country']
        if attribute_line:
            resource = attribute_line[0].value_ids[0].resource
            model, country_id = resource.split(',')
            country = self.env[model].browse(int(country_id))
        elif self.product_manager:
            country = self.product_manager.partner_id.country_id
        else:
            country = self.create_uid.partner_id.country_id
        self.country_id = country.id

    @api.one
    def publish_and_update_state(self):
        res = self.publish_to_master()
        if res:
            self.write({'state': 'sellable', 'to_send': False})
        return True

    @api.one
    def unpublish_and_update_state(self):
        res = self.unpublish_from_master()
        if res:
            self.write({'state': 'draft', 'to_send': False})
        return True

    _defaults = {
        'type': 'consu',
        'state': 'draft'
    }
