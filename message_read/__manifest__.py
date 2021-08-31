# Copyright 2019-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Message Read',
    'version': '12.0.1.0.0',
    'summary': 'Message Read',
    'category': 'Administration',
    'author': 'Quadi',
    'license': 'AGPL-3',
    'maintainer': 'Quadi',
    'company': 'Quadi SAS',
    'website': 'https://quadi.co/',
    'depends': [
        'mail',
    ],
    'data': [
    ],
    'qweb': [
        "static/src/xml/discuss.xml",
    ],
    'installable': True,
    'application': True,
}
