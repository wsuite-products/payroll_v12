# -*- coding: utf-8 -*-
# Copyright 2020-TODAY Darshan Patel <darshan.barcelona@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class CRMAudienceAttributes(models.Model):
    """CRM Audience Attributes."""

    _name = 'crm.audience.attributes'
    _description = 'CRM Audience Attributes'

    name = fields.Text()


class CRMAudienceType(models.Model):
    """CRM Audience Type."""

    _name = 'crm.audience.type'
    _description = 'Audience Type'

    name = fields.Char('Name')


class CRMAudience(models.Model):
    """CRM Audience."""

    _name = 'crm.audience'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'CRM Audience'

    name = fields.Text()
    audience_line_ids = fields.One2many(
        'crm.audience.lines', 'audience_id')
    type_id = fields.Many2one('crm.audience.type', 'Type')


class CRMAudienceLines(models.Model):
    """CRM Audience Lines."""

    _name = 'crm.audience.lines'
    _description = 'Audience Lines'

    audience_id = fields.Many2one('crm.audience')
    attribute_id = fields.Many2one('crm.audience.attributes')
    condition = fields.Selection([
        ('greater', '>'),
        ('greater_equal', '>='),
        ('less', '<'),
        ('less_equal', '<='),
        ('equal', '='),
        ('not_equal', '!=')], default='greater')
    value = fields.Text()
