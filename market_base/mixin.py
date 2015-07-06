# -*- coding: utf-8 -*-
import datetime as dt
import openerp
from openerp import models, fields, api, SUPERUSER_ID
from openerp.tools import config
from openerp.addons.saas_utils import connector
from openerp.exceptions import ValidationError


class PublishMixin(models.AbstractModel):
    _name = 'publish.mixin'

    published = fields.Boolean('Published')
    publish_date = fields.Datetime('Last Published Date')
    to_send = fields.Boolean('To Send', default=False)
    flow = fields.Char('Flow')
    
    internal_flow = fields.Boolean(compute='_is_internal_flow',
                                   string='Internal Flow')
    
    @api.model
    def create(self, vals):
        if hasattr(self, 'partner_id'):
            vals['flow'] = self.env['b2b.flow'].register_flow(self._name, vals)
        return super(PublishMixin, self).create(vals)

    @api.multi
    def write(self, vals):
        res = super(PublishMixin, self).write(vals)
        if ('to_send' not in vals) and ('message_last_post' not in vals) \
                                   and ('message_follower_ids' not in vals) \
                                   and ('receive_object' not in self.env.context) \
                                   and (vals.get('state', False) != 'sent'):
            for obj in self:
                self.env.cr.execute("update " + self._table + " set to_send = %s where id = %s", (True, obj.id))
        return res

    @api.one
    def publish(self):
        res = self.env['cenit.flow'].send(self)
        if res:
            vals = {
                'published': True,
                'publish_date': dt.datetime.now(),
                'to_send': False
            }
            self.write(vals)
        return res

    @api.one
    def publish_to_master(self):
        db = config.get('db_master')
        return self.with_context(partner_db=db).publish()

    @api.one
    def unpublish_from_master(self):
        db_master = config.get('db_master')
        model = self.env.context.get('master_model', self._name)
        domain = [('name', '=', self.name)]
        oids = connector.call(db_master, model, 'search', domain)
        res = connector.call(db_master, model, 'unlink', oids)
        if res:
            self.write({'published': False})
        return res

    @api.one
    def exists_partner(self):
        assert hasattr(self, 'partner_id'), "The object doesn't have partner_id"
        data = connector.call(config.get('db_master'), 'res.users', 'search_read',
                              [('organization', '=', self.partner_id.name)],
                              ['database', 'partner_id'])
        return data and data[0] or False
        
    @api.one
    def _is_internal_flow(self):
        partner = self.exists_partner()
        self.internal_flow = (partner and partner[0]) and True or False

    @api.one
    def publish_to_partner(self):
        if not self.env.context.get('partner_db', False):
            assert hasattr(self, 'partner_id'), "Field partner_id not present."
            data = connector.call(config.get('db_master'),
                                  'res.users', 'search_read',
                                  [('organization', '=', self.partner_id.name)],
                                  ['database'])
            if not data:
                return False
            db = data[0]['database']
        return self.with_context(partner_db=db).publish()

    @api.one
    def message_post(self, **kwargs):
        receive_object = self.env.context.get('receive_object', False)
        if receive_object and hasattr(self, 'partner_id'):
            if self.partner_id not in self.message_follower_ids:
                self.message_subscribe([self.partner_id.id])
            kwargs['author_id'] = self.partner_id.id
            kwargs['partner_ids'] = [self.env.user.partner_id.id]
        res = super(PublishMixin, self).message_post(**kwargs)
        #if not receive_object and kwargs.get('type') == 'comment' \
        #                      and kwargs.get('subtype') == 'mail.mt_comment':
        #    self._send_comment(**kwargs)
        return res
        
    @api.one
    def _send_comment(self, **kwargs):
        user = self.exists_partner()
        if user:
            db = user['database']
            registry = openerp.modules.registry.RegistryManager.get(db)
            with registry.cursor() as db_cr:
                model = registry[self._get_partner_model(obj._name)]
                model_ids = model.search(db_cr, SUPERUSER_ID,
                                         [('name', '=', obj.name)])
                if model_ids:
                    ctx = {'receive_object': True}
                    model.message_post(db_cr, SUPERUSER_ID, model_ids[0],
                                       body=kwargs.get('body', ''),
                                       subject=kwargs.get('subject', None),
                                       type=kwargs.get('type', 'notification'),
                                       subtype=kwargs.get('subtype', None),
                                       context=ctx)

    def _get_partner_model(self, model):
        m = {'sale.order': 'purchase.order', 'purchase.order': 'sale.order'}
        return m.get(model, model)
         


class CatalogMixin(models.AbstractModel):
    _name = 'catalog.mixin'

    def read(self, cr, uid, ids, fields=None, context=None,
             load='_classic_read'):
        args = (ids, fields, context, load)
        context = context or {}
        if context.get('catalog_db', False):
            db = config.get(context['catalog_db'])
            res = connector.call(db, self._name, 'read', *args)
            return res
        return super(CatalogMixin, self).read(cr, uid, *args)

    def search_read(self, cr, uid, domain=None, fields=None, offset=0,
                    limit=None, order=None, context=None):
        args = (domain, fields, offset, limit, order, context)
        context = context or {}
        if context.get('catalog_db', False):
            db = config.get(context['catalog_db'])
            return connector.call(db, self._name, 'search_read', *args)
        return super(CatalogMixin, self).search_read(cr, uid, *args)

    def read_group(self, cr, uid, domain, fields, groupby, offset=0,
                   limit=None, context=None, orderby=False, lazy=True):
        args = (domain, fields, groupby, offset, limit, context, orderby, lazy)
        context = context or {}
        if context.get('catalog_db', False):
            db = config.get(context['catalog_db'])
            return connector.call(db, self._name, 'read_group', *args)
        return super(CatalogMixin, self).read_group(cr, uid, *args)

    @api.cr_uid
    def pull_from_catalog(self, cr, uid, oid):
        wh = self.pool.get('cenit.handler')
        vals = connector.call(config.get('db_master'), 'cenit.serializer',
                              'serialize_model_id', self._name, oid)
        return wh.add(cr, 1, vals, self._get_root(cr, uid, self._name))

    @api.cr_uid
    def pull_from_catalog_by(self, cr, uid, field, value):
        domain = [(field, '=', value)]
        oids = connector.call(config.get('db_master'), self._name, 'search',
                              domain)
        if not oids:
            raise ValidationError('''It could not find the object %s
                                    in catalog''' % value)
        return self.pull_from_catalog(cr, uid, oids[0])

    @api.cr_uid
    def search_in_catalog(self, cr, uid, name):
        res = connector.call(config.get('db_master'), self._name, 'search',
                             [('name', '=', name)])
        return res and res[0] or False

    def _get_root(self, cr, uid, model):
        wdt = self.pool.get('cenit.data.type')
        matching_id = wdt.search(cr, uid, [('model_id.model', '=', model)])
        if matching_id:
            return wdt.browse(cr, uid, matching_id[0]).name
        return False


class ShippingMixin(models.AbstractModel):
    _name = 'shipping.mixin'

    mode_of_payment = fields.Selection([('bank', 'Bank Transfer'),
                                        ('check', 'Check'),
                                        ('credit', 'Letter or Credit'),
                                        ('escrow', 'Reserva Escrow')],
                                         'Mode of Payment')
    mode_of_transport = fields.Selection([('air', 'Air'),
                                          ('sea', 'Sea'),
                                          ('land', 'Land')],
                                         'Mode of Transport')
    carrier = fields.Char('Carrier', size=64)
    city_of_origin = fields.Char('City of Origin', size=64)
    departure_port = fields.Char('Departure Port', size=64)
    arrival_port = fields.Char('Arrival Port', size=64)
    destination_city = fields.Char('Destination City', size=64)
    awb_bl_number = fields.Char('AWB/BL number', size=64)
    shipping_date = fields.Date('Shipping Date')
