# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models, _
from odoo.exceptions import UserError


class ReportPurchaseOrderQuoteType(models.AbstractModel):
    _name = 'report.flow_purchase_sale.report_purchaseorder_quote_type'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        po_id = self.env['purchase.order'].browse(docids)
        check_report_type = any(
            [line.crm_lead_line_id.quote_type for line in po_id.order_line if line.crm_lead_line_id.quote_type in ['DC','PR','EP']])
        if not check_report_type:
            raise UserError(_("Report Type Miss-Match data.\n"
                              "This Purchase Order data is related to Production Type and "
                              "you are trying to print report of Media Type"))
        lead_id = po_id.so_id.opportunity_id
        data.update({
            'No': po_id.name,
            'Area': '',
            'Proveedor': po_id.partner_id.name,
            'Nit_Proveedor': po_id.partner_id.vat,
            'Cliente': lead_id.partner_id.name,
            'Producto': lead_id.brand_id.name,
            'Proyecto': lead_id.name,
            'Proyecto_ID': lead_id.id,
            'Contacto': po_id.user_id.name,
            'Moneda': po_id.currency_id.name,
            'Cliente_Principal': lead_id.partner_id.name,
            'company_name': po_id.company_id.name,
        })
        list_data = []
        for line_id in po_id.order_line:
            if not data.get('Presupuesto'):
                data.update({
                    'Presupuesto': line_id.crm_lead_line_id.quotation_number,
                })
            taxes = sum([tax_id.amount for tax_id in line_id.taxes_id])
            lead_name = line_id.crm_lead_line_id and line_id.crm_lead_line_id.name or ''
            categ_name = line_id.crm_lead_line_id.product_id.categ_id.name or line_id.product_id.categ_id.name
            data_records = {
                'category_name': categ_name + ' - ' + lead_name,
                'name': line_id.crm_lead_line_id.product_id.name,
                'Cantidad': '{0:.2f}'.format(line_id.product_qty) or 0.00,
                'Dias': 0,
                'Vr_Unitario': '{0:.2f}'.format(line_id.price_unit) or 0.00,
                'Vr_Total': '{0:.2f}'.format(line_id.price_subtotal) or 0.00,
                'percentage_Iva': '{0:.2f}'.format(taxes) or 0.00,
                'Iva': '{0:.2f}'.format(line_id.price_tax) or 0.00,
            }
            list_data.append(data_records)
        return {
            'doc_ids': docids,
            'list_data': list_data,
            'doc_model': 'sale.order',
            'docs': po_id,
            'data': data
        }
