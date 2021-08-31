# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api

BINARY_FIELD_LIST = [
    'image'
]


class HRModuleYOU(models.Model):
    _name = "hr.module.you"
    _description = "HR Module YOU"

    name = fields.Char('Name', required=True)
    tag = fields.Char('Tag')
    reference_module = fields.Char('Reference Module')
    group_id = fields.Many2one('res.groups', 'Group')
    show = fields.Boolean('Show')
    description = fields.Text('Description')
    parent_id = fields.Many2one('hr.module.you', 'Parent')
    image = fields.Binary()
    support_name = fields.Char()
    support_attachment_url = fields.Char("Image URL")
    file_name = fields.Char("File Name", track_visibility='onchange')
    type = fields.Many2one('hr.you.type')
    function = fields.Selection([
        ('any', 'Any'),
        ('create_pending', 'Create Pending'),
        ('created', 'Created')], default='any')
    field_ids = fields.One2many('hr.you.fields.type.conf', 'hr_module_you_id')
    event_id = fields.Many2one('hr.novelty.event', 'Novelty Event')

    @api.model
    def create(self, vals):
        res = super(HRModuleYOU, self).create(vals)
        attachment_obj = self.env['ir.attachment']
        for bin_field in BINARY_FIELD_LIST:
            if vals.get(bin_field, False):
                name = vals.get(
                    'support_name', '') if bin_field == 'image' else\
                    bin_field
                attachment_obj.create(dict(
                    name=name,
                    datas_fname=name,
                    datas=vals.get(bin_field, ''),
                    res_model='hr.module.you',
                    res_field=bin_field,
                    type='binary',
                    res_id=res.id
                ))
        return res

    @api.multi
    def write(self, vals):
        res = super(HRModuleYOU, self).write(vals)
        attachment_obj = self.env['ir.attachment']
        for bin_field in BINARY_FIELD_LIST:
            if vals.get(bin_field, False):
                name = vals.get(
                    'support_name', '') if bin_field == 'image' else\
                    bin_field
                attachment_obj.create(dict(
                    name=name,
                    datas_fname=name,
                    datas=vals.get(bin_field, ''),
                    res_model='hr.module.you',
                    res_field=bin_field,
                    type='binary',
                    res_id=self.id
                ))
        return res
