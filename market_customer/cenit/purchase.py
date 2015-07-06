# -*- coding: utf-8 -*-
import openerp
from openerp import models
from openerp.osv import fields

STATES_OUT = {
    'bid': 'bid-sent',
    'confirmed': 'confirmed-to_approve',
    'approved': 'approved-progress'
}

STATES_IN = {
    'draft-bid': 'bid_received',
    'sent-bid': 'bid_received',
    'to_approve-confirmed': 'purchase_confirm',
    'progress-approved': 'purchase_approve'
}


class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = 'purchase.order'

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
        new_vals['product_qty'] = vals['quantity']
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
        company = self.pool.get('res.company')
        company_ids = company.search(cr, uid,
                                     [('name', '=', value['firstname'])],
                                     context=context)
        if not company_ids:
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
        purchase_line = self.pool.get('purchase.order.line')
        context = context or {}
        lines = []
        for var in value:
            vals = self._convert(cr, uid, var, context)
            domain = [
                ('order_id', '=', oid),
                ('product_id', '=', vals['product_id']),
                ('name', '=', vals['name']),
            ]
            pl_ids = purchase_line.search(cr, uid, domain)
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
                var['quantity'] = line.product_qty
                lines.append(var)
            result[obj.id] = lines
        return result

    _columns = {
        'status': fields.function(_get_status, method=True, type='char',
                                  fnct_inv=_set_status),
        'reference': fields.function(_get_reference, method=True, type='char',
                                     fnct_inv=_set_reference),
        'billing_address': fields.function(_get_company, method=True,
                                            type='char', fnct_inv=_set_company,
                                            priority=1),
        'line_items': fields.function(_get_lines, method=True, type='char',
                                      fnct_inv=_set_lines, priority=4)
    }


class PurchaseRequisition(models.Model):
    _name = 'purchase.requisition'
    _inherit = 'purchase.requisition'

    def _get_resource(self, cr, uid, model_name, resource_name):
        model = self.pool.get('market.%s' % model_name)
        res_ids = model.search(cr, uid, [('name', '=', resource_name)])
        return res_ids and res_ids[0] or False

    def _set_lines(self, cr, uid, oid, name, value, args, context=None):
        line = self.pool.get('market.request.line')
        context = context or {}
        for var in value:
            vals = {}
            vals['requisition_id'] = oid
            vals['product_qty'] = var['quantity']
            for x in ['commodity', 'variety', 'package']:
                vals['%s_id' % x] = self._get_resource(cr, uid, x, var[x])
            line.create(cr, uid, vals)
        return True

    def _get_lines(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            lines = []
            for line in obj.line_ids:
                var = {}
                var['commodity'] = line.commodity_id.name
                var['variety'] = line.variety_id.name
                var['package'] = line.package_id.name
                var['quantity'] = line.product_qty
                lines.append(var)
            result[obj.id] = str(lines)
        return result

    def _get_partner(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = {
                'firstname': obj.company_id.partner_id.name,
                'email': obj.company_id.partner_id.name
            }
        return result

    def _get_country(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = obj.country.name
        return result

    def _get_destination(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = obj.destination.name
        return result

    _columns = {
        'request_detail': fields.function(_get_lines, method=True,
                                           type='char', fnct_inv=_set_lines),
        'partner_id': fields.function(_get_partner, method=True, type='char'),
        'country_id': fields.function(_get_country, method=True, type='char'),
        'destination_id': fields.function(_get_destination, method=True, type='char')
    }
