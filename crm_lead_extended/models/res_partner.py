# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer_admin = fields.Boolean('Customer Admin')
    product_suite_ids = fields.Many2many(
        'product.product', string='Product Wsuite')
    crm_lead_type_ids = fields.One2many('crm.lead.type', 'partner_id')
    is_special_vendor = fields.Boolean('Is Special Vendor?')

    @api.onchange('customer_admin')
    def onchange_customer_admin(self):
        self.customer = False
        if self.customer_admin:
            self.customer = True
