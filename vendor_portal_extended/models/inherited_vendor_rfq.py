# Copyright 2020-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api


class VendorRfq(models.Model):
    """Vendor Rfq."""

    _inherit = 'vendor.rfq'

    crm_lead_line_id = fields.Many2one('crm.lead.lines', 'Lead Line')
    template_id = fields.Many2one('crm.product.template')


class VendorRfqLine(models.Model):
    """Vendor Rfq Line."""

    _inherit = 'vendor.rfq.line'

    @api.depends('vrfq_template_line_ids',
                 'vrfq_template_line_ids.price_subtotal')
    def _compute_rfq_price(self):
        for rec in self:
            price = 0.0
            for template in rec.vrfq_template_line_ids:
                price += template.price_subtotal
            rec.rfq_price = price

    vendor_rfq_line_template_id = fields.Many2one(
        'vendor.rfq.line.template', 'Template')
    vrfq_template_line_ids = fields.One2many(
        'vendor.rfq.line.template', 'vrfq_line_id')
    rfq_price = fields.Float(string="Price", compute="_compute_rfq_price")


class VendorRfqLineTemplate(models.Model):
    """Vendor Rfq Line Template."""

    _name = 'vendor.rfq.line.template'
    _rec_name = 'product_id'

    @api.depends('qty', 'price_unitary')
    def _compute_price_subtotal(self):
        for rec in self:
            if rec.qty > 0.0 and rec.price_unitary > 0.0:
                rec.price_subtotal = rec.price_unitary * rec.qty

    product_id = fields.Many2one('product.product', 'Product')
    qty = fields.Float()
    price_unitary = fields.Float()
    price_subtotal = fields.Float(compute="_compute_price_subtotal")
    file = fields.Binary()
    vrfq_line_id = fields.Many2one('vendor.rfq.line')
    del_date = fields.Date(string="Delivery Date")
    note = fields.Text(string="Note")
    profit_price_total = fields.Float()


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    @api.multi
    def action_create_rfq(self, line_id, crm_product_template_id):
        crm_lead_line_ids = self.env['crm.lead.lines'].browse(line_id)
        for crm_lead_line_id in crm_lead_line_ids:
            seller_ids = crm_lead_line_id.product_id.seller_ids
            supplier_list = seller_ids.mapped('name')
            vendor_rfq = self.env['vendor.rfq'].create({
                'product_id': crm_lead_line_id.product_id.id,
                'qty': crm_lead_line_id.product_uom_qty,
                'product_uom': crm_lead_line_id.product_uom.id,
                'template_id': crm_product_template_id,
                'vendor_ids': [(6, 0, supplier_list.ids)],
                'crm_lead_line_id': crm_lead_line_id.id,
            })
            line_tmp = self.env['vendor.rfq.line.template'].create({
                'product_id': vendor_rfq.product_id.id,
                'qty': 0,  # vendor_rfq.qty,
                'price_unitary': 0,  # crm_lead_line_id.price
            })
            for vendor in seller_ids:
                self.env['vendor.rfq.line'].create({
                    'vendor_rfq_line_template_id': line_tmp.id,
                    'vendor_id': vendor.name.id,
                    'rfq_price': line_tmp.price_subtotal,
                    'rfq_id': vendor_rfq.id,
                })
            return vendor_rfq.read()

    @api.multi
    def action_create_rfq_static(self, line_id, crm_product_template_id, vendors_ids):
        """Create RFQ."""
        line_id = self.env['crm.lead.lines'].browse(line_id)
        crm_product_template_id = self.env['crm.product.template'].browse(
            crm_product_template_id)
        vendors_ids = self.env['res.partner'].browse(vendors_ids)
        vendor_rfq = self.env['vendor.rfq'].create({
            'product_id': line_id.product_id.id,
            'qty': line_id.product_uom_qty,
            'product_uom': line_id.product_uom.id,
            'template_id': crm_product_template_id.id,
            'vendor_ids': [(6, 0, vendors_ids.ids)],
            'crm_lead_line_id': line_id.id,
            'pricelist_id':
            line_id.crm_lead_id.pricelist_id.id
        })
        if vendor_rfq:
            for vendor in vendors_ids:
                rfq_line = self.env['vendor.rfq.line'].create({
                    'vendor_id': vendor.id,
                    'rfq_id': vendor_rfq.id,
                })
                rfq_line_price = 0.0
                if rfq_line and vendor_rfq.template_id and\
                        vendor_rfq.template_id.template_line_ids:
                    for template_line in\
                            vendor_rfq.template_id.template_line_ids:
                        line_tmp = self.env[
                            'vendor.rfq.line.template'].create({
                                'product_id': template_line.product_id.id,
                                'qty': 0,  # vendor_rfq.qty,
                                'price_unitary': 0,  # line_id.price,
                                'vrfq_line_id': rfq_line.id
                            })
                        rfq_line_price += line_tmp.price_subtotal
                rfq_line.write({'rfq_price': rfq_line_price})
            return vendor_rfq.read()
