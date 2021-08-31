# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
import calendar
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from collections import OrderedDict

Months = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
}

Number_TO_Months = {
    '1': 'Enero',
    '2': 'Febrero',
    '3': 'Marzo',
    '4': 'Abril',
    '5': 'Mayo',
    '6': 'Junio',
    '7': 'Julio',
    '8': 'Agosto',
    '9': 'Septiembre',
    '10': 'Octubre',
    '11': 'Noviembre',
    '12': 'Diciembre',
}

Days = {
    'Sat': 'Sáb',
    'Sun': 'Dom',
    'Mon': 'Lun',
    'Tue': 'Mar',
    'Wed': 'Mié',
    'Thu': 'Jue',
    'Fri': 'Vie',
}

class ReportPurchaseOrderCustom(models.AbstractModel):
    _name = 'report.flow_purchase_sale.report_purchaseorder_custom'

    def get_month_day_range(self, date):
        first_day = date.replace(day=1)
        last_day = date.replace(day=calendar.monthrange(date.year, date.month)[1])
        return first_day, last_day

    def _get_day(self, start_date, last_date, month_day):
        res = []
        start_date = fields.Date.from_string(start_date)
        for x in range(0, month_day):
            color = '#ababab' if self._date_is_day_off(start_date) else ''
            english_day = start_date.strftime('%a')
            spanish_day = Days.get(english_day)
            res.append({'day_str': spanish_day, 'day': start_date.day, 'color': color})
            start_date = start_date + relativedelta(days=1)
        return res

    def _get_day_values(self, value_date, value, start, end):
        # value_date = datetime.strptime(value_date, '%Y/%m/%d')
        # if start <= value_date.date() <= end:
        #     return {value_date.day: value}
        # else:
        #     return {value_date.day: 0}
        return {value_date.day: value}

    def _date_is_day_off(self, date):
        return date.weekday() in (calendar.SATURDAY, calendar.SUNDAY,)

    @api.model
    def _get_report_values(self, docids, data=None):
        po_id = self.env['purchase.order'].browse(docids)
        check_report_type = any(
            [line.crm_lead_line_id.media_config for line in po_id.order_line if line.crm_lead_line_id.media_config])
        if not check_report_type:
            raise UserError(_("Report Type Miss-Match data.\n"
                              "This Sale Order data is related to Media Type and "
                              "you are trying to print report of Production Type"))

        vendor_list = []
        vendor = po_id.partner_id
        while vendor:
            vendor_list.append(vendor.name)
            vendor = vendor.parent_id
        vendors = ', '.join(vendor_list)
        report_type = ""
        list_data = []
        data.update({
            'Senores': vendors,
            'Atencion': '',
            'Cliente': po_id.so_id.opportunity_id.partner_id.name,
            'Nit_Cliente': po_id.so_id.partner_id.vat,
            'Producto': po_id.so_id.opportunity_id.brand_id.name,
            'No': po_id.name,
            'Presupuesto_No': po_id.so_id.name,
            'Moneda': po_id.currency_id.name,
            'Total_Total_Cunas': 0.0,
            'Total_Valor_Neto': 0.0,
            'Total_IVA': 0.0,
            'Total_Total': 0.0,
        })
        data_dict = {}
        first_day = False
        last_day = False
        month_list = []
        for line_id in po_id.order_line:
            outputs_dates_config = json.loads(line_id.crm_lead_line_id.outputs_dates)
            firstday = datetime.strptime(str(outputs_dates_config.get('stateDate')), '%Y/%m/%d').date()
            lastday = datetime.strptime(str(outputs_dates_config.get('endDate')), '%Y/%m/%d').date()
            if not first_day:
                first_day = firstday
            if not last_day:
                last_day = lastday
            if first_day > firstday:
                first_day = firstday
            if last_day < lastday:
                last_day = lastday
        month_list.extend(OrderedDict(((first_day + timedelta(_)).strftime(r"%b-%Y"), None) for _ in
                                      range((last_day - first_day).days)).keys())

        month_data_dict = {}
        months_header_data = {}
        months_header_day = {}
        for m in month_list:
            month = m.split('-')[0]
            year = int(m.split('-')[1])
            month_data_dict[Months.get(month)] = []
            date = datetime(year, Months.get(month), 1)
            first_day, last_day = self.get_month_day_range(date.date())
            for line_id in po_id.order_line:
                outputs_dates_config = json.loads(line_id.crm_lead_line_id.outputs_dates)
                media_config = json.loads(line_id.crm_lead_line_id.media_config)
                date_diff = relativedelta(last_day, first_day)
                month_day = int(date_diff.days + 1)
                data.update({'month_day': month_day})
                taxes = sum([taxid.amount for taxid in line_id.crm_lead_line_id.tax_id])
                cpr_neg = 0
                if media_config.get('cpr_neg_s'):
                    # cpr_neg = media_config.get('cpr_neg', 0.0)[2:]
                    cpr_neg = float(media_config.get('cpr_neg_s').split("$ ")[1])
                data['Total_Valor_Neto'] += float(cpr_neg)

                line_raw = {
                    'month_name': date.strftime('%B') or '',
                    'raw_list': [],
                    'Total_Cunas': 0.0,
                    'Valor_Neto': 0.0,
                    'IVA': taxes or 0.0,
                    'IVA_amount': 0.0,
                    'Total': 0.0,
                    'Referencia': media_config.get('reference', False),
                    'Tipo_de_Cuna': line_id.product_id.name,
                    'Sistema': media_config.get('canal', False).get('name', False),
                    'Emisora': media_config.get('franja', False).get('name', False),
                    'Dial_Banda': '',
                    'Programa': media_config.get('programa', False).get('name', False),
                }

                data['Total_IVA'] += line_id.price_tax or 0.0
                data_dict[line_id.id] = {'lines_values': []}

                for x in range(1, last_day.day + 1):
                    data_dict[line_id.id]['lines_values'].append({x: 0})
                if not report_type:
                    report_type = media_config.get('media')
                    data.update({'report_type': media_config.get('media')})
                values_list = []

                for week in outputs_dates_config.get('weeks', False):
                    for day in week.get('days'):
                        value_date = datetime.strptime(day.get('day'), '%Y/%m/%d')
                        if first_day <= value_date.date() <= last_day:
                            values_list.append(self._get_day_values(value_date, day.get('value'), first_day, last_day))

                final_value_dict = dict(list(d.items())[0] for d in data_dict[line_id.id]['lines_values'])
                value_dict = dict(list(d.items())[0] for d in values_list)
                final_value_dict.update(value_dict)
                day_dict = self._get_day(first_day, last_day, month_day)
                months_header_data.update({Months.get(month): day_dict})
                months_header_day.update({Months.get(month): 31 - month_day})
                final_list = []
                total_Total_Cunas = 0.0
                for a in day_dict:
                    val = final_value_dict.get(a.get('day'))
                    total_Total_Cunas += val
                    a.update({'value': val})
                    final_list.append(a)
                line_raw['raw_list'].extend(final_list)
                line_raw['Total_Cunas'] = total_Total_Cunas
                if report_type == 'Televisión':
                    rating = float(media_config.get('rating'))
                    valor_neto = total_Total_Cunas * cpr_neg * rating
                else:
                    valor_neto = total_Total_Cunas * cpr_neg
                line_raw['Valor_Neto'] = valor_neto
                line_raw['IVA_amount'] = (valor_neto * taxes) / 100
                month_data_dict[Months.get(month)].append(line_raw)
        print("==month_data_dict==", month_data_dict)
        return {
            'final_value_list': month_data_dict,
            'Number_TO_Months': Number_TO_Months,
            'months_header_data': months_header_data,
            'months_header_day': months_header_day,
            'month_list': month_list,
            'doc_ids': docids,
            'report_type': report_type,
            'list_data': list_data,
            'doc_model': 'sale.order',
            'get_day': self._get_day(first_day, last_day, month_day),
            'docs': po_id,
            'data': data
        }
