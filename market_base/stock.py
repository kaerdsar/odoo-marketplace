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
from openerp import models, fields, api, SUPERUSER_ID as SI
import openerp.addons.decimal_precision as dp
from openerp.exceptions import ValidationError


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['publish.mixin', 'stock.picking', 'ir.needaction_mixin']
    _order = 'date desc'

    shipped_quantity = fields.Float(compute='_get_quantities', string='Shipped Qty.',
                                    digits_compute=dp.get_precision('Product Unit of Measure'),
                                    track_visibility='always')
    received_quantity = fields.Float(compute='_get_quantities', string='Received Qty.',
                                     digits_compute=dp.get_precision('Product Unit of Measure'),
                                     track_visibility='always')

    @api.one
    def _get_quantities(self):
        self.shipped_quantity = sum([x.shipped_quantity for x in self.pack_operation_ids if x.shipped_quantity] or [0])
        self.received_quantity = sum([x.received_quantity for x in self.pack_operation_ids if x.received_quantity] or [0])

    @api.multi
    def action_picking_send(self):
        if self.exists_partner():
            self.publish_to_partner()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('market_product',
                                        'email_template_edi_stock_picking')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail',
                                        'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'stock.picking',
            'default_res_id': self[0].id,
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

    @api.one
    def do_enter_transfer_details(self):
        for operation in self.pack_operation_ids:
            if self.picking_type_code == 'incoming' and not operation.received_quantity:
                raise ValidationError("Missing %s quantity" % 'received')
            if self.picking_type_code == 'outgoing' and not operation.shipped_quantity:
                raise ValidationError("Missing %s quantity" % 'shipped')
        std = self.env['stock.transfer_details']
        obj = std.create({'picking_id': self.id})
        return obj.do_detailed_transfer()
        
    def get_signup_url(self, cr, uid, ids, context=None):
        assert len(ids) == 1
        obj_name = self.browse(cr, uid, ids[0]).origin
        user = self.exists_partner(cr, uid, ids, context)
        if user:
            db = user['database']
            registry = openerp.modules.registry.RegistryManager.get(db)
            with registry.cursor() as db_cr:
                po = registry['stock.picking']
                po_ids = po.search(db_cr, SI, [('origin', '=', obj_name)])
                if not po_ids:
                    return False
                document = po.browse(db_cr, uid, po_ids[0], context=context)
                rp = registry['res.partner']
                if not document.company_id.partner_id.child_ids:
                    return False
                partner = document.company_id.partner_id.child_ids[0]
                data = rp._get_signup_url_for_action(db_cr, SI, [partner.id],
                                        action='mail.action_mail_redirect',
                                        model='stock.picking',
                                        res_id=document.id)
                url = data[partner.id]
            return url
        else:
            document = self.browse(cr, uid, ids[0], context=context)
            contex_signup = dict(context, signup_valid=True)
            return self.pool['res.partner']._get_signup_url_for_action(
                cr, uid, [document.partner_id.id], action='mail.action_mail_redirect',
                model=self._name, res_id=document.id, context=contex_signup,
            )[document.partner_id.id]


class StockMove(models.Model):
    _name = 'stock.move'
    _inherit = 'stock.move'

    @api.one
    def write(self, vals):
        res = super(StockMove, self).write(vals)
        if vals.get('picking_id', False) or self.picking_id:
            operation = self.env['stock.pack.operation']
            domain = [('product_id', '=', self.product_id.id),
                      ('product_qty', '=', self.product_uom_qty),
                      ('picking_id', '=', self.picking_id.id)]
            if not operation.search(domain):
                wals = {x[0]: x[2] for x in domain}
                wals.update({
                    'location_id': self.picking_id.location_id.id,
                    'location_dest_id': self.picking_id.location_dest_id.id,
                    'product_uom_id': self.product_id.uom_id.id,
                    'ordered_quantity': self.product_uom_qty
                })
                operation.create(wals)
        return res


class StockPackOperation(models.Model):
    _name = 'stock.pack.operation'
    _inherit = 'stock.pack.operation'

    shipped_quantity = fields.Float(string='Shipped Quantity',
                    digits_compute=dp.get_precision('Product Unit of Measure'))
    received_quantity = fields.Float(string='Received Quantity',
                    digits_compute=dp.get_precision('Product Unit of Measure'))
    ordered_quantity = fields.Float(string='Ordered Quantity',
                    digits_compute=dp.get_precision('Product Unit of Measure'))
    picking_type_code = fields.Char(compute='_get_pickgin_type_code',
                                    string='Picking Type Code', size=32)

    @api.one
    def _get_pickgin_type_code(self):
        self.picking_type_code = self.picking_id.picking_type_code

    @api.onchange('shipped_quantity', 'received_quantity')
    def onchange_operation_quantity(self):
        if self.picking_id.picking_type_code == 'incoming':
            self.product_qty = self.received_quantity
        elif self.picking_id.picking_type_code == 'outgoing':
            self.product_qty = self.shipped_quantity
