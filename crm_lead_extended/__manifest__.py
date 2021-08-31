# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'CRM Lead Extended',
    'version': '12.0.1.0.0',
    'category': 'Sales',
    'author': 'Quadi',
    'maintainer': 'Quadi',
    'company': 'Quadi SAS',
    'website': 'https://quadi.co/',
    'depends': ['sale_crm', 'mrp'],
    'data': [
        'security/ir.model.access.csv',
        'report/lead_line_report_templates.xml',
        'report/lead_line_templates_quote_type.xml',
        'report/report_action_view.xml',
        'views/crm_lead_type_view.xml',
        'views/crm_lead_product_quotes_view.xml',
        'views/crm_lead_view.xml',
        'views/res_partner_view.xml',
        'views/product_view.xml',
        'views/res_groups_view.xml',
        'views/mrp_routing_workcenter_view.xml',
        'wizard/quotation_selection_process_wizard_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
