# Copyright 2020-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Slack Connect',
    'version': '12.0.1.0.0',
    'summary': 'Slack Connect',
    'category': 'Extra Tools',
    'author': 'Quadi',
    'license': 'AGPL-3',
    'maintainer': 'Quadi',
    'company': 'Quadi SAS',
    'website': 'https://quadi.co/',
    'depends': [
        'mail'
    ],
    'data': [
        'views/res_config_settings_view.xml',
    ],
    'installable': True,
    'application': True,
}
