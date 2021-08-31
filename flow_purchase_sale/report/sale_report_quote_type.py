# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models, _
import json
from odoo.exceptions import UserError


class ReportSaleOrderQuoteType(models.AbstractModel):
    _name = 'report.flow_purchase_sale.report_saleorder_quote_type'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        so_id = self.env['sale.order'].browse(docids)
        check_report_type = any(
            [line.crm_lead_line_id.quote_type for line in so_id.order_line if line.crm_lead_line_id.quote_type])
        if not check_report_type:
            raise UserError(_("Report Type Miss-Match data.\n"
                              "This Sale Order data is related to Production Type and "
                              "you are trying to print report of Media Type"))
        # as_percentage = so_id.opportunity_id.brand_id.advertising_services_percentage
        data.update({
            'No': so_id.name,
            'Cliente': so_id.opportunity_id.partner_id.name,
            'Producto': so_id.opportunity_id.brand_id.name,
            'Referencia': so_id.opportunity_id.name,
            'Proyecto_ID': so_id.opportunity_id.id,
            'Moneda': so_id.currency_id.name})
        list_data = []
        all_line_total = 0.0
        for line_id in so_id.order_line:
            total = line_id.price_subtotal + line_id.price_tax
            if not line_id.check_ads_service:
                all_line_total += total
            data_records = {
                'Cotizado': line_id.crm_lead_line_id.name,
                'Proveedor_Cant': line_id.product_uom_qty or 0.00,
                'Vr_Unitario': line_id.price_unit or 0.00,
                'Vr_Total': line_id.price_subtotal or 0.00,
                'Iva': line_id.price_tax or 0.00,
                'SP': 0.0,
                'Vr_SP': 0.0,
                'IVA_Vr_SP': 0.0,
                'Total': total or 0.00,
                'is_ads': True if line_id.check_ads_service else False,
            }
            if line_id.check_ads_service:
                # per_vr_total = (as_percentage * line_id.price_subtotal) / 100
                all_line_total += line_id.price
                data_records.update({
                    'is_ads': True,
                    'Iva': 0.00,
                    'Vr_Total': line_id.price or 0.00,
                    'Total': line_id.price or 0.00,
                })
            list_data.append(data_records)
        data.update({'all_line_total': '{0:.2f}'.format(all_line_total)})
        return {
            'doc_ids': docids,
            'list_data': list_data,
            'doc_model': 'sale.order',
            'docs': so_id,
            'data': data
        }
