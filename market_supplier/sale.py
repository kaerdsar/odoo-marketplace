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


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['publish.mixin', 'sale.order']

    def __init__(self, pool, cr):
        from openerp.addons.sale.sale import sale_order
        item = ('to_approve', 'Waiting Approval')
        if item not in sale_order._columns['state'].selection:
            sale_order._columns['state'].selection.insert(4, item)
        return super(SaleOrder, self).__init__(pool, cr)

    @api.one
    def check_and_publish(self):
        for line in self.order_line:
            if line.product_id and not line.product_id.published:
                model = self.env['product.product']
                domain = [('id', '=', line.product_id.id)]
                objs = model.search(domain)
                if objs and not objs[0].product_id.published:
                    raise ValidationError('''You must publish the product %s
                              before send the order''' % line.product_id.name)
        return self.publish_to_partner()

    @api.multi
    def action_quotation_send(self):
        if self.exists_partner():
            self.check_and_publish()
            self.signal_workflow('quotation_sent')
        return super(SaleOrder, self).action_quotation_send()

    @api.multi
    def action_approve(self):
        return self.write({'state': 'to_approve'})

    """@api.multi
    def action_ship_create(self):
        res = super(SaleOrder, self).action_ship_create()
        for obj in self:
            if obj.commodity_environment:
                for pick in obj.picking_ids:
                    pick.force_assign()
        return res"""

    @api.one
    def get_signup_url(self):
        obj_name = self.name
        user = self.exists_partner()
        if user and 'database' in user:
            db = user['database']
            registry = openerp.modules.registry.RegistryManager.get(db)
            with registry.cursor() as db_cr:
                po = registry['purchase.order']
                po_ids = po.search(db_cr, SI, [('name', '=', obj_name)])
                if not po_ids:
                    return False
                document = po.browse(db_cr, SI, po_ids[0])
                rp = registry['res.partner']
                if not document.company_id.partner_id.child_ids:
                    return False
                partner = document.company_id.partner_id.child_ids[0]
                data = rp._get_signup_url_for_action(db_cr, SI, [partner.id],
                                        action='mail.action_mail_redirect',
                                        model='purchase.order',
                                        res_id=document.id)
                url = data[partner.id]
            return url
        return super(SaleOrder, self).get_signup_url()

    def get_commercial_invoice(self, cr, uid, ids, context=None):
        ci = self.pool.get('commercial.invoice')
        order = self.browse(cr, uid, ids[0])
        invoice = ci.get_commercial_invoice_from_order(cr, uid, order)
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'commercial.invoice',
            'res_id': invoice.id
        }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def __init__(self, pool, cr):
        from openerp.addons.sale.edi import sale_order as edi_order
        edi_order.SALE_ORDER_LINE_EDI_STRUCT['date_planned'] = True
        return super(SaleOrderLine, self).__init__(pool, cr)

    date_planned = fields.Date(compute='_get_date_planned',
                               string='Date Planned')

    @api.one
    def _get_date_planned(self):
        order = self.env['sale.order']
        self.date_planned = order._get_date_planned(self, self.order_id.date_order)
