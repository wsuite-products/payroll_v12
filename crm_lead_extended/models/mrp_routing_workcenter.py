# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    resource_id = fields.Many2one('hr.job', 'Resource')
    task_form_json = fields.Text('Task Form Json')
    is_operational = fields.Boolean('Is Operational?')
