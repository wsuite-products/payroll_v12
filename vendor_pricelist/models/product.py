# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from odoo.tools import formatLang


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    vendor_price = fields.Float("Vendor Price", store=False)


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.multi
    def price_compute(self, price_type, uom=False,
                      currency=False, company=False):
        prices = super(ProductProduct, self).price_compute(
            price_type, uom, currency, company)
        if not uom and self._context.get('uom'):
            uom = self.env['uom.uom'].browse(self._context['uom'])
        if not currency and self._context.get('currency'):
            currency = self.env['res.currency'].browse(
                self._context['currency'])
        products = self
        for product in products:
            prices[product.id] = product[price_type] or 0.0
            supplier_selected = product.seller_ids.filtered(
                lambda r: r.supplier_selected)
            if price_type == 'vendor_price' and supplier_selected:
                prices[product.id] = product.vendor_price
            if uom:
                prices[product.id] = product.uom_id._compute_price(
                    prices[product.id], uom)
            if currency:
                prices[product.id] = product.currency_id._convert(
                    prices[product.id], currency,
                    product.company_id, fields.Date.today())
        return prices


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    supplier_selected = fields.Boolean("Supplier selected")

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            price = formatLang(
                self.env, record.price,
                monetary=True, currency_obj=record.currency_id)
            name = '%s [ %s ]' % (record.name.name, price or 0.0)
            result.append((record.id, name))
        return result
