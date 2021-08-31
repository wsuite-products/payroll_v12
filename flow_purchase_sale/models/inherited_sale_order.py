# Copyright 2019-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
import base64
import re


class SaleOrder(models.Model):
    """Added PO from SO feature."""

    _inherit = "sale.order"

    @api.multi
    def calculate_po(self):
        """Calculate total PO."""
        for rec in self:
            rec.total_po = self.env['purchase.order'].search_count(
                [('so_id', '=', rec.id)])

    total_po = fields.Integer('Total Purchase Order', compute='calculate_po')
    report_url = fields.Char('Report S3 URL')

    @api.multi
    def action_confirm(self):
        check_report_type = any([line.crm_lead_line_id.media_config for line in self.order_line if line.crm_lead_line_id.media_config])
        if check_report_type:
            pdf = self.env.ref('flow_purchase_sale.action_report_saleorder_custom').render_qweb_pdf(self.id)[0]
        else:
            pdf = self.env.ref('flow_purchase_sale.action_report_saleorder_quote_type').render_qweb_pdf(self.id)[0]
        pdf = base64.b64encode(pdf)
        pdf_name = re.sub(r'\W+', '', self.name) + '.pdf'
        attachment = self.env['ir.attachment'].create({
            'name': pdf_name,
            'datas': pdf,
            'datas_fname': self.name,
            'res_model': 'sale.order',
            'res_id': self.id,
            'type': 'binary',
        })
        self.report_url = attachment.url
        return super(SaleOrder, self).action_confirm()

    @api.multi
    def action_create_purchase_order(self):
        """Create PO."""
        for sale in self:
            return {
                'name': _('Create Purchase Order'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'create.purchase.order',
                'target': 'new',
            }

    @api.multi
    def action_view_po(self):
        """View PO."""
        for sale in self:
            return {
                'name': _('Purchase Order'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'purchase.order',
                'domain': [('so_id', '=', sale.id)],
            }
