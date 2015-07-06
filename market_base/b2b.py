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
import datetime as dt
import openerp
from openerp import models, fields, api, SUPERUSER_ID
from openerp.tools import config


class B2BFlow(models.Model):
    _name = 'b2b.flow'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char('Name', track_visibility='always')
    partner_id = fields.Many2one('res.partner', 'Partner',
                                 track_visibility='always')
    last_send_date = fields.Datetime(compute='_get_last_date',
                                     string='Last Send Date')
    last_receive_date = fields.Datetime(compute='_get_last_date',
                                        string='Last Receive Date')
    transactions = fields.One2many('b2b.flow.transaction', 'flow',
                                   'Transactions')
    
    @api.model
    def create(self, vals):
        db = config.get('db_master')
        if 'name' not in vals:
            registry = openerp.modules.registry.RegistryManager.get(db)
            with registry.cursor() as db_cr:
                bf = registry['b2b.flow']
                wals = {'client': self.env.cr.dbname}
                b2b_flow_id = bf.create(db_cr, SUPERUSER_ID, wals)
                flow = bf.browse(db_cr, SUPERUSER_ID, b2b_flow_id).name
            vals['name'] = flow
        return super(B2BFlow, self).create(vals)

    @api.one
    def _get_last_date(self):
        send, receive = False, False
        for transaction in self.transactions:
            if transaction.action == 'send' and not send:
                self.last_send_date = transaction.date
                send = True
            elif transaction.action == 'receive' and not receive:
                self.last_receive_date = transaction.date
                receive = True
            if send and receive:
                break
                
    @api.model
    def register_flow(self, model, vals):
        if vals.get('flow', False):
            flows = self.env['b2b.flow'].search([('name', '=', vals['flow'])])
            if flows:
                return flows[0].name
            else:
                wals = {
                    'name': vals['flow'],
                    'partner_id': vals.get('partner_id', False)
                }
                flow = self.env['b2b.flow'].create(wals)
                return flow.name
        else:
            if model in ['purchase.order', 'sale.order']:
                wals = {'partner_id': vals.get('partner_id', False)}
                flow = self.env['b2b.flow'].create(wals)
                return flow.name
            elif model == 'stock.picking':
                origin = vals.get('origin', '')
                model = origin.startswith('P') and 'purchase.order' or 'sale.order'
                res = self.env[model].search([('name', '=', origin)])
                return res and res[0].flow or False 
            elif model == 'account.invoice':
                origin = vals.get('origin', '')
                res = self.env['stock.picking'].search([('name', '=', origin)])
                return res and res[0].flow or False
        
        
class B2BFlowTransaction(models.Model):
    _name = 'b2b.flow.transaction'
    
    model = fields.Char('Model')
    name = fields.Char('Name', size=128)
    origin = fields.Char('Origin', size=64)
    state = fields.Char('State', size=64)
    date = fields.Datetime('Publish Date')
    action = fields.Selection([('send', 'Send'), ('receive', 'Receive')],
                              'Action')
    flow = fields.Many2one('b2b.flow', 'Flow')
    
    _order = 'date desc'
    
    @api.model
    def register_transaction(self, obj, action):
        flows = self.env['b2b.flow'].search([('name', '=', obj.flow)])
        if flows:
            vals = {
                'model': obj._name,
                'name': obj.name,
                'origin': obj.origin,
                'state': obj.state,
                'date': dt.datetime.now(),
                'action': action,
                'flow': flows[0].id
            }
            return self.create(vals)
    
    
class CenitFlow(models.Model):
    _name = 'cenit.flow'
    _inherit = 'cenit.flow'
    
    def receive(self, cr, uid, root, data, context=None):
        res = super(CenitFlow, self).receive(cr, uid, root.lower(), data, context)
        if res:
            context = context or {}
            data_type = self.find(cr, uid, root, 'receive', context)
            if data_type:
                model = self.pool.get(data_type.model_id.model)
                for d in [x for x in data if 'flow' in x]:
                    obj_ids = model.search(cr, uid, [('flow', '=', d['flow'])])
                    if obj_ids:
                        obj = model.browse(cr, uid, obj_ids[0])
                        transaction = self.pool.get('b2b.flow.transaction')
                        transaction.register_transaction(cr, uid, obj, 'receive')
        return res
        
    def send(self, cr, uid, obj, context=None):
        res = super(CenitFlow, self).send(cr, uid, obj, context)
        if res:
            transaction = self.pool.get('b2b.flow.transaction')
            transaction.register_transaction(cr, uid, obj, 'send')
        return res
