# Copyright 2020-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ProductAttributes(models.Model):
    _name = "product.attributes"

    name = fields.Char()
    date = fields.Date()
    tax_ids = fields.Many2many(
        'account.tax', 'product_attributes_tax_default_rel',
        'product_attributes_id', 'tax_id', string="Taxes",
        domain=[('type_tax_use', '=', 'sale')])
    type = fields.Selection([
        ('man', 'MAN'),
        ('fee', 'FEE'),
        ('iw', 'IW')], default='man')
    product_id = fields.Many2one('product.product')
