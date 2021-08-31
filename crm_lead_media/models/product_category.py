# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# Copyright 2020-TODAY Darshan Patel <darshan.barcelona@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
import threading
import logging
_logger = logging.getLogger(__name__)


class ProductCategory(models.Model):
    _inherit = 'product.category'

    media = fields.Boolean('Media', track_visibility='onchange')
    fringe = fields.Boolean('Fringe', track_visibility='onchange')
    channel = fields.Boolean('Channel', track_visibility='onchange')
    active = fields.Boolean("Active", default=True)
    description = fields.Text('Description')
    no_show = fields.Boolean("No Show")
    quotation_template_category = fields.Boolean("Quotation Template Category")
    crm_product_categ_tag_ids = fields.Many2many(
        'crm.product.categ.tag',
        'product_category_crm_product_categ_tag_default_rel',
        'product_category_id', 'crm_product_categ_tag_id')
    crm_audience_ids = fields.Many2many(
        'crm.audience',
        'product_category_crm_audience_default_rel',
        'product_category_id', 'crm_audience_id')
    icon = fields.Char('Icon')
    product_type = fields.Selection([('internal', 'Internal'), ('external', 'External')], "Product Type",  default='internal')

    def get_vendor_ids(self, categ_id=None):
        product_ids = self.env['product.product'].search([('categ_id', 'child_of', categ_id)])
        vendor_ids = []
        if product_ids.mapped('item_ids'):
            for item_id in product_ids.mapped('item_ids'):
                if not item_id.vendor_id or item_id.vendor_id.id in vendor_ids:
                    continue
                vendor_ids.append(item_id.vendor_id.id)
        return vendor_ids

    @api.multi
    def action_delete_category_related_data_api(self, category_id=None):
        if category_id:
            category = self.browse([category_id])
            product_template_obj = self.env['product.template']
            template_ids = product_template_obj.search([('categ_id', 'child_of', [category_id])])
            if template_ids:
                self.generic_for_delete_category_related_data(template_ids)
                _logger.info("Data Deleted successfully related to Product Category!")
                category.unlink()
                return "Data Deleted successfully related to Product Category!"
            else:
                _logger.info("Data not found related to given Product Category!")
                category.unlink()
                return "Data not found related to given Product Category!"
        else:
            _logger.info("Please provide the Product Category!")
            return "Please provide the Product Category!"

    @api.multi
    def generic_for_delete_category_related_data(self, template_ids):
        bom_obj = self.env['mrp.bom']
        product_obj = self.env['product.product']
        crm_lead_lines_obj = self.env['crm.lead.lines']
        sale_order_line_obj = self.env['sale.order.line']
        purchase_order_line_obj = self.env['purchase.order.line']
        for template_id in template_ids:
            product_ids = product_obj.search(['|', ('product_tmpl_id', '=', template_id.id), ('categ_id', '=', self.id)])
            bom_ids = bom_obj.search(['|', ('product_id', 'in', product_ids.ids), ('product_tmpl_id', '=', template_id.id)])
            for bom_id in bom_ids:
                if bom_id.routing_id:
                    bom_id.routing_id.unlink()
            if bom_ids:
                self._cr.execute('DELETE FROM mrp_production WHERE bom_id in %s', (tuple(bom_ids.ids),))
                bom_ids.unlink()

            if product_ids:
                lead_line_ids = crm_lead_lines_obj.search([('product_id', 'in', product_ids.ids)])
                lead_ids = lead_line_ids.mapped('crm_lead_id')
                if lead_ids:
                    _logger.info("lead_ids==> %s", lead_ids)
                    self._cr.execute('DELETE FROM crm_lead WHERE id in %s', (tuple(lead_ids.ids),))

                sale_order_line_ids = sale_order_line_obj.search([('product_id', 'in', product_ids.ids)])
                order_ids = sale_order_line_ids.mapped('order_id')
                if order_ids:
                    _logger.info("order_ids==> %s", order_ids)
                    self._cr.execute('DELETE FROM sale_order WHERE id in %s', (tuple(order_ids.ids),))

                purchase_order_line_ids = purchase_order_line_obj.search([('product_id', 'in', product_ids.ids)])
                purchase_order_ids = purchase_order_line_ids.mapped('order_id')
                if purchase_order_ids:
                    _logger.info("purchase_order_ids==> %s", purchase_order_ids)
                    self._cr.execute('DELETE FROM purchase_order WHERE id in %s', (tuple(purchase_order_ids.ids),))

                self._cr.execute('DELETE FROM stock_move WHERE product_id in %s', (tuple(product_ids.ids),))
                self._cr.execute('DELETE FROM mrp_production WHERE product_id in %s', (tuple(product_ids.ids),))
        template_ids.unlink()

    @api.multi
    def action_delete_category_related_data(self):
        product_template_obj = self.env['product.template']
        template_ids = product_template_obj.search([('categ_id', 'child_of', self.ids)])
        self.generic_for_delete_category_related_data(template_ids)
        _logger.info("Data Deleted successfully related to Product Category!")
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


class CrmProductCategTag(models.Model):
    """CRM Product Categ Tag."""

    _name = 'crm.product.categ.tag'
    _description = 'CRM Product Category Tag'

    @api.depends('type', 'value')
    def _calculate_name(self):
        """CRM Product Categ Tag Name Fill."""
        for rec in self:
            if rec.type and rec.value:
                rec.name = rec.type + ' ' + rec.value

    name = fields.Text(compute='_calculate_name')
    type = fields.Text()
    value = fields.Text()
    date = fields.Date('Date')
