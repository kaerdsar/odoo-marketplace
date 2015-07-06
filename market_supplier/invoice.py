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
from openerp import SUPERUSER_ID as SI
from openerp.addons.saas_utils import connector
from openerp.exceptions import ValidationError
import openerp.addons.decimal_precision as dp


class CommercialInvoice(models.Model):
    _name = 'commercial.invoice'
    _inherit = ['mail.thread', 'shipping.mixin']
    
    @api.one
    @api.depends('invoice_lines.price_subtotal')
    def _compute_amount(self):
        self.amount_total = sum(line.price_subtotal for line in self.invoice_lines)
        
    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id
    
    name = fields.Char(string='Reference/Description', index=True)
    origin = fields.Char(string='Source Document', readonly=True,
        help="Reference of the document that produced this invoice.")
    reference = fields.Char(string='Invoice Reference',
        help="The partner reference of this invoice.")
    comment = fields.Text('Additional Information')
    sent = fields.Boolean(readonly=True, default=False, copy=False,
        help="It indicates that the invoice has been sent.")
    date_invoice = fields.Date(string='Invoice Date')
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    invoice_lines = fields.One2many('commercial.invoice.line', 'invoice_id',
        string='Invoice Lines')
    amount_total = fields.Float(string='Total', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_amount')
    currency_id = fields.Many2one('res.currency', string='Currency',
        required=True, default=_default_currency)
    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env['res.company']._company_default_get('account.invoice'))
    user_id = fields.Many2one('res.users', string='Salesperson',
        default=lambda self: self.env.user)
        
    @api.model
    def get_commercial_invoice_from_order(self, order):
        invoices = self.search([('origin', '=', order.name)])
        if invoices:
            commercial_invoice = invoices[0]
        else:
            ci_vals = {
                'name': order.name.replace('SO', 'CI'),
                'origin': order.name,
                'comment': order.note,
                'date_invoice': order.date_order,
                'partner_id': order.partner_id.id,
                'mode_of_payment': order.mode_of_payment,  
                'mode_of_transport': order.mode_of_transport,
                'carrier': order.carrier,
                'city_of_origin': order.city_of_origin,
                'departure_port': order.departure_port,
                'arrival_port': order.arrival_port,
                'destination_city': order.destination_city,
                'awb_bl_number': order.awb_bl_number,
                'shipping_date': order.shipping_date
            }
            lines = []
            for line in order.order_line:
                cil_vals = {
                    'name': line.name,
                    'product_id': line.product_id.id,
                    'uos_id': line.product_uom.id,
                    'price_unit': line.price_unit,
                    'quantity': line.product_uom_qty
                }
                lines.append((0, 0, cil_vals))
            if lines:
                ci_vals.update({'invoice_lines': lines})
            commercial_invoice = self.create(ci_vals)
        return commercial_invoice

    def action_commercial_invoice_send(self, cr, uid, ids, context=None):
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid,
                                        'market_b2b_supplier',
                                        'email_template_edi_commercial_invoice')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail',
                                        'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'commercial.invoice',
            'default_res_id': ids[0],
            'default_use_template': False,
            'default_template_id': template_id,
            'default_composition_mode': 'comment'
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx
        }

    
class CommercialInvoiceLine(models.Model):
    _name = 'commercial.invoice.line'
    
    @api.one
    @api.depends('price_unit', 'discount', 'quantity', 'product_id',
                 'invoice_id.partner_id', 'invoice_id.currency_id')
    def _compute_price(self):
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        self.price_subtotal = price * self.quantity
        if self.invoice_id:
            self.price_subtotal = self.invoice_id.currency_id.round(self.price_subtotal)
    
    @api.model
    def _default_price_unit(self):
        total = 0
        for l in self._context.get('invoice_lines', []):
            if isinstance(l, (list, tuple)) and len(l) >= 3 and l[2]:
                vals = l[2]
                price = vals.get('price_unit', 0) * (1 - vals.get('discount', 0) / 100.0)
                total = total - (price * vals.get('quantity'))
        return total
    
    name = fields.Text(string='Description', required=True)
    origin = fields.Char(string='Source Document',
        help="Reference of the document that produced this invoice.")
    sequence = fields.Integer(string='Sequence', default=10,
        help="Gives the sequence of this line when displaying the invoice.")
    invoice_id = fields.Many2one('commercial.invoice', string='Invoice Reference',
        ondelete='cascade', index=True)
    uos_id = fields.Many2one('product.uom', string='Unit of Measure',
        ondelete='set null', index=True)
    product_id = fields.Many2one('product.product', string='Product',
        ondelete='restrict', index=True)
    price_unit = fields.Float(string='Unit Price', required=True,
        digits= dp.get_precision('Product Price'),
        default=_default_price_unit)
    price_subtotal = fields.Float(string='Amount', digits= dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_price')
    quantity = fields.Float(string='Quantity', digits= dp.get_precision('Product Unit of Measure'),
        required=True, default=1)
    discount = fields.Float(string='Discount (%)', digits= dp.get_precision('Discount'),
        default=0.0)
    company_id = fields.Many2one('res.company', string='Company',
        related='invoice_id.company_id', store=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner',
        related='invoice_id.partner_id', store=True, readonly=True)
