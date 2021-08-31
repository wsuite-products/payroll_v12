# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class HrCenterFormation(models.Model):
    _name = 'hr.center.formation'
    _description = 'Center Formation'

    name = fields.Char('Name', required=True)
    description = fields.Text('Description')
