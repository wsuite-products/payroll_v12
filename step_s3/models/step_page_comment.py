# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class StepPageComment(models.Model):
    _inherit = 'step.page.comment'

    @api.model
    def create(self, vals):
        res = super(StepPageComment, self).create(vals)
        if vals.get('attachment', ''):
            self.env['ir.attachment'].create(dict(
                name=vals.get('file_name', ''),
                datas_fname=vals.get('file_name', ''),
                datas=vals.get('attachment', ''),
                res_model='step.page.comment',
                type='binary',
                res_id=res.id
            ))
        return res
    
    @api.multi
    def write(self, vals):
        res = super(StepPageComment, self).write(vals)
        if vals.get('attachment', ''):
            self.env['ir.attachment'].create(dict(
                name=vals.get('file_name', ''),
                datas_fname=vals.get('file_name', ''),
                datas=vals.get('attachment', ''),
                res_model='step.page.comment',
                type='binary',
                res_id=self.id
            ))
        return res