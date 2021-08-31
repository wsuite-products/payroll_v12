# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models, _
from odoo.exceptions import UserError


class ReportVendorRFQ(models.AbstractModel):
    _name = 'report.vendor_portal_product.report_vendor_rfq'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        rfq_id = self.env['vendor.rfq'].browse(docids)
        if rfq_id.crm_lead_line_id.quote_type not in ['DC', 'PR']:
            raise UserError(_("This Vendor RFQ data is not related to Direct Cost or Profit"))
        lead_id = rfq_id.crm_lead_line_id.crm_lead_id
        data.update({
            'No': rfq_id.purchase_id.name or rfq_id.name,
            'Cliente': lead_id.partner_id.name,
            'Producto': lead_id.brand_id.name,
            'Referencia': lead_id.name,
            'Actividad': '',
            'Proyecto_ID': lead_id.id,
            'Moneda': lead_id.name,
            'Cotizacion': '',
            'Version': '',
            'Template_name': rfq_id.template_id.name,
            'length': len(rfq_id.rfq_line_ids) + 1,
            'remaining_length': 5 - len(rfq_id.vendor_ids),
        })
        list_data = []
        supplier_list_data = []
        supplier_details_data = {}
        supplier_total_data = {}
        for line in rfq_id.rfq_line_ids:
            values = {
                'name': line.vendor_id.name,
                'Director_Fotografo': '',
                'Dias_Rodaje_Fotos': '',
                'Comercial_Fotos': '',
                'Referencia': '',
                'Duracion': '',
                'Formato': '',
            }
            supplier_list_data.append(values)

            for vtl in line.vrfq_template_line_ids:
                if vtl.product_id.categ_id.id not in supplier_total_data:
                    supplier_total_data[vtl.product_id.categ_id.id] = {'category_name': vtl.product_id.categ_id.name}
                    if line.vendor_id.name not in supplier_total_data[vtl.product_id.categ_id.id]:
                        supplier_total_data[vtl.product_id.categ_id.id][line.vendor_id.name] = vtl.price_subtotal
                else:
                    if line.vendor_id.name not in supplier_total_data[vtl.product_id.categ_id.id]:
                        supplier_total_data[vtl.product_id.categ_id.id][line.vendor_id.name] = vtl.price_subtotal
                    else:
                        supplier_total_data[vtl.product_id.categ_id.id][line.vendor_id.name] += vtl.price_subtotal

                if vtl.product_id.categ_id.id not in supplier_details_data:
                    supplier_details_data[vtl.product_id.categ_id.id] = {
                        'category_name': vtl.product_id.categ_id.name,
                        'total': vtl.price_subtotal,
                    }
                    supplier_details_data[vtl.product_id.categ_id.id][vtl.product_id.id] = [
                        {
                            'product_name': vtl.product_id.name,
                            'category_name': vtl.product_id.categ_id.name,
                            'supp_line_details': [{'qty': '{0:.2f}'.format(vtl.qty), 'price_subtotal': '{0:.2f}'.format(vtl.price_subtotal) or 0.00, 'Dias': 0, 'note': vtl.note}]
                        }]
                elif vtl.product_id.id not in supplier_details_data[vtl.product_id.categ_id.id]:
                    supplier_details_data[vtl.product_id.categ_id.id]['total'] += vtl.price_subtotal
                    supplier_details_data[vtl.product_id.categ_id.id][vtl.product_id.id] = [
                        {
                            'product_name': vtl.product_id.name,
                            'category_name': vtl.product_id.categ_id.name,
                            'supp_line_details': [{'qty': '{0:.2f}'.format(vtl.qty), 'price_subtotal': '{0:.2f}'.format(vtl.price_subtotal) or 0.00, 'Dias': 0, 'note': vtl.note}]
                        }]
                else:
                    a = {'qty': '{0:.2f}'.format(vtl.qty), 'price_subtotal': '{0:.2f}'.format(vtl.price_subtotal) or 0.00, 'Dias': 0, 'note': vtl.note}
                    supplier_details_data[vtl.product_id.categ_id.id]['total'] += vtl.price_subtotal
                    supplier_details_data[vtl.product_id.categ_id.id][vtl.product_id.id][0]['supp_line_details'].append(a)

        supplier_total_list_data = []
        for stld in supplier_total_data:
            supplier_total_list_data.append(supplier_total_data.get(stld))
        
        final_list = []
        for d in supplier_details_data:
            final_list.append(supplier_details_data.get(d))
    
        a_final_list = []
        for a in final_list:
            for k, v in a.items():
                if k not in ['category_name', 'total']:
                    a_final_list.extend(a.get(k))

        import itertools
        from operator import itemgetter
        Final_list_Data = []
        for key, value in itertools.groupby(a_final_list, key=itemgetter('category_name')):
            print(key, value)
            vals = {'category_name': key, 'data_list': []}
            for i in value:
                print(i)
                vals['data_list'].append(i)
            Final_list_Data.append(vals)

        return {
            'doc_ids': docids,
            'list_data': list_data,
            'final_list': Final_list_Data,
            'supplier_list_data': supplier_list_data,
            'doc_model': 'sale.order',
            'supplier_total_list_data': supplier_total_list_data,
            'docs': rfq_id,
            'data': data
        }
