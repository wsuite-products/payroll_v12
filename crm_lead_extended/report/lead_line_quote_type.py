# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models, _
from odoo.exceptions import UserError


class ReportLeadLineQuoteType(models.AbstractModel):
    _name = 'report.crm_lead_extended.report_leadline_quote_type'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        lead_line_ids = self.env['crm.lead.lines'].browse(docids)
        check_report_type = any(
            [line.quote_type for line in lead_line_ids if line.quote_type])
        if not check_report_type:
            raise UserError(_("Report Type Miss-Match data.\n"
                              "This Sale Order data is related to Production Type and "
                              "you are trying to print report of Media Type"))
        lead_id = lead_line_ids[0].crm_lead_id
        as_percentage = lead_id.brand_id.advertising_services_percentage
        data.update({
            'No': lead_id.name,
            'Cliente': lead_id.partner_id.name,
            'Producto': lead_id.brand_id.name,
            'Referencia': lead_id.name,
            'Proyecto_ID': lead_id.id,
            'Moneda': lead_id.currency_id.name})
        list_data = []
        all_line_total = 0.0
        for line_id in lead_line_ids:
            total = line_id.price_subtotal + line_id.price_tax
            all_line_total += total
            data_records = {
                'Cotizado': line_id.name,
                'Proveedor_Cant': line_id.product_uom_qty or 0.00,
                'Vr_Unitario': line_id.price_unit or 0.00,
                'Vr_Total': line_id.price_subtotal or 0.00,
                'Iva': line_id.price_tax or 0.00,
                'SP': 0.0,
                'Vr_SP': 0.0,
                'IVA_Vr_SP': 0.0,
                'Total': total or 0.00,
                'is_ads': False,
            }
            list_data.append(data_records)
            if line_id.quote_type == 'EP' and as_percentage > 0:
                ads_data_records = data_records.copy()
                per_vr_total = (as_percentage * line_id.price_subtotal) / 100
                all_line_total += per_vr_total
                ads_data_records.update({
                    'is_ads': True,
                    'Iva': 0.00,
                    'Vr_Total': per_vr_total or 0.00,
                    'Total': per_vr_total or 0.00,
                })
                list_data.append(ads_data_records)
                
        data.update({'all_line_total': '{0:.2f}'.format(all_line_total)})
        return {
            'doc_ids': docids,
            'list_data': list_data,
            'doc_model': 'crm.lead',
            'docs': lead_id,
            'data': data
        }
