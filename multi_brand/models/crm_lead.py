# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    brand_id = fields.Many2one('multi.brand', 'Brand')
    wpartner_id = fields.Many2one(
        'res.partner', 'W-Partner',
        domain=[('customer', '=', True), ('parent_id', '=', False)]
    )

    @api.onchange('wpartner_id')
    def onchange_wpartner_id(self):
        res = {'domain': {'partner_id': []}}
        self.partner_id = False
        if self.wpartner_id:
            domain = [('wpartner_id', '=', self.wpartner_id.id)]
            res['domain']['partner_id'] = domain
        return res
