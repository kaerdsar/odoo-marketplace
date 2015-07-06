# -*- coding: utf-8 -*-
import openerp
from openerp import models
from openerp.osv import fields

STATES_OUT = {
    'draft': 'draft-bid',
    'sent': 'sent-bid',
    'to_approve': 'to_approve-confirmed',
    'progress': 'progress-approved'
}

STATES_IN = {
    'bid-sent': 'quotation_sent',
    'confirmed-to_approve': 'order_to_approve',
    'approved-progress': 'order_confirm'
}


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    def _get_resource(self, cr, uid, model, name, context={}):
        domain = [('name', '=', name)] + context.get('add_domain', [])
        res = self.pool.get(model).search(cr, uid, domain, context=context)
        return res and res[0] or False

    def _convert(self, cr, uid, vals, context=None):
        new_vals = {}
        new_vals['name'] = vals['name']
        context = context or {}
        context.update({'add_domain': [('variant', '=', vals['variant'])]})
        new_vals['product_id'] = self._get_resource(cr, uid, 'product.product', vals['product'], context)
        new_vals['price_unit'] = vals['price']
        new_vals['product_uom_qty'] = vals['quantity']
        return new_vals

    def _set_status(self, cr, uid, oid, name, value, args, context=None):
        context = context or {}
        if value in STATES_IN:
            self.signal_workflow(cr, uid, [oid], STATES_IN[value], context=context)
            if context.get('receive_object', False):
                self.write(cr, uid, oid, {'to_send': False}, context)
        return True

    def _get_status(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = STATES_OUT.get(obj.state, obj.state)
        return result
        
    def _set_reference(self, cr, uid, oid, name, value, args, context=None):
        return self.write(cr, uid, oid, {'origin': value}, context)

    def _get_reference(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = obj.name
        return result

    def _set_company(self, cr, uid, oid, name, value, args, context=None):
        return True
        company = self.pool.get('res.company')
        domain = [('name', '=', value['firstname'])]
        if company.search(cr, uid, domain, context=context):
            # This order is not for this company
            raise openerp.exceptions.AccessDenied()
        return True

    def _get_company(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            partner = obj.company_id.partner_id
            var = {}
            var['firstname'] = partner.name
            var['email'] = partner.email
            var['address1'] = partner.street
            var['address2'] = partner.street2
            var['city'] = partner.city
            var['state'] = partner.state_id and partner.state_id.name or False
            var['country'] = partner.country_id and partner.country_id.name or False
            var['phone'] = partner.phone
            var['zipcode'] = partner.zip
            result[obj.id] = var
        return result

    def _set_lines(self, cr, uid, oid, name, value, args, context=None):
        sale_line = self.pool.get('sale.order.line')
        context = context or {}
        lines = []
        for var in value:
            vals = self._convert(cr, uid, var, context)
            domain = [
                ('order_id', '=', oid),
                ('product_id', '=', vals['product_id']),
                ('name', '=', vals['name']),
            ]
            pl_ids = sale_line.search(cr, uid, domain)
            lines.append(pl_ids and (1, pl_ids[0], vals) or (0, 0, vals))
        if lines:
            self.write(cr, uid, oid, {'order_line': lines}, context)

    def _get_lines(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            lines = []
            for line in obj.order_line:
                var = {}
                var['name'] = line.name
                var['product'] = line.product_id.name
                var['variant'] = line.product_id.variant
                var['price'] = line.price_unit
                var['quantity'] = line.product_uom_qty
                lines.append(var)
            result[obj.id] = lines
        return result

    _columns = {
        'status': fields.function(_get_status, method=True, type='char',
                                  fnct_inv=_set_status),
        'reference': fields.function(_get_reference, method=True, type='char',
                                     fnct_inv=_set_reference),
        'supplier_address': fields.function(_get_company, method=True,
                                            type='char', fnct_inv=_set_company,
                                            priority=1),
        'line_items': fields.function(_get_lines, method=True, type='char',
                                      fnct_inv=_set_lines, priority=2)
    }
