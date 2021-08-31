# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.one
    @api.depends('product_variant_ids.product_tmpl_id')
    def _compute_wsuite_product_variant_count(self):
        self.wsuite_product_count = len(self.with_prefetch().product_variant_ids.filtered(lambda self: not self.wsuite))

    wsuite = fields.Boolean("Wsuite")
    flow_json = fields.Text('Flow Json')
    flow_config_json = fields.Text('Flow Config Json')
    wsuite_product_count = fields.Integer(
        '# Wsuite Product Count', compute='_compute_wsuite_product_variant_count')
    client_id = fields.Many2one('res.partner', 'Client')
    # brand_id = fields.Many2one('multi.brand', 'Brand')
    is_default = fields.Boolean('Is Default?')
    pwi_id = fields.Integer('W-Project WorkFlow ID')
    task_id = fields.Integer('W-Project Task Id')
    # profit_type = fields.Selection([
    #     ('PR', 'Profit'),
    #     ('DC', 'Direct Cost'),
    #     ('IW', 'Internal Work'),
    #     ('PI', 'Product Items'),
    # ])
    # profit_percentage = fields.Float('Profit Percentage')
    # direct_cost = fields.Float('Direct Cost')
    # indirect_cost = fields.Float('Indirect Cost')
    # income = fields.Float('Income')
    custom_asset = fields.Boolean('Custom Asset')
    w_message = fields.Boolean('W-Message?')

    @api.multi
    def create_variant_ids(self):
        res = super(ProductTemplate, self).create_variant_ids()
        for product_id in self.product_variant_ids:
            product_id.write({
                'wsuite': self.wsuite,
                'product_name': self.name,
                'product_description': self.description,
                'custom_asset': self.custom_asset,
                'w_message': self.w_message,
            })
        return res

class ProductProduct(models.Model):
    _inherit = "product.product"

    wsuite = fields.Boolean("Wsuite")
    flow_json = fields.Text('Flow Json')
    flow_config_json = fields.Text('Flow Config Json')
    # wsuite_product_count = fields.Integer(
    #     '# Wsuite Product Count', compute='_compute_wsuite_product_variant_count')
    client_id = fields.Many2one('res.partner', 'Client')
    # brand_id = fields.Many2one('multi.brand', 'Brand')
    is_default = fields.Boolean('Is Default?')
    pwi_id = fields.Integer('W-Project WorkFlow ID')
    task_id = fields.Integer('W-Project Task Id')
    profit_type = fields.Selection([
        ('PR', 'Profit'),
        ('DC', 'Direct Cost'),
        ('IW', 'Internal Work'),
        ('PI', 'Product Items'),
    ])
    profit_percentage = fields.Float('Profit Percentage')
    direct_cost = fields.Float('Direct Cost')
    indirect_cost = fields.Float('Indirect Cost')
    income = fields.Float('Income')
    product_name = fields.Char('Product Name')
    estimated_live_date = fields.Date('Date')
    quotation_deadline = fields.Datetime('Quotation Deadline')
    module_type = fields.Char('Module Type')
    product_description = fields.Text('Product Description')
    custom_asset = fields.Boolean('Custom Asset')
    w_message = fields.Boolean('W-Message?')
