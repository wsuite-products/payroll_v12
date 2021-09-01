# Copyright 2019-TODAY WSuite Products <wsuite-products@destiny.ws>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Alert Finish Contract',
    'version': '12.0.1.0.0',
    'summary': 'Alert Finish Contract',
    'category': 'Human Resources',
    'author': 'Destiny',
    'license': 'AGPL-3',
    'maintainer': 'Destiny',
    'company': 'Destiny SAS',
    'website': 'https://destiny.ws/',
    'depends': [
        'hr_payroll',
    ],
    'data': [
        "security/ir.model.access.csv",
        "views/alert_finish_contract_view.xml",
    ],
    'installable': True,
}
