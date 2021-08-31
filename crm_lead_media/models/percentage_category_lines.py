# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class PercentageCategoryLines(models.Model):
    _name = 'percentage.category.lines'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Percentage Category Lines'

    name = fields.Char(
        related='classification_id.complete_name', string="Name")
    lead_id = fields.Many2one(
        'crm.lead', 'Lead',
        track_visibility='onchange')
    classification_id = fields.Many2one(
        'product.category', 'Product Category',
        track_visibility='onchange')
    percentage = fields.Float(
        'Percentage', track_visibility='onchange')
    level = fields.Integer(
        'Level', track_visibility='onchange')
    percentage_total = fields.Float(
        'Percentage Total', track_visibility='onchange')
    qty = fields.Integer(
        'Quantity', track_visibility='onchange')
    cpr_prom = fields.Float(
        'CPR Prom', track_visibility='onchange')
    sov_channel = fields.Float(
        'SOV Channel', track_visibility='onchange')
    investment = fields.Float(
        'Investment', track_visibility='onchange')
    per_categ_id = fields.Many2one(
        'percentage.category.lines', 'Percentage Category',
        track_visibility='onchange')
    channel_fringe_ids = fields.One2many(
        'channel.fringe.lines',
        'per_categ_id',
        'Channel Fringe Lines')
    parent_category = fields.Many2one('product.category', 'Parent Category')
    parent_category_share_accumulate = fields.Float(
        string="Parent Category Share Accumulate",
        compute='_parent_category_share_accumulate',
        store=True,
        track_visibility='onchange'
    )
    media_config = fields.Text('Media Config')
    reference_config = fields.Text('Reference Config')
    request_config = fields.Text('Request Config')

    @api.onchange('classification_id')
    def onchange_classification_id(self):
        if self.classification_id:
            self.parent_category = self.classification_id.parent_id.id

    @api.depends('classification_id', 'lead_id', 'percentage', 'parent_category')
    def _parent_category_share_accumulate(self):
        for rec in self:
            if rec.lead_id:
                pcl_ids = self.read_group([
                    ('parent_category', '=', rec.parent_category.id),
                    ('lead_id', '=', rec.lead_id.id)],
                    ['lead_id', 'classification_id', 'percentage', 'parent_category'],
                    groupby=['parent_category'])
                if pcl_ids:
                    rec.parent_category_share_accumulate = pcl_ids[0].get('percentage')
                else:
                    rec.parent_category_share_accumulate = 0.0
            else:
                rec.parent_category_share_accumulate = 0.0

    @api.constrains('classification_id', 'lead_id', 'percentage', 'parent_category')
    def _compute_parent_category_share_accumulate(self):
        for rec in self:
            if rec.parent_category_share_accumulate > 100.0:
                raise ValidationError(_(
                    "Parent Category Share Accumulate cannot be greater than 100%!"))
            if rec.parent_category_share_accumulate < 0.0:
                raise ValidationError(_(
                    "Parent Category Share Accumulate cannot be less than 0.0%!"))