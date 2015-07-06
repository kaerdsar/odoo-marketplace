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
from openerp.tools import config
from openerp.addons.saas_utils import connector


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = ['product.template', 'catalog.mixin']


class ProductTemplateCommodity(models.Model):
    _name = 'product.template.commodity'
    _inherit = 'product.template.commodity'
    
    @api.multi
    def unlink(self):
        for obj in self:
            obj.unpublish_from_master()
        return super(ProductTemplateCommodity, self).unlink()

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


class MarketPriceByDate(models.Model):
    _name = 'market.price.by.date'
    _inherit = ['market.price.by.date', 'catalog.mixin']


class FilterCommodity(models.TransientModel):
    _name = 'filter.commodity'
    _inherit = 'filter.commodity'

    def save(self, cr, uid, ids, context=None):
        res = super(FilterCommodity, self).save(cr, uid, ids, context)
        res.update({'context': {'catalog_db': 'db_master'}})
        return res
