from openerp import http
from openerp.http import request
from openerp.addons.website_sale.controllers.main import website_sale

class website_sale(website_sale):
	
    @http.route(['/shop/add_to_cart'], type='http', auth="public", methods=['POST'], website=True)
    def my_cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        cr, uid, context = request.cr, request.uid, request.context
        request.website.sale_get_order(force_create=1)._cart_update(product_id=int(product_id), add_qty=float(add_qty), set_qty=float(set_qty))
