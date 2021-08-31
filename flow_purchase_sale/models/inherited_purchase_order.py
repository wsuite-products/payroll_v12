# Copyright 2019-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api
import base64
import re


class PurchaseOrder(models.Model):
    """Added PO from SO feature."""

    _inherit = "purchase.order"

    so_id = fields.Many2one(
        'sale.order', 'Sale Order',
        readonly=True)
    report_url = fields.Char('Report S3 URL')
    quotation_number = fields.Char('#Quotation Number')

    @api.multi
    def button_confirm(self):
        check_report_type = any([line.crm_lead_line_id.media_config for line in self.order_line if line.crm_lead_line_id.media_config])
        check_report_type_quote = any(
            [line.crm_lead_line_id.quote_type for line in self.order_line if line.crm_lead_line_id.quote_type])
        if check_report_type:
            check_outputs_dates = [line_id.crm_lead_line_id.outputs_dates for line_id in self.order_line]
            if any(check_outputs_dates):
                pdf = self.env.ref('flow_purchase_sale.action_report_purchase_order_custom').render_qweb_pdf(self.id)[0]
            else:
                pdf = self.env.ref('purchase.action_report_purchase_order').render_qweb_pdf(self.id)[0]
        elif check_report_type_quote:
            pdf = self.env.ref('flow_purchase_sale.action_report_purchaseorder_quote_type').render_qweb_pdf(self.id)[0]
        else:
            pdf = self.env.ref('purchase.action_report_purchase_order').render_qweb_pdf(self.id)[0]
        pdf = base64.b64encode(pdf)
        pdf_name = re.sub(r'\W+', '', self.name) + '.pdf'
        attachment = self.env['ir.attachment'].create({
            'name': pdf_name,
            'datas': pdf,
            'datas_fname': self.name,
            'res_model': 'purchase.order',
            'res_id': self.id,
            'type': 'binary',
        })
        self.report_url = attachment.url
        return super(PurchaseOrder, self).button_confirm()

    @api.model
    def create(self, vals):
        if vals.get('origin'):
            so_id = self.env['sale.order'].search([('name', '=', vals['origin'])])
            vals['so_id'] = so_id and so_id.id or False
        res = super(PurchaseOrder, self).create(vals)
        res.button_confirm()
        return res

    @api.multi
    def write(self, vals):
        if vals.get('origin'):
            so_id = self.env['sale.order'].search([('name', '=', vals['origin'])])
            vals['so_id'] = so_id and so_id.id or False
        return super(PurchaseOrder, self).write(vals)


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    crm_lead_line_id = fields.Many2one('crm.lead.lines', string='Lead Line')
    order_line_id = fields.Many2one(
        'sale.order.line',
        required=False,
        string='Order Line Reference')
    quotation_number = fields.Char('#Quotation Number')