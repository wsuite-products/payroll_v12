# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models, _
import json
from odoo.exceptions import UserError

class ReportSaleOrderCustom(models.AbstractModel):
    _name = 'report.flow_purchase_sale.report_saleorder_custom'

    @api.model
    def _get_report_values(self, docids, data=None):
        so_id = self.env['sale.order'].browse(docids)
        check_report_type = any(
            [line.crm_lead_line_id.media_config for line in so_id.order_line if line.crm_lead_line_id.media_config])
        if not check_report_type:
            raise UserError(_("Report Type Miss-Match data.\n"
                              "This Sale Order data is related to Media Type and "
                              "you are trying to print report of Production Type"))
        MO_object = self.env['mrp.production']
        as_percentage = so_id.opportunity_id.brand_id.advertising_services_percentage
        data.update({
            'No': so_id.name,
            'Cliente': so_id.opportunity_id.partner_id.name,
            'Producto': so_id.opportunity_id.brand_id.name,
            'Nombre': so_id.opportunity_id.name,
            'Moneda': so_id.currency_id.name})
        list_data = []
        report_type_list = []
        for line_id in so_id.order_line:
            media_config = json.loads(line_id.crm_lead_line_id.media_config)
            mo_id = MO_object.search([('sale_order_line_id', '=', line_id.id)], limit=1)
            report_t = media_config.get('media')
            if report_t not in report_type_list:
                report_type_list.append(report_t)
            data_records = {
                'Cadena_Sistema': media_config.get('canal', False).get('name', False),
                'Emisora_Ciudad': media_config.get('franja', False).get('name', False),
                'Tipo_de_Cuna': line_id.product_id.name,
                'Programa_Periodo': media_config.get('programa', False).get('name', False),
                'Duración': media_config.get('reference', False),
                'Orden': mo_id and mo_id.purchase_order_id.name or '',
                'Total_Cunas': line_id.product_uom_qty,
                'Tarifa_Publicada': media_config.get('valor_thirty', 0.0),
                'Equiv': 0,
                'Valor_Bruto': (float(line_id.product_uom_qty) * float(media_config.get('valor_thirtys', 0.0)) * 0),
                'Desc_Cliente': media_config.get('descuento', 0.0),
                'Desc_Agen': 0,
                'Desc_Finan': 0,
                'Rcgos': 0,
                'Valor_Neto': media_config.get('cpr_neg', 0.0),
                'IVA': line_id.price_tax or 0.0,
                'Oyentes_ECAR': 0.0,
                'CPM': 0.0,
                'rating': media_config.get('rating', 0.0),
                'trp': media_config.get('trp', 0.0),
                'audience': media_config.get('audience', ''),
                'is_ads': True if line_id.check_ads_service else False,
                'report_type': report_t,
            }
            if line_id.check_ads_service and as_percentage > 0:
                cpr_neg = 0.0
                currency_symbol = ''
                if media_config.get('cpr_neg'):
                    currency_symbol = media_config.get('cpr_neg').split(" ")[0]
                    cpr_neg = media_config.get('cpr_neg').split("$ ")[1]
                    if cpr_neg.count('.') >= 2:
                        str_split = ".".join(cpr_neg.split(".", 2)[:2])
                        cpr_neg = float(str_split)
                    else:
                        cpr_neg = float(cpr_neg)
                vn = '{0:.2f}'.format((cpr_neg * as_percentage) / 100)
                data_records.update({
                    'IVA': 0.00,
                    'is_ads': True,
                    'Valor_Neto': currency_symbol and currency_symbol + ' ' + vn or vn or 0.00,
                })
            list_data.append(data_records)
        report_type = ", ".join(report_type_list)
        data.update({'report_type': report_type})
        return {
            'doc_ids': docids,
            'report_type': report_type,
            'list_data': list_data,
            'doc_model': 'sale.order',
            'docs': so_id,
            'data': data,
            'report_type_list': report_type_list,
        }
