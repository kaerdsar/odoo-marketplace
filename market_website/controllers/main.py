# -*- coding: utf-8 -*-
import werkzeug

from openerp import SUPERUSER_ID
from openerp import http
from openerp.http import request
from openerp.tools.translate import _

class market_portal(http.Controller):
    def pricing(self, page=0, category=None, search='', **post):
        pass
