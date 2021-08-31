# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    supplier_id = fields.Many2one('product.supplierinfo', 'Product Supplier')
    product_tmpl_id = fields.Many2one(
        related='product_id.product_tmpl_id', string='Template')

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        if self.product_id:
            self.supplier_id = \
                self.product_id.seller_ids and self.product_id.seller_ids[0]
            res['domain']['supplier_id'] = [
                ('id', 'in', self.product_id.seller_ids.ids)]
        return res

    @api.onchange('supplier_id')
    def _onchange_supplier_id(self):
        if self.supplier_id:
            self.supplier_id.write({'supplier_selected': True})
            product_supplierinfo_ids = self.env['product.supplierinfo'].search(
                [('id', '!=', self.supplier_id.id)])
            product_supplierinfo_ids.write({'supplier_selected': False})
            self.update({'price_unit': self.supplier_id.price})
            self.product_id.vendor_price = self.supplier_id.price
            self.product_tmpl_id.vendor_price = self.supplier_id.price
            self.product_id_change()
            self._onchange_discount()
