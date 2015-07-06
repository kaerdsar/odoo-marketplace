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


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = ['publish.mixin', 'account.invoice', 'ir.needaction_mixin']
    
    @api.model
    def create(self, vals):
        if self.env.context.get('receive_object', False):
            vals = self._prepare_external_object(vals)
        return super(AccountInvoice, self).create(vals)
        
    @api.multi
    def write(self, vals):
        if self.env.context.get('receive_object', False):
            vals = self._prepare_external_object(vals)
        return super(AccountInvoice, self).write(vals)
        
    def _prepare_external_object(self, vals):
        if 'type' in vals:
            prefix = vals['type'].split('_')[0] == 'out' and 'in' or 'out'
            vals['type'] = '%s_%s' % (prefix, vals['type'].split('_')[1])
            if not vals.get('account_id', False) and vals.get('partner_id', False):
                partner = self.env['res.partner'].browse(vals['partner_id'])
                if vals['type'] in ('out_invoice', 'out_refund'):
                    vals['account_id'] = partner.property_account_receivable.id
                else:
                    vals['account_id'] = partner.property_account_payable.id
        return vals

    @api.multi
    def action_invoice_sent(self):
        if self.exists_partner():
            self.publish_to_partner()
        return super(AccountInvoice, self).action_invoice_sent()
