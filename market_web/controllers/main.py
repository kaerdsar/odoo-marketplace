# -*- coding: utf-8 -*-
import openerp
from openerp import SUPERUSER_ID
from openerp.addons.web import http
from openerp.addons.web.http import request
import werkzeug
import simplejson
import uuid
import random
try:
	import stripe
except:
	pass
from openerp.tools import config
    
class MarketWebPortal(http.Controller):

    @http.route('/web/stripe_show_form', type='http', auth="public")
    def stripe_change_plan(self, **post):
        user = request.registry.get('res.users').browse(request.cr,
                                                        SUPERUSER_ID,
                                                        request.uid)
        db = config.get('db_master')
        registry = openerp.modules.registry.RegistryManager.get(db)
        with registry.cursor() as cr:
            to_search = [('login', '=', user.login)]
            fields = ['email', 'password']
            data = registry['res.users'].search_read(cr, SUPERUSER_ID,
                                                     to_search, fields)
        if not data:
            return werkzeug.utils.redirect('/web')
        scheme = 'https'
        domain = db.replace('_', '.')
        login = data[0]['email']
        key =  data[0]['password']
        return werkzeug.utils.redirect('{scheme}://{domain}/web'.format(scheme=scheme, domain=domain))
