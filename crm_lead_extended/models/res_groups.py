# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

class ResGroups(models.Model):
    _inherit = 'res.groups'

    product_id = fields.Many2one(
        'product.product', 'Product',
        domain=[('wsuite', '=', True)])
    # product_ids = fields.Many2many(
    #     'product.product', 'res_group_product_rel', 'group_id', 'product_id', string='Product Wsuite',
    #     domain=[('wsuite', '=', True)])
