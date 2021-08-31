# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    currency_id = fields.Many2one('res.currency', string="Currency", readonly=False)
