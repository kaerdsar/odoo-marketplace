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

PRODUCT_FIELDS = []
CATEGORY_NAME = 'Wines'

class WebsiteSaleSeller(http.Controller):
        
    @http.route('/seller/add_product', type='http', auth='user', website=True)
    def add_product(self, *args, **kw):
        qcontext = request.params.copy()
        qcontext['new'] = True
        qcontext['success'] = False
        
        for field in PRODUCT_FIELDS:
            if not qcontext.get(field['name']):
                qcontext[field['name']] = self.get_values(field['model'])
        
        categories = self.get_values('product.category')
        for category in categories:
            if category.name == CATEGORY_NAME:
                qcontext['category'] = category 
            
        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                self.do_add_product(qcontext)
                if 'create_and_finish' in kw:
                    return request.redirect('/saas_server/tenant')
                qcontext['success'] = True
                qcontext['name'] = False
            except Exception, e:
                qcontext['error'] = _(e.message)

        return request.render('market_portal.add_product', qcontext)
        
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
            'categ_id': qcontext['category'].id,
        }
        for attribute in qcontext['category'].product_attributes:
			if attribute.name in qcontext:
				cals[attribute.name] = qcontext[attribute.name]
        product = request.registry['product.template']
        cid = product.create(request.cr, request.uid, cals, {'category':qcontext['category'].name})
        
        product_obj = product.browse(request.cr, request.uid, cid, request.context)
        for line in product_obj.attribute_line_ids:
            if line.attribute_id.name in qcontext:
                id_ = None
                for value in line.attribute_id.value_ids:
                    if value.name == qcontext[line.attribute_id.name]:
                        id_ = value.id
                if id_ is None:
                    id_ = line.attribute_id.create({'name':qcontext[line.attribute_id.name]})
                line.write({'value_ids': [(4, id_)]})
        vals = {
            'product_tmpl_id': cid,
            'website_published': True,
            'categ_id': qcontext['category'].id,
        }
        for attribute in qcontext['category'].variant_attributes:
			if attribute.name in qcontext:
				vals[attribute.name] = qcontext[attribute.name]
        variant = request.registry['product.product']
        variant.create(request.cr, request.uid, vals, request.context)
        
        request.cr.commit()
