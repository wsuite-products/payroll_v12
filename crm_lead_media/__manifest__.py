# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'CRM Lead Media',
    'summary': '',
    'version': '12.0.1.0.0',
    'category': 'base',
    'website': 'https://quadi.co/',
    'author': 'Quadi',
    'application': False,
    'installable': True,
    'depends': [
        'crm_lead_extended','base_extended'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_category_view.xml',
        'views/channel_fringe_lines_view.xml',
        'views/percentage_category_lines_view.xml',
        'views/crm_lead_view.xml',
        'views/crm_process_type_view.xml',
        'views/crm_audience_view.xml',
    ],
}
