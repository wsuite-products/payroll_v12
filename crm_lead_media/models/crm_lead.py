# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    reference_media = fields.Char(
        'Reference Media',
        track_visibility='onchange')
    process_type_id = fields.Many2one(
        'crm.process.type', 'CRM Process Type',
        track_visibility='onchange')
    share_accumulate = fields.Float(
        string="Share Accumulate",
        compute='_compute_share_accumulate',
        store=True,
        track_visibility='onchange')
    percentage_categ_ids = fields.One2many(
        'percentage.category.lines',
        'lead_id',
        'Percentage Category Lines')
    channel_fringe_ids = fields.One2many(
        'channel.fringe.lines',
        'lead_id',
        'Channel Fringe Lines')
    trm_date = fields.Date('TRM Date')
    trm_value = fields.Float('TRM Value')

    @api.depends('percentage_categ_ids')
    def _compute_share_accumulate(self):
        for rec in self:
            rec.share_accumulate = sum([pcl.percentage for pcl in rec.percentage_categ_ids.filtered(lambda x: not x.parent_category)])

    @api.constrains('percentage_categ_ids', 'share_accumulate')
    def _check_total_perc(self):
        for rec in self:
            if rec.share_accumulate > 100.0:
                raise ValidationError(_(
                    "Share Accumulate cannot be greater than 100!"))
            if rec.share_accumulate < 0.0:
                raise ValidationError(_(
                    "Share Accumulate cannot be less than 0.0!"))
