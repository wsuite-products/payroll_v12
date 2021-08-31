# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from odoo.exceptions import Warning
import base64
import logging
_logger = logging.getLogger(__name__)


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    def _default_stage_ids(self):
        return self.env['crm.stage'].search([])

    corporate_name = fields.Char()
    product_name = fields.Char()
    accepted_campiagn_date = fields.Date()
    version = fields.Integer()
    campaign_type = fields.Selection([
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large')
    ])
    campaign_redirect_state = fields.Char()
    reject_message = fields.Char()
    project_id = fields.Integer()
    business_category_name = fields.Char()
    cancel_message = fields.Char()
    main_category = fields.Selection([
        ('campaign', 'Campaign'),
        ('promotions', 'Promotions'),
        ('single_assets', 'Single - Assets')
    ])
    crm_lead_line_ids = fields.One2many(
        'crm.lead.lines',
        'crm_lead_id',
        string='Lead Lines',
        copy=True, auto_join=True)
    pricelist_id = fields.Many2one(
        'product.pricelist',
        string='Pricelist',
        help="Pricelist for current crm lead.")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.ref('base.COP'))
    partner_stage_ids = fields.Many2many(
        'crm.stage', default=_default_stage_ids)
    crm_lead_stage_ids = fields.One2many(
        'crm.lead.stage',
        'crm_lead_id',
        'CRM Lead Stage History')
    crm_lead_type_id = fields.Many2one('crm.lead.type', 'Lead Type')
    campaign_control = fields.Selection([
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
        ('semi_automatic', 'Semi Automatic')
    ])
    product_template_ids = fields.Many2many('product.template', string='Product Templates')
    users_ids = fields.Many2many('res.users', string='Team assign')
    product_quote_ids = fields.One2many(
        'crm.lead.product.quotes',
        'crm_lead_id',
        string="Product Quotes"
    )
    lead_global_config = fields.Text('Global Config')
    slug = fields.Char('Slug')
    reference_name_config = fields.Text('Reference Name Config')
    all_user_ids = fields.Many2many('res.users', 'crm_lead_all_user_details', 'crm_lead_id', 'new_user_id',  string='Users')
    add_member_user_ids = fields.One2many('new.member.history', 'lead_id')
    notification_history_ids = fields.One2many('notification.history', 'lead_id')
    job_ids = fields.One2many('job', 'lead_id')
    cdb_id = fields.Integer('CDB Id')
    status_info = fields.Char('Status Information')
    cancel_history_ids = fields.One2many('lead.cancel.history', 'lead_id')

    @api.onchange('pricelist_id')
    def onchange_pricelist(self):
        self.currency_id = False
        if self.pricelist_id:
            self.currency_id = self.pricelist_id.currency_id.id

    @api.multi
    def create_crm_lead_stage(self, stage, prev_stage):
        self.env['crm.lead.stage'].create({
            'crm_lead_id': self.id,
            'stage_id': stage,
            'pre_stage_id': prev_stage,
            'date': fields.Datetime.now()
        })

    @api.model
    def create(self, vals):
        res = super(CRMLead, self).create(vals)
        all_user_ids = []
        if res.users_ids:
            all_user_ids = res.users_ids.ids
        if res.user_id:
            all_user_ids.append(res.user_id.id)
        if all_user_ids:
            res.with_context({'set_user': False}).write({'all_user_ids': [(6, 0, all_user_ids)]})
        stage_ids = self.env['crm.stage'].search([])
        if res.partner_id and not res.pricelist_id:
            res.pricelist_id = res.partner_id.property_product_pricelist.id
        res.partner_stage_ids = [(6, 0, stage_ids.ids)]
        res.create_crm_lead_stage(res.stage_id.id, False)
        return res

    @api.multi
    def write(self, vals):
        if 'stage_id' in vals:
            check_exsist = self.crm_lead_stage_ids.filtered(
                lambda stage_line: stage_line.stage_id.id == vals['stage_id'])
            if check_exsist:
                raise Warning(_("You passed from this stage. Already "
                                "completed this stage process for this lead!"))
            self.create_crm_lead_stage(vals['stage_id'], self.stage_id.id)
        current_user_list = []
        if vals.get('users_ids', False):
            current_user_list = self.users_ids.ids
        res = super(CRMLead, self).write(vals)
        if current_user_list and self.users_ids:
            new_member_ids = list(set(self.users_ids.ids) - set(current_user_list))
            self.env['new.member.history'].create({
                'lead_id': self.id,
                'user_ids': [(6, 0, new_member_ids)]
                })
        if not self.env.context.get('set_user') and vals.get('users_ids') or vals.get('user_id'):
            all_user_ids = self.users_ids.ids
            all_user_ids.append(self.user_id.id)
            self.with_context({'set_user': True}).write({'all_user_ids': [(6, 0, all_user_ids)]})
        return res

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        values = self._onchange_partner_id_values(
            self.partner_id.id if self.partner_id else False)
        values.update({
            'pricelist_id': self.partner_id.property_product_pricelist.id,
        })
        self.update(values)

    @api.onchange('crm_lead_type_id')
    def _onchange_crm_lead_type_id(self):
        values = {}
        res = {'domain': {'state_id': []}}
        stage_ids = self.env['crm.stage'].search([])
        if stage_ids:
            values.update({'partner_stage_ids': [(6, 0, stage_ids.ids)]})
        domain = ['|', ('team_id', '=', False), ('team_id', '=', self.team_id)]
        if self.crm_lead_type_id.flows_ids:
            domain += [('id', 'in',
                        self.crm_lead_type_id.flows_ids.ids)]
            values.update({
                'partner_stage_ids':  [(
                    6, 0, self.crm_lead_type_id.flows_ids.ids)]})
        self.update(values)
        res['domain']['stage_id'] = domain
        return res

    @api.multi
    def sale_action_quotations_new(self):
        for lead_id in self:
            context = self.env.context.copy()
            lines = []
            line_ids = lead_id.crm_lead_line_ids.filtered(
                lambda line: not line.order_line_id)
            if not line_ids:
                raise Warning(_("Please add Lead Lines or "
                                "Quotation already created for all lines!"))
            for line_id in line_ids:
                lines.append((0, 0, {
                    'name': line_id.name,
                    'product_id': line_id.product_id.id,
                    'product_uom': line_id.product_id.uom_po_id.id,
                    'product_uom_qty': line_id.product_uom_qty,
                    'price_unit': line_id.price_unit,
                    'price_subtotal': line_id.price_subtotal,
                    'discount': line_id.discount,
                    'tax_id': [(6, 0, line_id.tax_id.ids)],
                    'crm_lead_line_id': line_id.id,
                    'order_date': line_id.order_date,
                    'product_tmpl_id': line_id.product_id.product_tmpl_id.id,
                    'hours': line_id.hours,
                    'price': line_id.product_uom_qty * line_id.price_unit,
                    'quotation_number': line_id.quotation_number,
                }))
            context.update({
                'default_quotation_selection_pro_ids': lines,
                'default_crm_lead_id': lead_id.id
            })
            return {
                'context': context,
                'view_type': 'form',
                'view_mode': 'form,tree,graph',
                'res_model': 'quotation.selection.process',
                'views': [(False, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'new',
            }

    @api.multi
    def action_create_quotation_select_line(self, line_ids=[]):
        crm_lead_line_ids = self.env['crm.lead.lines'].browse(line_ids)
        crm_lead_pq = self.env['crm.lead.product.quotes']
        order_lines = []
        for lead_id in self:
            template_list = []
            quotation_number = ''
            for line_id in crm_lead_line_ids:
                template_list.append(line_id.product_id.product_tmpl_id.id)
                if not quotation_number:
                    quotation_number = line_id.quotation_number
                order_lines.append((0, 0, {
                    'name': line_id.name,
                    'product_id': line_id.product_id.id,
                    'res_supplier_id': line_id.res_supplier_id.id,
                    'product_uom': line_id.product_id.uom_po_id.id,
                    'product_uom_qty': line_id.product_uom_qty,
                    'price_unit': line_id.price_unit,
                    'discount': line_id.discount,
                    'tax_id': [(6, 0, line_id.tax_id.ids)],
                    'crm_lead_line_id': line_id.id,
                    'order_date': line_id.order_date,
                    'product_tmpl_id': line_id.product_id.product_tmpl_id.id,
                    'hours': line_id.hours,
                    'price': line_id.product_uom_qty * line_id.price_unit,
                    'quotation_number': line_id.quotation_number,
                }))
            clpq_id = crm_lead_pq.search([
                ('quotation_number', '=', quotation_number),
                ('crm_lead_id', '=', lead_id.id)], limit=1)
            values = {
                'partner_id': lead_id.partner_id.id,
                'opportunity_id': lead_id.id,
                'partner_id': lead_id.partner_id.id,
                'team_id': lead_id.team_id.id,
                'campaign_id': lead_id.campaign_id.id,
                'medium_id': lead_id.medium_id.id,
                'origin': lead_id.name,
                'source_id': lead_id.source_id.id,
                'order_line': order_lines,
                'opportunity_id': lead_id.id,
                'quotation_number': quotation_number,
                'fee_check': clpq_id and clpq_id.is_fee,
                'product_template_ids': [(6, 0, template_list)],
            }
            sale_order_id = self.env['sale.order'].create(values)
            return sale_order_id.read()

    @api.multi
    def get_pre_quotation_report_url(self, lead_id=False, quotation_number=False):
        url = ""
        _logger.info("lead_id: %s %s", lead_id, type(lead_id))
        _logger.info("quotation_number: %s %s", quotation_number, type(quotation_number))
        if lead_id and quotation_number:
            line_ids = self.env['crm.lead.lines'].search([
                ('order_line_id', '=', False),
                ('order_id', '=', False),
                ('quotation_number', '=', quotation_number),
                ('crm_lead_id', '=', lead_id),
            ])
            check_report_type = any([line.media_config for line in line_ids if line.media_config])
            check_report_type_quote = any([line.quote_type for line in line_ids if line.quote_type])
            if check_report_type:
                pdf = self.env.ref('crm_lead_extended.action_report_leadline_custom').render_qweb_pdf(line_ids.ids)[0]
            elif check_report_type_quote:
                pdf = self.env.ref('crm_lead_extended.action_report_leadline_quote_type').render_qweb_pdf(line_ids.ids)[0]
            else:
                raise Warning(_("Record Not Found!"))
            pdf = base64.b64encode(pdf)
            name = 'Quotation'
            pdf_name = name + '.pdf'
            attachment = self.env['ir.attachment'].create({
                'name': pdf_name,
                'datas': pdf,
                'datas_fname': name,
                'res_model': 'crm.lead',
                'res_id': line_ids[0].crm_lead_id.id,
                'type': 'binary',
            })
            url = attachment.url
        _logger.info(_("\n\nQuotation Report URL : \n\n %s") % url)
        return url


class CancelHistory(models.Model):
    _name = 'lead.cancel.history'
    _description = 'Lead Cancel History'
    _rec_name = 'date'

    date = fields.Date('Date', default=fields.Date.context_today)
    lead_id = fields.Many2one('crm.lead', 'Lead')
    message = fields.Text('Message')
    user_id = fields.Many2one('res.users', 'User')
    stage_id = fields.Many2one('crm.lead.stage', 'Stage')


class NotificationHistory(models.Model):
    _name = 'notification.history'
    _description = 'Notification History'
    _rec_name = 'quotation_number'

    event_name = fields.Selection([
        ('request_of_approval', 'Request Of Approval'),
        ('send_to_production', 'Send To Production'),
        ('send_to_agency', 'Send To Agency')], 'Event Name')
    event_config = fields.Text('Event Config')
    lead_id = fields.Many2one('crm.lead', 'Lead')
    quotation_number = fields.Char('Quotation Number')
    approved_by = fields.Many2one('res.groups', 'Group')
    service_link = fields.Char('Service Link')
    user_ids = fields.Many2many('res.users', 'notification_users', 'notification_history_id', 'user_id',  string='Users')

    @api.model
    def create(self, vals):
        res = super(NotificationHistory, self).create(vals)
        if not self.env.context.get('set_user') and res.approved_by:
            rugb_obj = self.env['res.user.groups.brand']
            group_brand_user_list = []
            for user_id in res.lead_id.users_ids:
                rugb_id = rugb_obj.search([
                    ('user_id', '=', user_id.id),
                    ('group_id', '=', res.approved_by.id),
                    ('multi_id', '=', res.lead_id.brand_id.id)])
                if rugb_id:
                    group_brand_user_list.append(user_id.id)
            res.with_context({'set_user': True}).write({'user_ids': [(6, 0, group_brand_user_list)]})
        return res


class Job(models.Model):
    _name = 'job'
    _description = 'Job'
    _rec_name = 'job_name'

    job_name = fields.Char('Name')
    quotation_number = fields.Char('Quotation Number')
    job_type = fields.Char('Job Type')
    status = fields.Char('Status')
    job_res = fields.Text('Job Res')
    job_id = fields.Char('Job Id')
    media_type = fields.Char('Media Type')
    lead_id = fields.Many2one('crm.lead', 'Lead')
    job_inputs = fields.Text('Job Inputs')


class NewMemberHistory(models.Model):
    _name = 'new.member.history'
    _description = 'Member History'
    _rec_name = 'date'

    date = fields.Date('Date', default=fields.Date.context_today)
    lead_id = fields.Many2one('crm.lead', 'Lead')
    user_ids = fields.Many2many('res.users', 'new_member_history_users', 'member_history_id', 'user_id',  string='Users')


class CRMLeadLines(models.Model):
    _name = 'crm.lead.lines'
    _inherit = 'sale.order.line'
    _description = 'CRM Lead Lines'

    crm_lead_id = fields.Many2one(
        'crm.lead',
        string='Lead Reference',
        required=True,
        ondelete='cascade',
        index=True,
        copy=False,
        readonly=True)
    order_id = fields.Many2one(
        'sale.order',
        required=False,
        string='Order Reference')
    order_line_id = fields.Many2one(
        'sale.order.line',
        required=False,
        string='Order Line Reference')
    order_date = fields.Date('Date')
    product_tmpl_id = fields.Many2one(related='product_id.product_tmpl_id', string='Product Template')
    hours = fields.Float()
    price = fields.Float('Price')
    quote_type = fields.Selection([
        ('PR', 'Profit'),
        ('DC', 'Direct Cost'),
        ('IW', 'Internal Work'),
        ('PI', 'Product Items'),
        ('EP', 'External Product'),
    ])
    profit_percentage = fields.Float('Profit Percentage')
    pre_quotation = fields.Boolean('Pre Quotation')
    quotation_number = fields.Char('#Quotation Number')
    outputs_dates = fields.Text('Outputs Dates')
    reference = fields.Text('Reference')
    media_config = fields.Text('Media Config')
    task_assignee_config = fields.Text('Task Assignee Config')
    start_date = fields.Date('Start Date')
    is_distribute = fields.Boolean('Is Distribute?')
    distribution = fields.Float('Distribution')
    distribution_order_by = fields.Char('Distribution Order By')
    res_supplier_id = fields.Many2one('res.partner', 'Supplier', domain="[('supplier', '=', True)]")
    price_update_reason = fields.Char('Price Update Reason')
    description = fields.Text('Description')

    @api.model
    def create(self, vals):
        res = super(CRMLeadLines, self).create(vals)
        if not self.env.context.get('set_hours'):
            minutes = sum([mrw.time_cycle_manual for mrw in res.product_id.mapped('bom_ids.routing_id.operation_ids')])
            hours = 0.0
            if minutes:
                hours = minutes / 60
            res.with_context({'set_hours': True}).write({'hours': hours})
        return res

    @api.multi
    def write(self, vals):
        res = super(CRMLeadLines, self).write(vals)
        if not self.env.context.get('set_hours'):
            minutes = sum([mrw.time_cycle_manual for mrw in self.product_id.mapped('bom_ids.routing_id.operation_ids')])
            hours = 0.0
            if minutes:
                hours = minutes / 60
            self.with_context({'set_hours': True}).write({'hours': hours})
        return res

    @api.multi
    def _get_display_price(self, product):
        # it is possible that a no_variant attribute is still in a variant if
        # the type of the attribute has been changed after creation.
        no_variant_attr_price_extra = [
            ptav.price_extra for ptav in
            self.product_no_variant_attribute_value_ids.filtered(
                lambda ptav:
                    ptav.price_extra and
                    ptav not in product.product_template_attribute_value_ids
            )
        ]
        if no_variant_attr_price_extra:
            product = product.with_context(
                no_variant_attributes_price_extra=no_variant_attr_price_extra
            )

        if self.crm_lead_id.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(
                pricelist=self.crm_lead_id.pricelist_id.id).price
        product_context = dict(
            self.env.context,
            partner_id=self.crm_lead_id.partner_id.id,
            date=self.crm_lead_id.accepted_campiagn_date,
            uom=self.product_uom.id)

        final_price, rule_id = \
            self.crm_lead_id.pricelist_id.with_context(
                product_context).get_product_price_rule(
                self.product_id, self.product_uom_qty or 1.0,
                self.crm_lead_id.partner_id)
        base_price, currency = \
            self.with_context(product_context)._get_real_price_currency(
                product, rule_id, self.product_uom_qty,
                self.product_uom, self.crm_lead_id.pricelist_id.id)
        if currency != self.crm_lead_id.pricelist_id.currency_id:
            base_price = currency._convert(
                base_price,
                self.crm_lead_id.pricelist_id.currency_id,
                self.crm_lead_id.company_id,
                self.crm_lead_id.accepted_campiagn_date or
                fields.Date.today())
        return max(base_price, final_price)

    # @api.onchange('product_uom', 'product_uom_qty')
    # def product_uom_change(self):
    #     if not self.product_uom or not self.product_id:
    #         self.price_unit = 0.0
    #         return
    #     if self.crm_lead_id.pricelist_id and self.crm_lead_id.partner_id:
    #         product = self.product_id.with_context(
    #             lang=self.crm_lead_id.partner_id.lang,
    #             partner=self.crm_lead_id.partner_id,
    #             quantity=self.product_uom_qty,
    #             date=self.crm_lead_id.accepted_campiagn_date,
    #             pricelist=self.crm_lead_id.pricelist_id.id,
    #             uom=self.product_uom.id,
    #             fiscal_position=self.env.context.get('fiscal_position')
    #         )
    #         self.price_unit = \
    #             self.env['account.tax']._fix_tax_included_price_company(
    #                 self._get_display_price(product),
    #                 product.taxes_id, self.tax_id, self.company_id)
    #         price = self.price_unit
    #         if self.hours:
    #             self.price_unit = price * self.hours

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}
        # res = super(CRMLeadLines, self).product_id_change()
        minutes = sum([mrw.time_cycle_manual for mrw in self.product_id.mapped('bom_ids.routing_id.operation_ids')])
        vals = {}
        self.hours = 0.0
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = self.product_uom_qty or 1.0
        product = self.product_id.with_context(
            lang=self.crm_lead_id.partner_id.lang,
            partner=self.crm_lead_id.partner_id,
            quantity=self.product_uom_qty,
            date=self.crm_lead_id.accepted_campiagn_date,
            pricelist=self.crm_lead_id.pricelist_id.id,
            uom=self.product_uom.id
        )
        # vals['price'] = self.product_id.lst_price
        result = {'domain': domain}

        name = self.get_sale_order_line_multiline_description_sale(product)
        vals['name'] = name

        # if self.crm_lead_id.pricelist_id and self.crm_lead_id.partner_id:
        #     vals['price_unit'] = \
        #         self.env['account.tax']._fix_tax_included_price_company(
        #             self._get_display_price(product),
        #             product.taxes_id, self.tax_id, self.company_id)
        if minutes:
            hours = minutes / 60
            vals['hours'] = hours
            # vals['price_unit'] = vals['price_unit'] * hours

        self.update(vals)

        title = False
        message = False
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            result = {'warning': warning}
            if product.sale_line_warn == 'block':
                self.product_id = False

        return result

    @api.onchange('product_id', 'price_unit',
                  'product_uom', 'product_uom_qty', 'tax_id')
    def _onchange_discount(self):
        self.price = self.price_unit * self.product_uom_qty
        if not (self.product_id and self.product_uom and
                self.crm_lead_id.partner_id and
                self.crm_lead_id.pricelist_id and
                self.crm_lead_id.pricelist_id.discount_policy ==
                'without_discount' and
                self.env.user.has_group('sale.group_discount_per_so_line')):
            return

        self.discount = 0.0
        product = self.product_id.with_context(
            lang=self.crm_lead_id.partner_id.lang,
            partner=self.crm_lead_id.partner_id,
            quantity=self.product_uom_qty,
            date=self.crm_lead_id.accepted_campiagn_date,
            pricelist=self.crm_lead_id.pricelist_id.id,
            uom=self.product_uom.id,
            fiscal_position=self.env.context.get('fiscal_position')
        )
        product_context = \
            dict(self.env.context,
                 partner_id=self.crm_lead_id.partner_id.id,
                 date=self.crm_lead_id.accepted_campiagn_date,
                 uom=self.product_uom.id)
        price, rule_id = \
            self.crm_lead_id.pricelist_id.with_context(
                product_context).get_product_price_rule(
                self.product_id, self.product_uom_qty or 1.0,
                self.crm_lead_id.partner_id)
        new_list_price, currency = \
            self.with_context(product_context)._get_real_price_currency(
                product, rule_id, self.product_uom_qty,
                self.product_uom, self.crm_lead_id.pricelist_id.id)
        if new_list_price != 0:
            if self.crm_lead_id.pricelist_id.currency_id != currency:
                new_list_price = currency._convert(
                    new_list_price,
                    self.crm_lead_id.pricelist_id.currency_id,
                    self.crm_lead_id.company_id,
                    self.crm_lead_id.accepted_campiagn_date or
                    fields.Date.today())
            discount = (new_list_price - price) / new_list_price * 100
            if discount > 0:
                self.discount = discount
