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

from openerp import models, api
from openerp.addons.saas_utils import connector
from openerp.tools import config, DEFAULT_SERVER_DATETIME_FORMAT as DF


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = ['product.template', 'catalog.mixin']
    
    def _name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100, name_get_uid=None):
        if context.get('commodity_environment') and context.get('seller_id'):
            args += [('seller_id', '=', context['seller_id'])]           
        return super(ProductTemplate, self)._name_search(cr, user, name, args, operator, context, limit, name_get_uid)


class ProductTemplateCommodity(models.Model):
    _name = 'product.template.commodity'
    _inherit = ['product.template.commodity', 'catalog.mixin']
        

class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit = ['product.product', 'catalog.mixin']


class ProductCommodityVariant(models.Model):
    _name = 'product.commodity.variant'
    _inherit = ['product.commodity.variant', 'catalog.mixin']
    
    @api.model
    def _get_commodity_data(self, ids):
        db = config.get('db_master')
        domain = [('id', '=', ids[0])]
        fields = ['product_commodity_id', 'variant']
        return connector.call(db, self._name, 'search_read', domain, fields)
    
    @api.model
    def create_request(self, ids):
        data = self._get_commodity_data(ids)
        if data:
            cid = data[0]['product_commodity_id'][0]
            pid = self.env['product.template.commodity'].pull_from_catalog(cid)
            res = self.search([('product_commodity_id', '=', pid[0]),
                               ('variant', '=', data[0]['variant'])])
            if not res:
                return False
            args = (self.env.cr, self.env.uid, res[0].id)
            variant = self.pool.get('product.commodity.variant').browse(*args)
            lines = [(0, 0, {
                        'product_tmpl_id': variant.product_product_id.product_tmpl_id.id,
                        'product_id': variant.product_product_id.id,
                        'name': variant.name,
                        'product_qty': variant.moq,
                        'date_planned': dt.strftime(dt.today(), DF),
                        'product_uom': 1,
                        'price_unit': variant.lst_price,
                        'state': 'draft'})]
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'purchase.order',
                'context': {
                    'catalog_db': False,
                    'commodity_environment': True,
                    'default_create_uid': self.env.uid,
                    'default_partner_id': variant.product_commodity_id.seller_id.id,
                    'default_pricelist_id': variant.product_commodity_id.seller_id.property_product_pricelist.id,
                    'default_order_line': lines
                }
            }
            
    @api.model
    def show_details(self, ids):
        data = self._get_commodity_data(ids)
        if data:
            xml_id = 'market_b2b_customer.catalog_product_template_form_view'
            args = (self.env.cr, self.env.uid, xml_id)
            view_id = self.pool.get('ir.model.data').xmlid_to_res_id(*args)
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view_id,
                'res_model': 'product.template.commodity',
                'res_id': data[0]['product_commodity_id'][0],
                'context': {'catalog_db': 'db_master'}
            }


class ProductAttributeLine(models.Model):
    _name = 'product.attribute.line'
    _inherit = ['product.attribute.line', 'catalog.mixin']


class ProductAttributeValue(models.Model):
    _name = 'product.attribute.value'
    _inherit = ['product.attribute.value', 'catalog.mixin']


class ProductCommodityForecast(models.Model):
    _name = 'product.commodity.forecast'
    _inherit = ['product.commodity.forecast', 'catalog.mixin']


class ProductCommoditySeason(models.Model):
    _name = 'product.commodity.season'
    _inherit = ['product.commodity.season', 'catalog.mixin']


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
