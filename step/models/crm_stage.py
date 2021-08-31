# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api


class CRMStage(models.Model):
    _inherit = "crm.stage"

    step_id = fields.Many2one('step.step')
    feedback = fields.Boolean('Feedback')
    feedback_category = fields.Char('Feedback Category')
    feedback_type = fields.Char('Feedback Type')
    category_css = fields.Text('Category CSS')
    step_flag = fields.Boolean('Step Flag')
    color = fields.Char(string='Color')
    image = fields.Binary('image')
    image_url = fields.Char('Image URL')
    file_name = fields.Char("File Name", track_visibility='onchange')
    is_loghour = fields.Boolean('Log Hours')
    mandatory = fields.Boolean('Mandatory')
    approved_by = fields.Many2one('res.groups', 'Group')
    active = fields.Boolean('Active', default=True)

    @api.model
    def create(self, vals):
        res = super(CRMStage, self).create(vals)
        if vals.get('image', ''):
            self.env['ir.attachment'].create(dict(
                name=vals.get('file_name', ''),
                datas_fname=vals.get('file_name', ''),
                datas=vals.get('image', ''),
                res_model='crm.stage',
                type='binary',
                res_id=res.id
            ))
        return res

    @api.multi
    def write(self, vals):
        res = super(CRMStage, self).write(vals)
        if vals.get('image', ''):
            self.env['ir.attachment'].create(dict(
                name=vals.get('file_name', ''),
                datas_fname=vals.get('file_name', ''),
                datas=vals.get('image', ''),
                res_model='crm.stage',
                type='binary',
                res_id=self.id
            ))
        return res