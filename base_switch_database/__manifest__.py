# Copyright 2019-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Base Switch Database',
    'version': '12.0.1.0.0',
    'summary': 'Base Switch Database',
    'category': 'Administration',
    'author': 'Quadi',
    'license': 'AGPL-3',
    'maintainer': 'Quadi',
    'company': 'Quadi SAS',
    'website': 'https://quadi.co/',
    'depends': [
        'base_synchro',
        'external_login',
        'partner_product',
    ],
    'data': [
        "security/ir.model.access.csv",
        "views/inherited_base_synchro_server_view.xml",
        "views/res_users_servers_view.xml",
        "views/webclient_templates.xml",
    ],
    'qweb': [
        "static/src/xml/base_switch_database.xml",
    ],
    'installable': True,
    'application': True,
}
