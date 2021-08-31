# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class CRMLeadStage(models.Model):
    _inherit = 'crm.lead.stage'

    step_id = fields.Many2one(
        'step.step',
        related='stage_id.step_id',
        string="Step", readonly=False)
    response_id = fields.Many2one(
        'step.user_input',
        string="Response",
        ondelete="set null")
    state = fields.Selection([
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], string='Status')
    user_ids = fields.Many2many('res.users', string='Users')
    done_user_ids = fields.Many2many('res.users', 'crm_lead_stage_done_user', 'crm_lead_stage_id', 'user_id',  string='Users')

    @api.multi
    def write(self, vals):
        res = super(CRMLeadStage, self).write(vals)
        if not self.env.context.get('set_user') and self.stage_id.approved_by:
            rugb_obj = self.env['res.user.groups.brand']
            group_brand_user_list = []
            for user_id in self.crm_lead_id.users_ids:
                rugb_id = rugb_obj.search([
                    ('user_id', '=', user_id.id),
                    ('group_id', '=', self.stage_id.approved_by.id),
                    ('multi_id', '=', self.crm_lead_id.brand_id.id)])
                if rugb_id:
                    group_brand_user_list.append(user_id.id)
            self.with_context({'set_user': True}).write({'user_ids': [(6, 0, group_brand_user_list)]})
            # self.with_context({'set_user': True}).write({'user_ids': [(6, 0, self.stage_id.approved_by.users.ids)]})
        if not self.env.context.get('set_user') and self.state == 'done' and self.response_id:
            user_list_ids = self.crm_lead_id.users_ids.ids
            user_list_ids.append(self.crm_lead_id.user_id.id)
            self.with_context({'set_user': True}).write({'done_user_ids': [(6, 0, user_list_ids)]})
        return res

    @api.multi
    def action_print_step(self):
        """ If response is available then print this response otherwise
         print step form (print template of the step) """
        self.ensure_one()
        if not self.response_id:
            return self.step_id.with_context({
                'lead_id': self.crm_lead_id.id
            }).action_print_step()
        else:
            response = self.response_id
            return self.step_id.with_context({
                'step_token': response.token,
                'lead_id': self.crm_lead_id.id}).action_print_step()

    @api.multi
    def action_step_results(self):
        return self.response_id.with_context({
            'lead_id': self.crm_lead_id.id}).action_step_results()

    @api.multi
    def action_send_step(self):
        return self.step_id.with_context({
            'lead_id': self.crm_lead_id.id}).action_send_step()
