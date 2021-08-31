# Copyright 2019-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Flow Purchase Sale',
    'version': '12.0.1.0.0',
    'summary': 'Flow Purchase Sale',
    'category': 'Sales',
    'author': 'Quadi',
    'license': 'AGPL-3',
    'maintainer': 'Quadi',
    'company': 'Quadi SAS',
    'website': 'https://quadi.co',
    'depends': [
        'purchase',
        'sale_management',
        'crm_lead_extended'
    ],
    'data': [
        'views/inherited_sale_order_view.xml',
        'views/report_action_view.xml',
        'views/sale_report_templates.xml',
        'views/sale_report_templates_quote_type.xml',
        'views/purchase_report_templates.xml',
        'views/purchase_report_templates_quote_type.xml',
        'views/inherited_purchase_order_view.xml',
        'wizard/create_purchase_order_view.xml',
    ],
    'installable': True,
}
