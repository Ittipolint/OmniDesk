import os
import re
from odoo import http
from odoo.http import request

# Shared secret with ChatDesk/n8n (local network only for phase 1).
# Override with env CHATDESK_ODOO_TOKEN in production; must match the token
# sent by n8n workflows api-13-odolead / api-14-odoo-outbox.
SHARED_TOKEN = os.environ.get('CHATDESK_ODOO_TOKEN', 'chatdesk-local-odoo-01')

OPEN_STAGES = [('stage_id.is_won', '=', False), ('stage_id.fold', '=', False)]


def _clean_phone(s):
    return re.sub(r'[^0-9]', '', s or '')


def _check(kw):
    if (kw.get('token') or '') != SHARED_TOKEN:
        return {'ok': False, 'error': 'bad token'}
    return None


class ChatDeskConnector(http.Controller):
    @http.route('/chatdesk/lead', type='json', auth='public', csrf=False, methods=['POST'])
    def chatdesk_lead(self, **kw):
        try:
            body = request.get_json_data() or {}
            if isinstance(body, dict):
                kw = dict(body)
        except Exception:
            pass
        return self._upsert_order_lead(kw)

    def _upsert_order_lead(self, kw):
        err = _check(kw)
        if err:
            return err
        name = (kw.get('name') or 'ลูกค้า ShopDee')[:120]
        phone = _clean_phone(kw.get('phone'))
        if len(phone) < 9:
            return {'ok': False, 'error': 'bad phone'}
        address = (kw.get('address') or '')[:500]
        code = (kw.get('code') or '')[:64]
        total = kw.get('total') or 0
        channel = (kw.get('channel') or 'shopweb')[:32]
        items = kw.get('items') or []
        lines = []
        for it in items if isinstance(items, list) else []:
            if isinstance(it, dict):
                lines.append('- %s x%s = %s' % (it.get('name', ''), it.get('qty', 1), it.get('price', 0)))
        desc = ('Order %s total %s (%s)\n%s\naddr: %s\nnote: %s\nchannel: %s' % (
            code, total, kw.get('payment', ''), '\n'.join(lines)[:1200],
            address, (kw.get('note') or '')[:500], channel))[:2000]

        Partner = request.env['res.partner'].sudo()
        partner = Partner.search(['|', ('phone', '=', phone), ('mobile', '=', phone)], limit=1)
        if partner:
            pid = partner.id
        else:
            partner = Partner.create({
                'name': name, 'phone': phone, 'mobile': phone,
                'street': address, 'comment': 'from ShopDee channel %s' % channel,
            })
            pid = partner.id
        lead = request.env['crm.lead'].sudo().create({
            'name': ('ShopDee %s - %s' % (code, name))[:200],
            'partner_id': pid,
            'phone': phone,
            'description': desc,
            'type': 'lead',
        })
        return {'ok': True, 'partner_id': pid, 'lead_id': lead.id}

    @http.route('/chatdesk/chat-lead', type='json', auth='public', csrf=False, methods=['POST'])
    def chatdesk_chat_lead(self, **kw):
        try:
            body = request.get_json_data() or {}
            if isinstance(body, dict):
                kw = dict(body)
        except Exception:
            pass
        err = _check(kw)
        if err:
            return err
        channel = (kw.get('channel') or '')[:32]
        ext = (kw.get('external_user_id') or kw.get('userId') or '')[:128]
        if not channel or not ext:
            return {'ok': False, 'error': 'need channel + external_user_id'}
        ref = '%s:%s' % (channel, ext)
        display = (kw.get('display_name') or '')[:120]
        text = (kw.get('text') or '')[:500]
        Partner = request.env['res.partner'].sudo()
        partner = Partner.search([('ref', '=', ref)], limit=1)
        if partner:
            pid = partner.id
            if display and not partner.name.startswith(display):
                pass
        else:
            partner = Partner.create({
                'name': display or ('Guest %s' % ext[-6:]),
                'ref': ref,
                'comment': 'chat guest from %s' % channel,
            })
            pid = partner.id
        Lead = request.env['crm.lead'].sudo()
        open_leads = Lead.search([('partner_id', '=', pid)] + OPEN_STAGES, limit=1)
        if open_leads:
            lead = open_leads[0]
            if text:
                lead.description = ((lead.description or '') + '\n[%s] %s' % (channel, text))[:2000]
            return {'ok': True, 'partner_id': pid, 'lead_id': lead.id, 'reused': True}
        lead = Lead.create({
            'name': ('Chat %s - %s' % (channel, partner.name))[:200],
            'partner_id': pid,
            'description': ('First message from %s:\n%s' % (channel, text))[:2000],
            'type': 'lead',
        })
        return {'ok': True, 'partner_id': pid, 'lead_id': lead.id, 'reused': False}

    @http.route('/chatdesk/outbox-info', type='json', auth='public', csrf=False, methods=['POST'])
    def chatdesk_outbox_info(self, **kw):
        try:
            body = request.get_json_data() or {}
            if isinstance(body, dict):
                kw = dict(body)
        except Exception:
            pass
        err = _check(kw)
        if err:
            return err
        try:
            mid = int(kw.get('message_id') or 0)
        except Exception:
            mid = 0
        if not mid:
            return {'ok': False, 'error': 'need message_id'}
        msg = request.env['mail.message'].sudo().browse(mid)
        if not msg.exists() or msg.model != 'crm.lead' or msg.message_type != 'comment':
            return {'ok': False, 'error': 'not a lead comment'}
        st = msg.subtype_id
        if not st or st.internal:
            return {'ok': False, 'error': 'internal note skipped'}
        lead = request.env['crm.lead'].sudo().browse(msg.res_id)
        if not lead.exists():
            return {'ok': False, 'error': 'lead gone'}
        partner = lead.partner_id
        mm = re.match(r'^([a-z0-9_]{2,32}):(.+)$', (partner.ref or ''))
        if not mm:
            return {'ok': False, 'error': 'no chat ref'}
        text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', msg.body or '')).strip()[:2000]
        if not text:
            return {'ok': False, 'error': 'empty text'}
        return {'ok': True, 'channel': mm.group(1), 'external_user_id': mm.group(2),
                'display_name': partner.name or '', 'text': text,
                'lead_id': lead.id, 'message_id': msg.id}

    @http.route('/chatdesk/order', type='json', auth='public', csrf=False, methods=['POST'])
    def chatdesk_order(self, **kw):
        try:
            body = request.get_json_data() or {}
            if isinstance(body, dict):
                kw = dict(body)
        except Exception:
            pass
        err = _check(kw)
        if err:
            return err
        channel = (kw.get('channel') or 'shopweb')[:32]
        ext = (kw.get('external_user_id') or kw.get('userId') or '')[:128]
        name = (kw.get('name') or 'ลูกค้า')[:120]
        phone = _clean_phone(kw.get('phone'))
        if len(phone) < 9:
            return {'ok': False, 'error': 'bad phone'}
        address = (kw.get('address') or '')[:500]
        code = (kw.get('code') or '')[:64]
        total = kw.get('total') or 0
        payment = (kw.get('payment') or '')[:32]
        items = kw.get('items') if isinstance(kw.get('items'), list) else []

        Partner = request.env['res.partner'].sudo()
        by_phone = Partner.search(['|', ('phone', '=', phone), ('mobile', '=', phone)], limit=1)
        target = by_phone or None
        if ext:
            by_ref = Partner.search([('ref', '=', '%s:%s' % (channel, ext))], limit=1)
            if by_ref and (not target or by_ref.id != target.id):
                if not target:
                    # enrich chat guest record into the customer (single record per person)
                    by_ref.write({'name': name, 'phone': phone, 'mobile': phone,
                                  'street': address or by_ref.street})
                    target = by_ref
                else:
                    # move open chat leads onto the phone record
                    Lead = request.env['crm.lead'].sudo()
                    for ld in Lead.search([('partner_id', '=', by_ref.id)] + OPEN_STAGES):
                        ld.partner_id = target.id
        if not target:
            target = Partner.create({
                'name': name, 'phone': phone, 'mobile': phone, 'street': address,
                'ref': ('%s:%s' % (channel, ext)) if ext else False,
                'comment': 'customer from %s' % channel,
            })
        pid = target.id

        Product = request.env['product.product'].sudo()
        order_lines = []
        for it in items:
            if not isinstance(it, dict):
                continue
            sku = (it.get('sku') or '')[:64]
            pname = (it.get('name') or 'สินค้า')[:200]
            price = float(it.get('price') or 0)
            qty = float(it.get('qty') or 1)
            prod = None
            if sku:
                prod = Product.search([('default_code', '=', sku)], limit=1)
            if not prod:
                prod = Product.search([('name', '=', pname)], limit=1)
            if not prod:
                prod = Product.create({
                    'name': pname, 'default_code': sku or False,
                    'type': 'consu', 'list_price': price,
                    'invoice_policy': 'order',
                    'taxes_id': [(6, 0, [])],  # ราคาหน้าร้านรวมภาษีแล้ว ไม่คิด VAT ซ้ำใน Odoo
                })
            order_lines.append((0, 0, {'product_id': prod.id, 'product_uom_qty': qty,
                                       'price_unit': price}))
        if not order_lines:
            return {'ok': False, 'error': 'empty items'}
        so = request.env['sale.order'].sudo().create({
            'partner_id': pid,
            'origin': code,
            'note': 'ShopDee %s (%s) %s' % (code, payment, channel),
            'order_line': order_lines,
        })
        so.action_confirm()
        invoices = so._create_invoices()
        won = 0
        Lead = request.env['crm.lead'].sudo()
        for ld in Lead.search([('partner_id', '=', pid)] + OPEN_STAGES):
            try:
                ld.action_set_won()
                won += 1
            except Exception:
                continue
        return {'ok': True, 'partner_id': pid, 'sale_id': so.id,
                'sale_name': so.name, 'invoice_ids': invoices.ids, 'leads_won': won}
