# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Pricelist based on vendor',
    'version': '12.0.1.0.0',
    'category': 'Sales',
    'author': 'Quadi',
    'maintainer': 'Quadi',
    'company': 'Quadi SAS',
    'website': 'https://quadi.co/',
    'depends': ['sale', 'crm_lead_media'],
    'data': [
        'views/product_pricelist_item_view.xml',
        'views/product_template_view.xml',
        'views/sale_order_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'license': 'AGPL-3',
}
