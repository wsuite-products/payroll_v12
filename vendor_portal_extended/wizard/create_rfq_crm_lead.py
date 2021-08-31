# Copyright 2020-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _


class CreateRfqCrmLead(models.TransientModel):
    """Create Rfq Crm Lead."""

    _name = 'create.rfq.crm.lead'

    crm_lead_line_id = fields.Many2one('crm.lead.lines')
    template_id = fields.Many2one('crm.product.template')
    vendors_ids = fields.Many2many(
        'res.partner', domain="[('supplier','=',True)]", string="Vendor")

    @api.model
    def default_get(self, default_fields):
        """Fill Purchase Order."""
        rec = super(CreateRfqCrmLead, self).default_get(default_fields)
        if self._context.get('active_model', '') and self._context.get(
                'active_id', ''):
            if self._context.get('active_model', '') == 'crm.lead.lines':
                lead_line_id = self.env[self._context.get(
                    'active_model', '')].browse(self._context.get(
                        'active_id', ''))
                rec.update({
                    'crm_lead_line_id': lead_line_id.id,
                })
        return rec

    @api.multi
    def action_create_rfq(self):
        """Create RFQ."""
        for rec in self:
            vendor_rfq = self.env['vendor.rfq'].create({
                'product_id': rec.crm_lead_line_id.product_id.id,
                'qty': rec.crm_lead_line_id.product_uom_qty,
                'product_uom': rec.crm_lead_line_id.product_uom.id,
                'template_id': rec.template_id.id,
                'vendor_ids': [(6, 0, rec.vendors_ids.ids)],
                'crm_lead_line_id': rec.crm_lead_line_id.id,
                'pricelist_id':
                rec.crm_lead_line_id.crm_lead_id.pricelist_id.id
            })
            if vendor_rfq:
                for vendor in rec.vendors_ids:
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
                                    'qty': 0.0,
                                    'price_unitary': 0.0,
                                    'vrfq_line_id': rfq_line.id
                                })
                            rfq_line_price += line_tmp.price_subtotal
                    rfq_line.write({'rfq_price': rfq_line_price})
                return {
                    'name': _('Vendor RFQ'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'vendor.rfq',
                    'domain': [('id', '=', vendor_rfq.id)],
                }
