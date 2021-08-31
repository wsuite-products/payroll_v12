# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResRequest(models.Model):
    _name = 'res.request'
    _order = 'date desc'
    _description = 'Request'

    name = fields.Char(
        string='Subject',
        required=True
    )
    date = fields.Datetime(string='Date')
    act_from_id = fields.Many2one(
        'res.users',
        string='From'
    )
    act_to_id = fields.Many2one(
        'res.users',
        string='To'
    )
    body = fields.Text(string='Request')
