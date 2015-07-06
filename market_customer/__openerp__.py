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
    'name': 'Market B2B Customer',
    'version': '0.1',
    'author': 'OpenJAF',
    'website': 'http://www.openjaf.com',
    'category': 'Base',
    'description': """
        Market B2B Customer
    """,
    'depends': ['market_purchase'],
    'data': [
        'security/ir.model.access.csv',
        'cenit/schemas.xml',
        'cenit/flows.xml',
        'views/market.xml',
        'views/product.xml',
        'views/res.xml',
        'views/purchase.xml',
        'views/stock.xml',
        'views/invoice.xml'
    ],
    'installable': True
}
