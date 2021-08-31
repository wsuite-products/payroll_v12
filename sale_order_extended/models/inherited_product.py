# Copyright 2020-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class Product(models.Model):
    _inherit = "product.product"

    product_attributes_ids = fields.One2many(
        'product.attributes', 'product_id')
