# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    @api.depends('order_line')
    def _compute_total_hours(self):
        for record in self:
            record.hours = sum([line.hours for line in record.order_line if not line.check_ads_service])

    hours = fields.Float(compute='_compute_total_hours')
    comment_ids = fields.One2many('order.line.comment', 'order_id', string='Comments')
    fee_amount = fields.Float()
    quotation_ax = fields.Char()
    revision_ax = fields.Char()
    quotation_number = fields.Char('#Quotation Number')
    fee_check = fields.Boolean('Fee?')

    @api.multi
    def _compute_count_manufacturing_orders(self):
        for record in self:
            record.manufacturing_order_count = self.env['mrp.production'].search_count([('origin', '=', record.name)])

    manufacturing_order_count = fields.Integer(string='Manufacturing Orders', compute='_compute_count_manufacturing_orders')
    product_template_ids = fields.Many2many('product.template', string='Product Templates')

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        MO_object = self.env['mrp.production']
        PO_object = self.env['purchase.order']
        POL_object = self.env['purchase.order.line']
        WC_object = self.env['workorder.comment']
        PO_List = []
        Supplier_List = []
        SOL_object = self.env['sale.order.line']

        as_percentage = self.opportunity_id.brand_id.advertising_services_percentage
        for line in self.order_line:
            purchase_order_id = False
            purchase_order_line_id = False
            if line.res_supplier_id:
                if line.res_supplier_id not in Supplier_List:
                    purchase_order_id = PO_object.create({
                        'partner_id': line.res_supplier_id.id,
                        'so_id': line.order_id.id,
                        'quotation_number': line.quotation_number,
                        'order_line': [(0, 0, {
                            'name': line.name,
                            'product_id': line.product_id.id,
                            'product_qty': line.product_uom_qty,
                            'product_uom': line.product_uom.id,
                            'price_unit': line.price_unit,
                            'date_planned': fields.Datetime.now(),
                            'crm_lead_line_id': line.crm_lead_line_id.id,
                            'quotation_number': line.quotation_number,
                            'order_line_id': line.id,
                         })]
                    })
                    PO_List.append(purchase_order_id)
                    Supplier_List.append(purchase_order_id.partner_id)
                    purchase_order_line_id = purchase_order_id.order_line[0]
                else:
                    purchase_order_id = [po_id for po_id in PO_List if po_id.partner_id == line.res_supplier_id]
                    purchase_order_id = purchase_order_id and purchase_order_id[0]
                    vals = {
                        'name': line.name,
                        'product_id': line.product_id.id,
                        'product_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'price_unit': line.price_unit,
                        'date_planned': fields.Datetime.now(),
                        'order_id': purchase_order_id and purchase_order_id.id,
                        'crm_lead_line_id': line.crm_lead_line_id.id,
                        'quotation_number': line.quotation_number,
                        'order_line_id': line.id,
                     }
                    purchase_order_line_id = POL_object.create(vals)
            for qty in range(0, int(line.product_uom_qty)):
                for bom_id in line.product_id.mapped('variant_bom_ids'):
                    mo_id = MO_object.create({
                        'quotation_number': line.quotation_number,
                        'product_id': line.product_id.id or bom_id.product_id.id,
                        'product_qty': 1,
                        'bom_id': bom_id.id,
                        'product_uom_id': line.product_uom.id or bom_id.product_uom_id.id,
                        'sale_order_id': self.id,
                        'sale_order_line_id': line.id,
                        'origin': self.name,
                        'task_assignee_config': line.crm_lead_line_id.task_assignee_config,
                        'purchase_order_id': purchase_order_id and purchase_order_id.id,
                        'purchase_order_line_id': purchase_order_line_id and purchase_order_line_id.id,
                        'lead_id': self.opportunity_id.id,
                        'lead_line_id': line.crm_lead_line_id.id,
                        'brand_id': self.opportunity_id.brand_id.id,
                    })
                    if line.crm_lead_line_id.quote_type in ['PR', 'DC', 'IW']:
                        WC_object.create({
                            'production_id': mo_id.id,
                            'attachment_url': line.product_id.image_url,
                            'comment': line.product_id.product_name,
                            'type': 'attachment',
                        })
                    mo_id.button_plan()
            if line.crm_lead_line_id.quote_type in ['DC', 'EP'] or line.crm_lead_line_id.media_config:
                if not as_percentage > 0:
                    continue
                # price_unit = line.price_unit * line.product_uom_qty
                price_unit = line.price_unit
                SOL_object.create({
                    'name': line.name,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_id.uom_po_id.id,
                    'product_uom_qty': line.product_uom_qty,
                    'res_supplier_id': line.res_supplier_id.id,
                    'order_date': line.order_date,
                    'product_tmpl_id': line.product_id.product_tmpl_id.id,
                    'hours': line.hours,
                    'price_unit': (price_unit * as_percentage) / 100,
                    'price': (line.price * as_percentage) / 100,
                    'crm_lead_line_id': line.crm_lead_line_id.id,
                    'quotation_number': line.quotation_number,
                    'check_ads_service': True,
                    'tax_id': [(6, 0, [])],
                    'discount': 0.0,
                    'order_id': line.order_id.id
                     })
        check = False
        for op_id in self.opportunity_id.crm_lead_line_ids:
            if op_id.order_line_id:
                check = True
            else:
                check = False
                break
        if check:
            self.opportunity_id.status_info = 'In Production'
        self.env['webhook'].action_webhook_create_form_data_common(15, self)
        return res

    @api.multi
    def action_cancel_api(self, sale_order_id=None):
        if sale_order_id:
            so_id = self.browse([sale_order_id])
            mrp_production_ids = self.env['mrp.production'].search([
                '|', ('origin', '=', so_id.name),
                ('sale_order_id', '=', sale_order_id)])
            if mrp_production_ids:
                [mrp_production_id.action_cancel() for mrp_production_id in mrp_production_ids]
            purchase_order_ids = self.env['purchase.order'].search(['|', ('origin', '=', so_id.name), ('so_id', '=', sale_order_id)])
            if purchase_order_ids:
                purchase_order_ids.button_cancel()
            so_id.action_cancel()
            _logger.info("Sale/Manufacturing/Purchase Order Cancelled successfully related to Sale Order!")
            return "Sale/Manufacturing/Purchase Order Cancelled successfully related to Sale Order!"
        else:
            _logger.info("Please provide the Sale Order id!")
            return "Please provide the Sale Order id!"

    @api.multi
    def action_view_mo_details(self):
        mo_ids = self.env['mrp.production'].search([('origin', '=', self.name)])
        action = self.env.ref('mrp.mrp_production_action').read()[0]
        if len(mo_ids) > 1:
            action['domain'] = [('id', 'in', mo_ids.ids)]
        elif len(mo_ids) == 1:
            action['views'] = [(self.env.ref('mrp.mrp_production_form_view').id, 'form')]
            action['res_id'] = mo_ids.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def create_budget(self):
        adv_wiz = self.env['sale.advance.payment.inv'].with_context(active_ids=[self.id]).create({
            'advance_payment_method': 'all',
        })
        act = adv_wiz.with_context(open_invoices=True).create_invoices()
        invoice_id = self.env['account.invoice'].browse(act['res_id'])
        return invoice_id.read()


class OrderLineComment(models.Model):
    _name = 'order.line.comment'
    _description = 'Order Line Comment'

    sequence = fields.Integer('Sequence', default=10)
    # line_id = fields.Many2one(
    #     'sale.order.line', string='Order Line',
    #     ondelete='cascade')
    comment = fields.Text('Comments')
    user_id = fields.Many2one('res.users')
    attachment = fields.Binary('Attachment')
    file_name = fields.Char("File Name")
    attachment_url = fields.Char('Attachment URL')
    # product_id = fields.Many2one('product.product', related='line_id.product_id', string='Product')
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Product Template')
    # crm_lead_line_id = fields.Many2one('crm.lead.lines', related='line_id.crm_lead_line_id', string='CRM Lead Line')
    order_id = fields.Many2one('sale.order', string='Sale Order')
    lead_line_id = fields.Many2one('crm.lead.lines', string='Lead Line')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    hours = fields.Float()
    crm_lead_line_id = fields.Many2one('crm.lead.lines', 'CRM Lead Line')
    # comment_ids = fields.One2many(
    #     'order.line.comment',
    #     'line_id',
    #     string='Comments')
    order_date = fields.Date('Date')
    product_tmpl_id = fields.Many2one(related='product_id.product_tmpl_id', string='Product Template')
    price = fields.Float('Unit Price')
    line_number = fields.Float()
    line_property = fields.Char()
    ax_id = fields.Char()
    transaction_type = fields.Char()
    res_supplier_id = fields.Many2one('res.partner', 'Supplier', domain="[('supplier', '=', True)]")
    quotation_number = fields.Char('#Quotation Number')
    check_ads_service = fields.Boolean('Advertising Services?')

    @api.model
    def create(self, vals):
        res = super(SaleOrderLine, self).create(vals)
        if res.crm_lead_line_id and not res.check_ads_service:
            res.crm_lead_line_id.write({'order_line_id': res.id})
        return res

    @api.multi
    def unlink(self):
        for record in self:
            record.crm_lead_line_id.write({'order_line_id': False})
        return super(SaleOrderLine, self).unlink()


class CRMLeadLines(models.Model):
    _inherit = 'crm.lead.lines'

    comment_ids = fields.One2many('order.line.comment', 'lead_line_id', string='Comments')