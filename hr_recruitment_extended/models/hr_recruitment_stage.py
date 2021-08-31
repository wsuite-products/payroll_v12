# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class HRRecruitmentStage(models.Model):
    _inherit = "hr.recruitment.stage"

    add_evaluation = fields.Boolean('Add Evaluation?')
