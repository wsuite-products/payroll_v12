# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    brand_id = fields.Many2one('multi.brand', 'Brand')
    color = fields.Char(string='Color')
