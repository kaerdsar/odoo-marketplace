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
from openerp import models, fields, api, SUPERUSER_ID
from openerp.tools import config
from openerp.addons.saas_utils import connector


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = ['product.template', 'catalog.mixin']

    def _get_seller(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid)
        supplier = {
            'name': user.company_id.partner_id.id,
            'min_qty': 1
        }
        return [(0, 0, supplier)]

    _defaults = {
        'seller_ids': _get_seller
    }
    
    @api.model
    def fields_view_get(self, *args, **kwargs):
        if self.env.user.id != SUPERUSER_ID and \
           not self.search([('sale_ok', '=', True)]):
            self.pull_initial_products()
        return super(ProductTemplate, self).fields_view_get(*args, **kwargs)
    
    @api.model
    def pull_initial_products(self):
        product_ids = []
        partner = self.env.user.partner_id
        db = config.get('db_master')
        registry = openerp.modules.registry.RegistryManager.get(db)
        with registry.cursor() as cr:
            res_user = registry['res.users']
            user_ids = res_user.search(cr, SUPERUSER_ID,
                                     [('partner_id.name', '=', partner.name)])
            if user_ids:
                user_id = user_ids[0]
                product_template = registry['product.template']
                product_ids = product_template.search(cr, SUPERUSER_ID,
                                            [('product_manager', '=', user_id)])
        for product_id in product_ids:
            self.pull_from_catalog(product_id)


class MarketRequest(models.Model):
    _name = 'market.request'
    _inherit = ['catalog.mixin', 'market.request']

    @api.model
    def select_products(self, ids):
        obj_ids = self.pull_from_catalog(ids[0])
        obj = self.pool.get('market.request').browse(self.env.cr, self.env.uid,
                                                     obj_ids[0])
        vals = {
            'name': obj.name,
            'request_id': obj.id,
            'line_ids': [(0, 0, {'request_line_id': x.id}) for x in obj.line_ids]
        }
        rtq_id = self.env['request.to.quotation'].create(vals)
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'request.to.quotation',
            'res_id': rtq_id.id,
            'target': 'new'
        }


class MarketRequestLine(models.Model):
    _name = 'market.request.line'
    _inherit = ['market.request.line', 'catalog.mixin']

