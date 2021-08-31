# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Kunjal Patel <kunjalpatel@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Vendor Portal',
    'version': '12.0.1.0.0',
    'summary': 'Vendor Portal',
    'category': 'Purchase',
    'author': 'Quadi',
    'maintainer': 'Quadi',
    'company': 'Quadi SAS',
    'website': 'https://quadi.co/',
    'depends': ['base', 'purchase', 'website', 'crm_lead_extended'],
    'data': [
        'security/vendor_portal_product_security.xml',
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/vendor_rfq_report_templates.xml',
        'views/report_action_view.xml',
        'views/res_partner_view.xml',
        'views/res_users_view.xml',
        'views/vendor_rfq_view.xml',
        'data/ir.sequence.xml',
        'views/portal_templates.xml'

    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'license': 'AGPL-3',
}
