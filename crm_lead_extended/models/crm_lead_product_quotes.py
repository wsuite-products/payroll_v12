# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class CRMLeadProductQuotes(models.Model):
    _name = 'crm.lead.product.quotes'
    _description = 'CRM Lead Product Quotes'

    product_tmp_id = fields.Many2one('product.template', 'Product Template')
    quotation_number = fields.Char('#Quotation Number')
    crm_lead_id = fields.Many2one('crm.lead', 'Lead')
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.ref('base.COP'))
    is_approval = fields.Boolean('Approval?')
    approved_by = fields.Many2one('res.groups', 'Group')
    is_fee = fields.Boolean('Fee?')
    asset_config = fields.Text('Asset Configuration')
    request_type = fields.Selection([('media', 'Media'),('production', 'Production')])
    main_cate_id = fields.Many2one('product.category', 'Main Category')
    is_billable = fields.Boolean('Billable ?')
    quote_type = fields.Selection([
        ('PR', 'Profit'),
        ('DC', 'Direct Cost'),
        ('IW', 'Internal Work'),
        ('PI', 'Product Items'),
        ('EP', 'External Product'),
    ])