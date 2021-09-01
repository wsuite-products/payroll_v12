# -*- coding: utf-8 -*-
# Copyright 2019-TODAY WSuite Products <wsuite-products@destiny.ws>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class AssetsConfig(models.Model):
    _name = "assets.config"
    _description = 'Assets Config'

    name = fields.Char('Name')
    provider_id = fields.Many2one('product.supplierinfo', string='Provider')
    partner_id = fields.Many2one('res.partner', string='Partner')
    brand_id = fields.Many2one('multi.brand', string='Brand')
    config_data = fields.Text('Json Data')
    asset_config_type = fields.Selection([('sms', 'SMS'), ('email', 'Email'), ('others', 'Others')])
    is_test_success = fields.Boolean('Is Test Success?')
    is_default = fields.Boolean(string="Default?", default=False)


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    image = fields.Binary('image')
    image_url = fields.Char('Image URL')
    file_name = fields.Char("File Name")

    @api.model
    def create(self, vals):
        """Add binary field in the attachment."""
        res = super(ProductSupplierInfo, self).create(vals)
        if vals.get('image', '') or vals.get('file_name', ''):
            self.env['ir.attachment'].create(dict(
                name=vals.get('file_name', ''),
                datas_fname=vals.get('file_name', ''),
                datas=vals.get('image', ''),
                res_model='product.supplierinfo',
                type='binary',
                res_field='image',
                res_id=res.id
            ))
        return res

    @api.multi
    def write(self, vals):
        """Add binary field in the attachment."""
        if vals.get('image', ''):
            self.env['ir.attachment'].create(dict(
                name=vals.get('file_name') or self.file_name,
                datas_fname=vals.get('file_name') or self.file_name,
                datas=vals.get('image', ''),
                res_model='product.supplierinfo',
                type='binary',
                res_field='image',
                res_id=self.id
                ))
        return super(ProductSupplierInfo, self).write(vals)
