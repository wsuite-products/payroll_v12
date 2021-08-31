# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    step_id = fields.Many2one('step.step', string="Step", readonly=False)
    response_id = fields.Many2one(
        'step.user_input', "Response", ondelete="set null", oldname="response")

    @api.multi
    def action_start_step(self):
        self.ensure_one()
        # create a response and link it to this applicant
        if not self.response_id:
            response = self.env['step.user_input'].create({
                'step_id': self.step_id.id,
                'partner_id': self.partner_id.id,
                'type': 'manually'})
            self.response_id = response.id
        else:
            response = self.response_id
        self.crm_lead_stage_ids[0].response_id = \
            response if self.step_id else False
        # grab the token of the response and start steping
        return self.step_id.with_context({
            'step_token': response.token, 'lead_id': self.id
        }).action_start_step()

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        super(CRMLead, self)._onchange_stage_id()
        self.step_id = self.stage_id.step_id.id
        self.response_id = False
