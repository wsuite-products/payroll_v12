# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Sale Order Extended',
    'version': '12.0.1.0.0',
    'category': 'Sales',
    'author': 'Quadi',
    'maintainer': 'Quadi',
    'company': 'Quadi SAS',
    'website': 'https://quadi.co/',
    'depends': ['crm_lead_extended', 'sale', 'multi_brand', 'mrp'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_view.xml',
        'views/inherited_res_partner_view.xml',
        'views/inherited_multi_brand_view.xml',
        'views/mrp_view.xml',
        'views/sale_work_group_view.xml',
        'views/inherited_product_view.xml',
        'views/product_attributes_view.xml',
        'views/inherited_calendar_event_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'license': 'AGPL-3',
}
