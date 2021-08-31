# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api

BINARY_FIELD_LIST = [
    'original_maternity_leave',
    'certificate_week_of_gestation',
    'birth_certificate',
    'certificate_born_alive',
    'support'
]


class HRNovelty(models.Model):
    _inherit = 'hr.novelty'

    original_maternity_leave_url = fields.Char('Original Maternity Leave URL')
    certificate_week_of_gestation_url = fields.Char(
        'Certificate Week of Gestation URL')
    birth_certificate_url = fields.Char('Birth Certificate URL')
    certificate_born_alive_url = fields.Char('Certificate Born Alive URL')

    @api.model
    def create(self, vals):
        res = super(HRNovelty, self).create(vals)
        attachment_obj = self.env['ir.attachment']
        for bin_field in BINARY_FIELD_LIST:
            if vals.get(bin_field, False):
                name = vals.get(
                    'file_name', '') if bin_field == 'support' else bin_field
                attachment_obj.create(dict(
                    name=name,
                    datas_fname=name,
                    datas=vals.get(bin_field, ''),
                    res_model='hr.novelty',
                    res_field=bin_field,
                    type='binary',
                    res_id=res.id
                ))
        return res

    @api.multi
    def write(self, vals):
        res = super(HRNovelty, self).write(vals)
        attachment_obj = self.env['ir.attachment']
        for bin_field in BINARY_FIELD_LIST:
            if vals.get(bin_field, False):
                name = vals.get(
                    'file_name', '') if bin_field == 'support' else bin_field
                attachment_obj.create(dict(
                    name=name,
                    datas_fname=name,
                    datas=vals.get(bin_field, ''),
                    res_model='hr.novelty',
                    res_field=bin_field,
                    type='binary',
                    res_id=self.id
                ))
        return res
