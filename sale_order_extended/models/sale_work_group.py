# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class SaleWorkGroup(models.Model):
    """Sale Work Group."""

    _name = 'sale.work.group'
    _description = 'Sale Work Group'

    name = fields.Char('Name', required=True)
    partner_ids = fields.One2many('res.partner', 'sale_work_group_id')

