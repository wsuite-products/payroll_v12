# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class CRMProcessType(models.Model):
    _name = 'crm.process.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'CRM Process Type'

    name = fields.Char(
        'Name', required=True,
        track_visibility='onchange')
    description = fields.Text(
        'Description',
        track_visibility='onchange')
