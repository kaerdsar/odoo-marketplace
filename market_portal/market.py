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
from openerp.addons.saas_utils import database

MODELS = ['product.category', 'product.attribute', 'product.attribute.value']


class MarketData(models.TransientModel):
    _name = 'market.data'

    model_ids = fields.Many2many('ir.model', rel='data_model_rel',
                                 id1='data_id', id2='model_id',
                                 string='Models',
                                 domain=[('model', 'in', MODELS)])
    database = fields.Char('Database')

    @api.one
    def synchronize_objects(self):
        flow = self.env['cenit.flow']
        dbs = self.database and [self.database] or database.get_market_dbs() 
        for db in dbs:
            ctx = {'partner_db': db, 'send_method':'local_post'}
            for x in self.model_ids:
                domain = [
                    ('data_type.model.model', '=', x.model)
                    #('purpose', '=', 'send')
                ]
                flows = flow.with_context(ctx).search(domain)
                if flows:
                    flow_ids = [x.id for x in flows]
                    ctx.update({'user': 1})
                    self.env['cenit.flow'].with_context(ctx).send_all(flow_ids[0])

    def _get_default_models(self, cr, uid, context=None):
        model_ids = self.pool.get('ir.model').search(cr, uid, 
                                                     [('model', 'in', MODELS)],
                                                     context=context)
        return [(6, 0, model_ids)]

    _defaults = {
        'model_ids': _get_default_models
    }
