# -*- coding: utf-8 -*-

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp


class QuotationSelectionProcess(models.TransientModel):
    _name = 'quotation.selection.process'
    _description = 'Quotation Selection Process'

    quotation_selection_pro_ids = fields.One2many(
        'quotation.selection.process.line',
        'quotation_selection_process_id',
        string='Quotation Lines')
    crm_lead_id = fields.Many2one('crm.lead', string="Lead")

    @api.multi
    def create_quotation(self):
        context = self.env.context.copy()
        crm_lead_line_ids = \
            self.quotation_selection_pro_ids.mapped('crm_lead_line_id')
        order_lines = []
        template_list = []
        quotation_number = ''
        crm_lead_pq = self.env['crm.lead.product.quotes']
        for line_id in crm_lead_line_ids:
            template_list.append(line_id.product_id.product_tmpl_id.id)
            if not quotation_number:
                quotation_number = line_id.quotation_number
            order_lines.append((0, 0, {
                'name': line_id.name,
                'product_id': line_id.product_id.id,
                'res_supplier_id': line_id.res_supplier_id.id,
                'product_uom': line_id.product_id.uom_po_id.id,
                'product_uom_qty': line_id.product_uom_qty,
                'price_unit': line_id.price_unit,
                'discount': line_id.discount,
                'tax_id': [(6, 0, line_id.tax_id.ids)],
                'crm_lead_line_id': line_id.id,
                'order_date': line_id.order_date,
                'product_tmpl_id': line_id.product_id.product_tmpl_id.id,
                'hours': line_id.hours,
                'price': line_id.product_uom_qty * line_id.price_unit,
                'quotation_number': line_id.quotation_number,
            }))
        clpq_id = crm_lead_pq.search([
            ('quotation_number', '=', quotation_number),
            ('crm_lead_id', '=', self.crm_lead_id.id)], limit=1)
        context.update({
            'search_default_partner_id': self.crm_lead_id.partner_id.id,
            'search_default_opportunity_id': self.crm_lead_id.id,
            'default_partner_id': self.crm_lead_id.partner_id.id,
            'default_team_id': self.crm_lead_id.team_id.id,
            'default_campaign_id': self.crm_lead_id.campaign_id.id,
            'default_medium_id': self.crm_lead_id.medium_id.id,
            'default_origin': self.crm_lead_id.name,
            'default_source_id': self.crm_lead_id.source_id.id,
            'default_order_line': order_lines,
            'default_opportunity_id': self.crm_lead_id.id,
            'default_fee_check': clpq_id and clpq_id.is_fee,
            'default_product_template_ids': [(6, 0, template_list)],
            'default_quotation_number': quotation_number,
        })
        return {
            'context': context,
            'view_type': 'form',
            'view_mode': 'form,tree,graph',
            'res_model': 'sale.order',
            'views': [(False, 'form')],
            'domain': [('opportunity_id', '=', self.crm_lead_id.id)],
            'type': 'ir.actions.act_window',
            'target': 'current',
        }


class QuotationSelectionProcessLine(models.TransientModel):
    _name = 'quotation.selection.process.line'
    _description = "Quotation Selection Process Line"

    name = fields.Text(string='Description', required=True)
    product_uom_qty = fields.Float(
        string='Ordered Qty',
        digits=dp.get_precision('Discount'))
    product_uom = fields.Many2one(
        'uom.uom',
        'Product Unit of Measure')
    product_id = fields.Many2one(
        'product.product',
        'Product')
    quotation_selection_process_id = fields.Many2one(
        'quotation.selection.process',
        'Quotation Selection Process')
    price_unit = fields.Float(
        string='Unit Price',
        digits=dp.get_precision('Product Price'))
    tax_id = fields.Many2many(
        'account.tax',
        string='Taxes')
    discount = fields.Float(
        string='Discount (%)',
        digits=dp.get_precision('Discount'),
        default=0.0)
    price_subtotal = fields.Float(string='Subtotal')
    crm_lead_line_id = fields.Many2one('crm.lead.lines', 'CRM Lead Line')
    order_date = fields.Date('Date')
    product_tmpl_id = fields.Many2one(related='product_id.product_tmpl_id', string='Product Template')
    hours = fields.Float()
    price = fields.Float('Unit Price')
    quotation_number = fields.Char('#Quotation Number')
