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


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    def send_to_partner(self, cr, uid, ids, context=None):
        sale = self.browse(cr, uid, ids[0])
        try:
            # context.update({'partner_db': db})
            self.pool.get('cenit.flow').execute(cr, uid, sale, context)
            return True
        except Exception, e:
            return False

    def action_quotation_send(self, cr, uid, ids, context=None):
        res = self.send_to_partner(cr, uid, ids, context)
        if res:
            context = dict(context, mail_post_autofollow=True)
            self.signal_workflow(cr, uid, ids, 'quotation_sent')
        return super(SaleOrder, self).action_quotation_send(cr, uid, ids, context)


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
        order = self.pool.get('sale.order')
        self.date_planned = order._get_date_planned(self.env.cr, self.env.uid,
                                                    self.order_id, self,
                                                    self.order_id.date_order)

