# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ChannelFringeLines(models.Model):
    _name = 'channel.fringe.lines'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Channel Fringe Lines'

    name = fields.Char(related='channel_id.complete_name', string="Name")
    lead_id = fields.Many2one('crm.lead', 'Lead', track_visibility='onchange')
    per_categ_id = fields.Many2one(
        'percentage.category.lines', 'Percentage Category',
        track_visibility='onchange')
    channel_id = fields.Many2one(
        'product.category', 'Product Category',
        track_visibility='onchange')
    product_tmp_id = fields.Many2one(
        'product.template', 'Template',
        track_visibility='onchange')
    product_product_id = fields.Many2one(
        'product.product', 'Product',
        track_visibility='onchange')
    percentage = fields.Float('Percentage', track_visibility='onchange')
    value = fields.Integer('Value', track_visibility='onchange')
