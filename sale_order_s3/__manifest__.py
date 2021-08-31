# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Order Comment and S3',
    'version': '12.0.1.0.0',
    'category': 'Sales',
    'author': 'Quadi',
    'description': """
        Added new module for store attachment in s3
    """,
    'maintainer': 'Quadi',
    'company': 'Quadi SAS',
    'website': 'https://quadi.co/',
    'depends': ['sale_order_extended', 'ir_attachment_s3'],
    'data': [
    ],
    'installable': True,
    'auto_install': True,
    'license': 'AGPL-3',
}
