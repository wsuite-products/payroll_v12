# Copyright 2019-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Alert Finish Contract',
    'version': '12.0.1.0.0',
    'summary': 'Alert Finish Contract',
    'category': 'Human Resources',
    'author': 'Quadi',
    'license': 'AGPL-3',
    'maintainer': 'Quadi',
    'company': 'Quadi SAS',
    'website': 'https://quadi.co/',
    'depends': [
        'hr_payroll',
    ],
    'data': [
        "security/ir.model.access.csv",
        "views/alert_finish_contract_view.xml",
    ],
    'installable': True,
}
