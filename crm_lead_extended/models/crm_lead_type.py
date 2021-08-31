# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class CRMLeadType(models.Model):
    _name = 'crm.lead.type'
    _description = 'crm.lead.type'

    name = fields.Char('Name', required=True)
    description = fields.Text('Description')
    flows_ids = fields.Many2many('crm.stage', string="Flows")
    parent_crm_lead_type = fields.Many2one('crm.lead.type', 'Parent Type')
    icon = fields.Binary("Icon", attachment=True)
    partner_id = fields.Many2one('res.partner', 'Partner')
    image_url = fields.Char('Image URL')
    color = fields.Char(string='Color')
    request_chk = fields.Boolean('Request Check?', default=True)
