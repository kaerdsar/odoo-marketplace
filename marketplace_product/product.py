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


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'

    def publish_product(self, cr, uid, ids, context=None):
        product = self.browse(cr, uid, ids[0])
        context.update({'partner_db': config.get('main_database')})
        res = self.pool.get('cenit.flow').execute(cr, uid, product, context)
        if res:
            self.write(cr, uid, product.id, {'state': 'sellable'})
        return True
