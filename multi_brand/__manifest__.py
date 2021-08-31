# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Multi Brand',
    'version': '12.0.1.0.0',
    'category': 'Sales',
    'author': 'Quadi',
    'description': """
        Added new module for multiple brand
    """,
    'maintainer': 'Quadi',
    'company': 'Quadi SAS',
    'website': 'https://quadi.co/',
    'depends': ['res_partner_extended', 'crm_lead_extended', 'hr_recruitment'],
    'data': [
        'security/multi_brand_group.xml',
        'security/ir.model.access.csv',
        'wizard/assign_brand_wizard_view.xml',
        'wizard/other_db_assign_brand_wizard_view.xml',
        'views/multi_brand_view.xml',
        'views/share_brand_view.xml',
        'views/product_view.xml',
        'views/crm_lead_view.xml',
        'views/crm_lead_type_view.xml',
        'views/res_partner_view.xml',
        'views/content_config_view.xml',
        'views/people_config_view.xml',
        'views/assets_config_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'license': 'AGPL-3',
}
