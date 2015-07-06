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

from openerp import models
from openerp.tools import config
from openerp.addons.market_product import mixin
from openerp.addons.saas_utils import connector


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'catalog.mixin']

    def select_products(self, cr, uid, ids, context=None):
        obj_ids = self.pull_from_catalog(cr, uid, ids[0])
        obj = self.browse(cr, uid, obj_ids[0])
        pt = self.pool.get('product.template.commodity')
        product_ids = connector.call(config.get('db_master'),
                                     'product.template.commodity', 'search',
                                     [('seller_id', '=', ids[0])])
        lines = []
        for pid in product_ids:
            lpid = pt.pull_from_catalog(cr, uid, pid)
            product = pt.browse(cr, uid, lpid[0])
            lines.append((0, 0, {
                            'product_commodity_id': product.id,
                            'variant_commodity_id': product.variant_ids[0].id,
                            'quantity': product.variant_ids[0].moq
                        }))
        vals = {
            'name': obj.name,
            'partner_id': obj.id,
            'line_ids': lines
        }
        ptr_id = self.pool.get('partner.to.request').create(cr, uid, vals)
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'partner.to.request',
            'res_id': ptr_id,
            'target': 'new'
        }
