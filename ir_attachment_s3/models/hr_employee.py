
from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    profile_image_url = fields.Char('Image URL', track_visibility='onchange')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    image_url = fields.Char('Image URL')

    @api.model
    def create(self, vals):
        # This code is for resolved the Incorrect padding issues.
        image_url = ''
        if vals.get('image_url'):
            image_url = vals['image_url']
            vals.pop('image_url')
        res = super(ResPartner, self).create(vals)
        if image_url:
            res.image_url = image_url
        return res

    @api.multi
    def write(self, vals):
        # This code resolved the issues when we change partner image.
        new_image = ''
        if vals.get('image', False):
            new_image = vals['image']
            self.image = False
        if new_image:
            vals['image'] = new_image
        return super(ResPartner, self).write(vals)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    image_url = fields.Char('Image URL')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    image_url = fields.Char('Image URL')
