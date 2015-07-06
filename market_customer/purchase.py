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


class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = ['publish.mixin', 'purchase.order']

    commodity_environment = fields.Boolean(compute='_is_commodity_environment',
                                           string='Commodity Environment',
                                           default=False)

    @api.one
    def _is_commodity_environment(self):
        self.commodity_environment = False
        for line in self.order_line:
            if line.product_id.is_comodity:
                self.commodity_environment = True
                break

    @api.multi
    def wkf_send_rfq(self):
        partner = self.exists_partner()
        if partner:
            self.publish_to_partner()
            self.signal_workflow('send_rfq')
        return super(PurchaseOrder, self).wkf_send_rfq()

    @api.model
    def create(self, vals):
        if vals.get('origin', False):
            pr = self.env['purchase.requisition']
            pr_objs = pr.search([('name', '=', vals['origin'])])
            vals['requisition_id'] = pr_objs and pr_objs[0].id or False
        self._pull_products(vals)
        return super(PurchaseOrder, self).create(vals)

    @api.one
    def write(self, vals):
        self._pull_products(vals)
        return super(PurchaseOrder, self).write(vals)

    @api.onchange('partner_id')
    def onchange_partner_in_marketplace(self):
        if self.partner_id:
            domain = [('seller_id.name', '=', self.partner_id.name)]
            pids = connector.call(config.get('db_master'),
                                  'product.template.commodity',
                                  'search', domain)
            for pid in pids:
                self.env['product.template.commodity'].pull_from_catalog(pid)
                
    @api.model
    def _pull_products(self, vals):
        if vals.get('line_items', False):
            pt = self.env['product.template.commodity']
            for line in vals['line_items']:
                pname = line.get('product')
                if pname and not pt.search([('name', '=', pname)]):
                    pt.pull_from_catalog_by('name', pname)


class PurchaseRequisition(models.Model):
    _name = 'purchase.requisition'
    _inherit = ['publish.mixin', 'purchase.requisition']

    country = fields.Many2one('res.country', 'Country')
    destination = fields.Many2one('res.country', 'Destination')
    frequency = fields.Selection([('one_time', 'One Time'),
                                  ('daily', 'Daily'),
                                  ('weekly', 'Weekly'),
                                  ('biweekly', 'Biweekly'),
                                  ('other', 'Other')], 'Frequency',
                                 default='one_time')
    commodity_environment = fields.Boolean(compute='_is_commodity_environment',
                                           string='Commodity Environment',
                                           default=False)

    def tender_in_progress(self):
        self.publish_to_master()
        return super(PurchaseRequisition, self).tender_in_progress()

    def tender_cancel(self):
        self.with_context(master_model='market.request').unpublish_from_master()
        return super(PurchaseRequisition, self).tender_cancel()
        
    @api.multi
    def unlink(self):
        for obj in self:
            obj.with_context(master_model='market.request').unpublish_from_master()
        return super(PurchaseRequisition, self).unlink()

    @api.one
    def _is_commodity_environment(self):
        self.commodity_environment = False
        for line in self.line_ids:
            if line.commodity_id:
                self.commodity_environment = True
                break


class PurchaseRequisitionLine(models.Model):
    _name = 'purchase.requisition.line'
    _inherit = ['purchase.requisition.line', 'commodity.line.mixin']
    
    description = fields.Char('Description')
