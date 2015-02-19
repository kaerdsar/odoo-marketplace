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


class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = 'purchase.order'

    def send_to_partner(self, cr, uid, ids, context=None):
        purchase = self.browse(cr, uid, ids[0])
        try:
            # context.update({'partner_db': db})
            self.pool.get('cenit.flow').execute(cr, uid, purchase, context)
            return True
        except Exception, e:
            return False

    def wkf_send_rfq(self, cr, uid, ids, context=None):
        res = self.send_to_partner(cr, uid, ids, context)
        if res:
            context = dict(context, mail_post_autofollow=True)
            self.signal_workflow(cr, uid, ids, 'send_rfq')
        return super(PurchaseOrder, self).wkf_send_rfq(cr, uid, ids, context)
