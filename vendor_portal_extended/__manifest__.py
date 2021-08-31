# Copyright 2020-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Vendor Portal Extended',
    'version': '12.0.1.0.0',
    'summary': 'Vendor Portal Extended',
    'category': 'Purchase',
    'author': 'Quadi',
    'license': 'AGPL-3',
    'maintainer': 'Quadi',
    'company': 'Quadi SAS',
    'website': 'https://quadi.co',
    'depends': [
        'crm_lead_extended',
        'vendor_portal_product',
    ],
    'data': [
        "security/ir.model.access.csv",
        "views/crm_product_template_view.xml",
        "views/inherited_vendor_rfq_view.xml",
        "wizard/create_rfq_crm_lead_view.xml",
        "views/inherited_crm_lead.xml",
        "views/inherited_portal_templates.xml",
    ],
    'installable': True,
}
