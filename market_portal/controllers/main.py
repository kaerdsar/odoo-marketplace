# -*- coding: utf-8 -*-
import werkzeug

from openerp import SUPERUSER_ID
from openerp import http
from openerp.http import request
from openerp.tools.translate import _
from openerp.addons.website.models.website import slug
from openerp.addons.web.controllers.main import login_redirect

from openerp.addons.website_sale.controllers.main import table_compute, QueryURL

PPG = 20 # Products Per Page
PPR = 4  # Products Per Row

PRODUCT_FIELDS = [{'name': 'commodities', 'model': 'market.commodity'},
                  {'name': 'varieties', 'model': 'market.variety'},
                  {'name': 'packages', 'model': 'market.package'}]


class WebsiteSaleSeller(http.Controller):
        
    @http.route('/seller/add_product', type='http', auth='user', website=True)
    def add_product(self, *args, **kw):
        qcontext = request.params.copy()
        qcontext['new'] = True
        qcontext['success'] = False
        
        for field in PRODUCT_FIELDS:
            if not qcontext.get(field['name']):
                qcontext[field['name']] = self.get_values(field['model'])
            
        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                self.do_add_product(qcontext)
                if 'create_and_finish' in kw:
                    return request.redirect('/saas_server/tenant')
                qcontext['success'] = True
                qcontext['name'] = False
            except Exception, e:
                qcontext['error'] = _(e.message)

        return request.render('website_sale_seller.add_product', qcontext)
        
    def get_values(self, model):
        cr, uid, context = request.cr, request.uid, request.context
        klass = request.registry.get(model)
        resource_ids = klass.search(cr, SUPERUSER_ID, [], context=context)
        return klass.browse(cr, SUPERUSER_ID, resource_ids, context=context)
    
    def do_add_product(self, qcontext):
        cals = {
            'name': qcontext['name'],
            'product_manager': request.uid,
            'sale_ok': True,
            'website_published': True,
            'commodity_id': qcontext['commodity'],
            'variety_id': qcontext['variety']
        }
        commodity = request.registry['product.template.commodity']
        cid = commodity.create(request.cr, request.uid, cals, request.context)
        
        vals = {
            'product_commodity_id': cid,
            'website_published': True,
            'package': qcontext['package']
        }
        variant = request.registry['product.commodity.variant']
        variant.create(request.cr, request.uid, vals, request.context)
        
        request.cr.commit()
