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

{
    'name': 'Market B2B Supplier',
    'version': '0.1',
    'author': 'OpenJAF',
    'website': 'http://www.openjaf.com',
    'category': 'Base',
    'description': """
        Market B2B Supplier
    """,
    'depends': ['market_base', 'sale_stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/market.xml',
        'views/product.xml',
        'views/res.xml',
        'views/sale.xml',
        'views/stock.xml',
        'views/invoice.xml',
        'report/invoice_report.xml',
        'report/invoice_report_template.xml',
        'report/invoice_action_data.xml'
    ],
    'installable': True
}
