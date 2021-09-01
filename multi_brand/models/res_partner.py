# -*- coding: utf-8 -*-
# Copyright 2019-TODAY WSuite Products <wsuite-products@destiny.ws>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    multi_brand_ids = fields.Many2many('multi.brand')


class ResUsersGroupsBrand(models.Model):
    _name = "res.user.groups.brand"
    _description = "Res Users Groups Brand"

    multi_id = fields.Many2one('multi.brand', 'Brand')
    group_id = fields.Many2one('res.groups', 'Group')
    user_id = fields.Many2one('res.users', 'User')
    product_id = fields.Many2one(related='group_id.product_id')
    is_brand_group = fields.Boolean('Is Brand Group?')
    partner_id = fields.Many2one('res.partner', string='Partner')


class ResUser(models.Model):
    _inherit = "res.users"

    group_brand_ids = fields.One2many('res.user.groups.brand', 'user_id')
    brand_ids = fields.Many2many('multi.brand', string='Brands')
    client_ids = fields.Many2many('res.partner', string='Clients')
    group_id = fields.Many2one('res.groups', 'Group')
    job_profile_id = fields.Many2one('hr.job')
    operation_zone = fields.Char('Operation Zone')
    redirect_to = fields.Char('Redirect To')
