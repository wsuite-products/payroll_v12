# Copyright 2019-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class CreatePurchaseOrder(models.TransientModel):
    """"Create Purchase Order."""

    _name = 'create.purchase.order'
    _description = "Create Purchase Order"

    partner_id = fields.Many2one('res.partner', 'Vendor')
    date_order = fields.Datetime(
        'Scheduled Date', default=lambda self: fields.Datetime.now())
    cpol_ids = fields.One2many('create.purchase.order.line', 'cpo_id')

    @api.model
    def default_get(self, default_fields):
        """Fill Purchase Order."""
        rec = super(CreatePurchaseOrder, self).default_get(default_fields)
        context = self._context
        if context.get('active_model', '') and context.get('active_id', ''):
            so = self.env[context.get('active_model', '')].browse(
                context.get('active_id', ''))
            if so.partner_id.supplier:
                rec.update({'partner_id': so.partner_id.id})
            if so.order_line:
                filb_values = [
                    (0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.product_id.with_context(
                            lang=self.partner_id.lang,
                            partner_id=self.partner_id.id,
                        ).display_name or '' +
                        '\n' + line.product_id.with_context(
                            lang=so.partner_id.lang,
                            partner_id=so.partner_id.id
                        ).description_purchase or '',
                        'product_qty': line.product_uom_qty,
                        'price_unit': line.product_id.standard_price or
                        line.price_unit,
                        'price_subtotal': line.product_uom_qty *
                        line.product_id.standard_price or line.price_unit
                    }) for line in so.order_line]
                rec.update({'cpol_ids': filb_values})
        return rec

    @api.multi
    def action_create_purchase_order(self):
        """Create Purchase Order."""
        for rec in self:
            po = self.env['purchase.order'].create({
                'partner_id': rec.partner_id.id,
                'date_order': rec.date_order,
                'so_id': self._context.get('active_id', '')
            })
            if rec.cpol_ids:
                for line in rec.cpol_ids:
                    self.env['purchase.order.line'].create({
                        'order_id': po.id,
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'product_qty': line.product_qty,
                        'price_unit': line.price_unit,
                        'date_planned': rec.date_order,
                        'product_uom': line.product_id.uom_po_id.id or
                        line.product_id.uom_id.id
                    })
            return {
                'res_id': po.id,
                'name': 'Purchase Order',
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'purchase.order',
                'type': 'ir.actions.act_window',
            }


class CreatePurchaseOrderLine(models.TransientModel):
    """"Create Purchase Order Line."""

    _name = 'create.purchase.order.line'
    _description = "Create Purchase Order Line"

    @api.depends('price_unit', 'product_qty')
    def _calculate_price_subtotal(self):
        for rec in self:
            rec.price_subtotal = rec.price_unit * rec.product_qty

    product_id = fields.Many2one('product.product', 'Product')
    name = fields.Text('Description')
    product_qty = fields.Float('Quantity')
    price_unit = fields.Float('Unit Price')
    price_subtotal = fields.Float(
        'Subtotal',
        compute='_calculate_price_subtotal')
    cpo_id = fields.Many2one('create.purchase.order')
