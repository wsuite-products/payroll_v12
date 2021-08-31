# Copyright 2020-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class CrmProductTemplate(models.Model):
    """Crm Product Template."""

    _name = 'crm.product.template'

    name = fields.Char()
    template_line_ids = fields.One2many(
        'crm.product.template.lines', 'template_id')


class CrmProductTemplateLine(models.Model):
    """Crm Product Template Line."""

    _name = 'crm.product.template.lines'

    product_categ_id = fields.Many2one('product.category', 'Product Category')
    product_id = fields.Many2one(
        'product.product', 'Product',
        domain="[('categ_id', 'child_of', product_categ_id)]")
    template_id = fields.Many2one('crm.product.template')
