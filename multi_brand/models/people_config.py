# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class PeopleConfig(models.Model):
    _name = "people.config"
    _description = 'People Config'

    name = fields.Char('Name', required=True)
    user_id = fields.Many2one('res.users', string='User', required=False, default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string='Partner')
    brand_id = fields.Many2one('multi.brand', string='Brand')
    json_data = fields.Text('Json Data')
    category_name = fields.Char('Category Name')
    category_slug = fields.Char('Category Slug')
    # is_add_more = fields.Boolean('Is_add_more?')
