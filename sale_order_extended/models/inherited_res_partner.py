# Copyright 2019-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class Partner(models.Model):
    """Extend Partner."""

    _inherit = 'res.partner'

    users_ids = fields.Many2many('res.users', string='Users')
    brand_ids = fields.One2many('multi.brand', 'partner_id')
    sale_work_group_id = fields.Many2one('sale.work.group', 'Sale Work Group')
    db_wp_id = fields.Integer('DB WP id')
