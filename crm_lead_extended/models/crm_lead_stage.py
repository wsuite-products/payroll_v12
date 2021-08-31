# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class CRMLeadStage(models.Model):
    _name = 'crm.lead.stage'
    _description = 'CRM Lead Stage'
    _order = 'date desc'

    crm_lead_id = fields.Many2one('crm.lead', 'Lead')
    stage_id = fields.Many2one('crm.stage', 'Stage')
    pre_stage_id = fields.Many2one('crm.stage', 'Previous Stage')
    date = fields.Datetime('Date')
