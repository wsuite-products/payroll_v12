# Copyright 2019-TODAY Kunjal Patel <kunjalpatel@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
from collections import OrderedDict

from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.tools import image_resize_image
from odoo.tools.translate import _
from odoo.addons.portal.controllers.portal import pager as portal_pager, \
    CustomerPortal
from odoo.addons.web.controllers.main import Binary


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = [request.env.user.partner_id.id]
        if request.env.user.partner_id.parent_id:
            partner.append(request.env.user.partner_id.parent_id.id)
        values['rfq_count'] = request.env['vendor.rfq'].search_count([
            ('state', 'in', ['in_progress', 'done']),
            ('vendor_ids', 'in', partner)
        ])
        values['purchase_count'] = request.env['purchase.order'].search_count([
            ('partner_id', 'in', partner)
        ])
        values['user_id'] = request.env.user
        return values

    def _rfq_order_get_page_view_values(self, order, access_token, **kwargs):
        #
        def resize_to_48(b64source):
            if not b64source:
                b64source = base64.b64encode(Binary().placeholder())
            return image_resize_image(b64source, size=(48, 48))

        values = {
            'rfq_order': order,
            'resize_to_48': resize_to_48,
        }
        return self._get_page_view_values(order, access_token, values,
                                          'my_rfq_history', True, **kwargs)

    @http.route(['/my/rfq', '/my/rfq/page/<int:page>'], type='http',
                auth="user", website=True)
    def portal_my_rfq_orders(self, page=1, date_begin=None, date_end=None,
                             sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = [request.env.user.partner_id.id]
        if request.env.user.partner_id.parent_id:
            partner.append(request.env.user.partner_id.parent_id.id)
        RFQ_Order = request.env['vendor.rfq']
        #
        domain = [('vendor_ids', 'in', partner)]
        #
        archive_groups = self._get_archive_groups('vendor.rfq', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin),
                       ('create_date', '<=', date_end)]
        searchbar_sortings = {
            'date':
                {'label': _('Newest'), 'order': 'create_date desc, id desc'},
            'name': {'label': _('Name'), 'order': 'name asc, id asc'}
        }
        # # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        # Remove Drft state after done code.
        searchbar_filters = {
            'all': {'label': _('All'),
                    'domain': [('state', 'in', ['in_progress', 'done'])]},
            'in_progress': {'label': _('In Progress Order'),
                            'domain': [('state', '=', 'in_progress')]},
            'done': {'label': _('Locked'), 'domain': [('state', '=', 'done')]}
        }
        # # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        #
        # # count for pager
        rfq_count = RFQ_Order.search_count(domain)
        # # make pager
        pager = portal_pager(
            url="/my/rfq",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=rfq_count,
            page=page,
            step=self._items_per_page
        )
        # # search the purchase orders to display, according to the pager data
        orders = RFQ_Order.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        request.session['my_rfq_history'] = orders.ids[:100]
        #
        values.update({
            'date': date_begin,
            'orders': orders,
            'page_name': 'rfq',
            'pager': pager,
            'archive_groups': archive_groups,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters':
                OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'default_url': '/my/rfq',
        })
        return request.render("vendor_portal_product.portal_my_rfq_orders",
                              values)

    @http.route(['/my/rfq/<int:order_id>'], type='http', auth="public",
                website=True)
    def portal_my_rfq(self, order_id=None, access_token=None, **kw):
        partner = [request.env.user.partner_id.id]
        if request.env.user.partner_id.parent_id:
            partner.append(request.env.user.partner_id.parent_id.id)
        try:
            order_sudo = self._document_check_access('vendor.rfq', order_id,
                                                     access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._rfq_order_get_page_view_values(order_sudo,
                                                      access_token, **kw)
        rfq_id = values.get('rfq_order')
        values.update({'vendor_rfq': rfq_id})
        values.update({'msg_reject': ''})
        vendor_rfq_line = rfq_id.mapped(
            'rfq_line_ids').filtered(lambda m: m.vendor_id.id in partner)
        if vendor_rfq_line:
            values.update(
                {'vendor_rfq_line': vendor_rfq_line, 'rfq_id': rfq_id})
        # if not vendor_rfq:
        #     values.update({'vendor_price': 0.0})
        # else:
        #     values.update({'vendor_price': vendor_rfq.rfq_price,
        #                    'vendor_note': vendor_rfq.note,
        #                    'vendor_del_date': vendor_rfq.del_date})
        # if vendor_rfq and rfq_id.state == 'in_progress':
        #     values.update({'msg_submit': "Thanks! "
        #                                  "We have received your quote."})
        # elif vendor_rfq and rfq_id.state == 'done' and \
        #         vendor_rfq.vendor_id != rfq_id.vendor_id:
        #     values.update(
        #         {'msg_reject': "We regret that your "
        #                        "quote has not been accepted."})
        # elif vendor_rfq and rfq_id.state == 'done' and \
        #         vendor_rfq.vendor_id == rfq_id.vendor_id and not \
        #         rfq_id.purchase_id:
        #     values.update(
        #         {'msg_accept': 'Congratulations! '
        #                        'we have accepted your quotation'})
        # elif vendor_rfq and rfq_id.state == 'done' and \
        #         vendor_rfq.vendor_id == rfq_id.vendor_id and \
        #         rfq_id.purchase_id:
        #     values.update(
        #         {'msg_po': "Congratulations! "
        #                    "A Purchase Order has been created."})
        return request.render("vendor_portal_product.portal_my_rfq_order",
                              values)

    @http.route('/submit/myprice', type='http', auth='user', website=True)
    def clock_time(self, **post):
        if post.get('rfq_template_line_id'):
            price_unitary = qty = '0'
            note = file = ''
            del_date = False
            if post.get('inputPrice', ''):
                price_unitary = post.get('inputPrice', '')
            if post.get('inputQuantity', ''):
                qty = post.get('inputQuantity', '')
            if post.get('inputNote', ''):
                note = post.get('inputNote', '')
            if post.get('inputFile', ''):
                file = post.get('inputFile', '')
            if post.get('inputDelivery', ''):
                del_date = post.get('inputDelivery', '')
            rfq_template_line_id = request.env[
                'vendor.rfq.line.template'].browse(
                    int(post.get('rfq_template_line_id', '')))
            rfq_template_line_id.write({
                'price_unitary': price_unitary,
                'qty': qty,
                'del_date': del_date,
                'note': note,
                'file': file})
            crm_lead_line =\
                rfq_template_line_id.vrfq_line_id.rfq_id.crm_lead_line_id
            profit_price_total = ((100.00 + crm_lead_line.profit_percentage
                                   ) * float(price_unitary) *
                                  float(qty)) /\
                100.00
            rfq_template_line_id.write(
                {'profit_price_total': profit_price_total})
        url = '/my/rfq/' + str(post.get('rfq_id'))
        return request.redirect(url)

    @http.route(['/my/purchase', '/my/purchase/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_purchase_orders(
            self, page=1, date_begin=None,
            date_end=None, sortby=None, filterby=None, **kw):
        # Overwrite method
        values = self._prepare_portal_layout_values()
        partner = [request.env.user.partner_id.id]
        if request.env.user.partner_id.parent_id:
            partner.append(request.env.user.partner_id.parent_id.id)
        PurchaseOrder = request.env['purchase.order']

        domain = [('partner_id', 'in', partner)]

        archive_groups = self._get_archive_groups('purchase.order', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin),
                       ('create_date', '<=', date_end)]

        searchbar_sortings = {
            'date': {'label': _('Newest'),
                     'order': 'create_date desc, id desc'},
            'name': {'label': _('Name'), 'order': 'name asc, id asc'},
            'amount_total': {'label': _('Total'),
                             'order': 'amount_total desc, id desc'},
        }
        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
            'all': {'label': _('All'), 'domain':
                    []},
            'purchase': {'label': _('Purchase Order'),
                         'domain': [('state', '=', 'purchase')]},
            'cancel': {'label': _('Cancelled'),
                       'domain': [('state', '=', 'cancel')]},
            'done': {'label': _('Locked'), 'domain': [('state', '=', 'done')]},
        }
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        # count for pager
        purchase_count = PurchaseOrder.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/purchase",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=purchase_count,
            page=page,
            step=self._items_per_page
        )
        # search the purchase orders to display, according to the pager data
        orders = PurchaseOrder.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        request.session['my_purchases_history'] = orders.ids[:100]

        values.update({
            'date': date_begin,
            'orders': orders,
            'page_name': 'purchase',
            'pager': pager,
            'archive_groups': archive_groups,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(
                sorted(searchbar_filters.items())),
            'filterby': filterby,
            'default_url': '/my/purchase',
        })
        return request.render("purchase.portal_my_purchase_orders", values)
