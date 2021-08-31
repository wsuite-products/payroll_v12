# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Kunjal Patel <kunjalpatel@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import datetime
import base64
import re
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)


class VendorRFQ(models.Model):
    _name = 'vendor.rfq'
    _rec_name = 'name'
    _description = 'Vendor Portal'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference',
                       required=True, copy=False, readonly=True,
                       index=True, default=lambda self: _('New'))
    product_id = fields.Many2one(comodel_name="product.product",
                                 string="Product")
    qty = fields.Float(string="Quantity")
    estimated_price = fields.Float(string="Estimated Price")
    estimated_del_date = fields.Date(string="Estimated Delivery")
    rfq_closing_date = fields.Date(string="RFQ Closing Date")
    pricelist_id = fields.Many2one(comodel_name="product.pricelist",
                                   string="Pricelist")
    sale_price = fields.Float(string="Sale Price")
    cost_price = fields.Float(string="Cost Price")
    vendor_ids = fields.Many2many('res.partner', string='Vendors')
    vendor_id = fields.Many2one('res.partner', string='Assigned Vendor')
    purchase_id = fields.Many2one('purchase.order', string='Purchase Order')
    rfq_price = fields.Float(string="Price")
    del_date = fields.Date(string="Delivery Date")
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    state = fields.Selection(string="Status",
                             selection=[('draft', 'Draft'),
                                        ('in_progress', 'In Progress'),
                                        ('pending', 'Pending'),
                                        ('cancel', 'Cancelled'),
                                        ('done', 'Done')], default='draft')
    currency_id = fields.Many2one(
        "res.currency",
        related='pricelist_id.currency_id',
        string="Pricelist Currency")
    is_assign_vendor = fields.Boolean(string="Is Assign Vendor ?")
    order_create = fields.Boolean(string="Is order create ?")
    rfq_line_ids = fields.One2many(comodel_name="vendor.rfq.line",
                                   inverse_name="rfq_id",
                                   string="RFQ History")
    report_url = fields.Char('Report S3 URL')
    notes = fields.Text(string="Note")

    @api.multi
    def generate_the_report_url(self):
        pdf = self.env.ref('vendor_portal_product.action_report_vendor_rfq').render_qweb_pdf(self.id)[0]
        pdf = base64.b64encode(pdf)
        pdf_name = re.sub(r'\W+', '', self.name) + '.pdf'
        attachment = self.env['ir.attachment'].create({
            'name': pdf_name,
            'datas': pdf,
            'datas_fname': self.name,
            'res_model': 'vendor.rfq',
            'res_id': self.id,
            'type': 'binary',
        })
        self.with_context(report_url=True).report_url = attachment.url

    @api.multi
    def action_purchase_order(self):
        self.ensure_one()
        return {
            'name': _('Purchase Order'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            # 'view_id': self.env.ref('account.invoice_form').id,
            'target': 'current',
            'res_id': self.purchase_id.id,
            }

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id

    @api.multi
    @api.onchange('pricelist_id')
    def pricelist_id_change(self):
        product = self.product_id.with_context(
            pricelist=self.pricelist_id.id,
            uom=self.product_uom.id
        )
        self.sale_price = product.lst_price
        self.cost_price = product.standard_price

    @api.multi
    def rfq_pending(self):
        self.state = 'pending'

    @api.multi
    def rfq_confirm(self):
        self.state = 'in_progress'

    @api.multi
    def rfq_cancel(self):
        self.state = 'cancel'

    @api.multi
    def action_draft(self):
        self.state = 'draft'

    @api.multi
    def create_purchase_order(self):
        purchase_obj = self.env['purchase.order']
        vals = {'name': self.product_id.name,
                'product_id': self.product_id.id,
                'product_qty': self.qty,
                'product_uom': self.product_uom.id,
                'price_unit': self.rfq_price,
                'crm_lead_line_id': self.crm_lead_line_id.id,
                'date_planned':
                    datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                }
        purchase_id = purchase_obj.create({'partner_id': self.vendor_id.id,
                                           'notes': self.notes,
                                           'order_line': [(0, 0, vals)]})
        self.order_create = True
        self.purchase_id = purchase_id.id

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = \
                self.env['ir.sequence'].next_by_code('vendor.rfq') or _('New')
        result = super(VendorRFQ, self).create(vals)
        return result

    '''
    @api.multi
    def write(self, vals):
        result = super(VendorRFQ, self).write(vals)
        check_delivery_date = all([line.del_date for line in self.rfq_line_ids])
        if not self._context.get('report_url') and check_delivery_date:
            self.generate_the_report_url()
        return result
    '''


class VendorRFQLine(models.Model):
    _name = 'vendor.rfq.line'
    _rec_name = 'vendor_id'
    _description = 'Vendor History'

    _sql_constraints = [(
        'rfq_vendor_id_uniq', 'unique (rfq_id,vendor_id)',
        'Duplicate Vendor in RFQ Details not allowed !')]

    vendor_id = fields.Many2one(comodel_name="res.partner", string="Vendor")
    rfq_price = fields.Float(string="Price")
    del_date = fields.Date(string="Delivery Date")
    note = fields.Text(string="Note")
    rfq_id = fields.Many2one(comodel_name="vendor.rfq", string="RFQ")
    is_accept = fields.Boolean(string="Accept")
    is_reject = fields.Boolean(string="Reject")

    @api.multi
    def write(self, vals):
        result = super(VendorRFQLine, self).write(vals)
        check_delivery_date = all([line.del_date for line in self.rfq_id.rfq_line_ids])
        _logger.info("\n\n===>>>context=check_delivery_date=>%s, %s", self._context, check_delivery_date)
        if check_delivery_date:
            self.rfq_id.generate_the_report_url()
        return result

    @api.multi
    def mark_done(self):
        self.is_accept = True
        self.rfq_id.write({'vendor_id': self.vendor_id.id,
                           'is_assign_vendor': True,
                           'rfq_price': self.rfq_price,
                           'del_date': self.del_date,
                           'state': 'done',
                           'notes': self.note,
                           })
        return True
