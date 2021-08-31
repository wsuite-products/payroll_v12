# Copyright 2019-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class HrYouFieldsTypes(models.Model):
    """Hr You Fields Types."""

    _name = "hr.you.fields.types"
    _description = "Hr You Fields Types"

    name = fields.Text()


class HrYouFields(models.Model):
    """Hr You Fields."""

    _name = "hr.you.fields"
    _description = "Hr You Fields"

    name = fields.Text()
    type_id = fields.Many2one('hr.you.fields.types', 'Type')


class HrYouFieldsTypeConf(models.Model):
    """Hr You Fields Type Conf."""

    _name = "hr.you.fields.type.conf"
    _description = "Hr You Fields Type Conf"
    _rec_name = 'field_id'

    field_id = fields.Many2one('hr.you.fields', 'Fields')
    type_id = fields.Many2one(
        related="field_id.type_id",
        string="Type")
    message = fields.Text()
    event_id = fields.Many2one('hr.module.you', 'Event')
    hr_module_you_id = fields.Many2one('hr.module.you')
