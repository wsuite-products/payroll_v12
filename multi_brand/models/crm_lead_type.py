# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class CRMLeadType(models.Model):
    _inherit = 'crm.lead.type'

    brand_id = fields.Many2one('multi.brand', 'Brand')


class CRMStage(models.Model):
    _inherit = 'crm.stage'

    brand_id = fields.Many2one('multi.brand', 'Brand')
