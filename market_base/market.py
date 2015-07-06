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
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp


class MarketRequest(models.Model):
    _name = 'market.request'

    name = fields.Char('Reference', size=128, required=True)
    country = fields.Many2one('res.country', 'Country')
    destination = fields.Many2one('res.country', 'Destination')
    frequency = fields.Selection([('one_time', 'One Time'),
                                  ('daily', 'Daily'),
                                  ('weekly', 'Weekly'),
                                  ('biweekly', 'Biweekly'),
                                  ('create', 'Create')], 'Frequency',
                                 default='one_time')
    partner = fields.Many2one('res.partner', 'Customer')
    ordering_date = fields.Date('Scheduled Ordering Date')
    date_end = fields.Datetime('Bid Submission Deadline')
    schedule_date = fields.Date('Scheduled Date', select=True)
    line_ids = fields.One2many('market.request.line', 'request', 'Lines')
    description = fields.Text('Description')
    summary = fields.Char(compute='_get_summary', string='Summary', size=255)

    @api.one
    def _get_summary(self):
        self.summary = ', '.join([x.name for x in self.line_ids if x.name])


class MarketRequestLines(models.Model):
    _name = 'market.request.line'

    name = fields.Char(compute='_line_name', string='Reference', size=256)
    product = fields.Many2one('product.product', 'product')
    quantity = fields.Float('Quantity',
                            digits_compute=dp.get_precision('PUoM'))
    request = fields.Many2one('market.request', 'Request', ondelete='cascade')
                                 
    @api.one
    def _line_name(self):
        if product:
            self.name = self.product.name
