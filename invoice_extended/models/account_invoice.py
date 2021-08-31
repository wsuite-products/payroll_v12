# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import json


from odoo import models, fields, api, _
from odoo.addons.account.models import account_invoice as AI
from odoo.tools import float_is_zero


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount',
                 'tax_line_ids.amount_rounding',
                 'currency_id', 'company_id', 'date_invoice', 'type')
    def _compute_amount(self):
        round_curr = self.currency_id.round
        self.amount_untaxed = sum(
            line.price_subtotal for line in self.invoice_line_ids)
        self.amount_tax = sum(round_curr(
            line.amount_total) for line in self.tax_line_ids)
        self.amount_total = self.amount_untaxed + self.amount_tax
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.company_id and \
                self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id
            amount_total_company_signed = currency_id._convert(
                self.amount_total, self.company_id.currency_id,
                self.company_id, self.date_invoice or fields.Date.today())
            amount_untaxed_signed = currency_id._convert(
                self.amount_untaxed, self.company_id.currency_id,
                self.company_id,
                self.date_invoice or fields.Date.today())
        sign = self.type in ['in_refund', 'out_refund',
                             'out_refund_account_collection'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign

    @api.multi
    def invoice_validate(self):
        for invoice in self.filtered(lambda invoice:
                                     invoice.partner_id not in
                                     invoice.message_partner_ids):
            if not invoice.reference and \
                    invoice.type == 'out_account_collection':
                invoice.reference = invoice._get_computed_reference()
        res = super(AccountInvoice, self).invoice_validate()
        return res

    @api.one
    def _get_outstanding_info_JSON(self):
        self.outstanding_credits_debits_widget = json.dumps(False)
        if self.state == 'open':
            domain = [('account_id', '=', self.account_id.id),
                      ('partner_id', '=',
                       self.env['res.partner']._find_accounting_partner(
                           self.partner_id).id),
                      ('reconciled', '=', False),
                      '|', '&', ('amount_residual_currency', '!=', 0.0),
                      ('currency_id', '!=', None),
                      '&', ('amount_residual_currency', '=', 0.0), '&',
                      ('currency_id', '=', None),
                      ('amount_residual', '!=', 0.0)]
            if self.type in ('out_invoice', 'in_refund',
                             'out_account_collection',
                             'out_refund_account_collection'):
                domain.extend([('credit', '>', 0), ('debit', '=', 0)])
                type_payment = _('Outstanding credits')
            else:
                domain.extend([('credit', '=', 0), ('debit', '>', 0)])
                type_payment = _('Outstanding debits')
            info = {'title': '',
                    'outstanding': True, 'content': [], 'invoice_id': self.id}
            lines = self.env['account.move.line'].search(domain)
            currency_id = self.currency_id
            if len(lines) != 0:
                for line in lines:
                    # get the outstanding residual value in invoice currency
                    if line.currency_id and \
                            line.currency_id == self.currency_id:
                        amount_to_show = abs(line.amount_residual_currency)
                    else:
                        currency = line.company_id.currency_id
                        amount_to_show = \
                            currency._convert(abs(line.amount_residual),
                                              self.currency_id,
                                              self.company_id,
                                              line.date or fields.Date.today())
                    if float_is_zero(
                            amount_to_show,
                            precision_rounding=self.currency_id.rounding):
                        continue
                    if line.ref:
                        title = '%s : %s' % (line.move_id.name, line.ref)
                    else:
                        title = line.move_id.name
                    info['content'].append({
                        'journal_name': line.ref or line.move_id.name,
                        'title': title,
                        'amount': amount_to_show,
                        'currency': currency_id.symbol,
                        'id': line.id,
                        'position': currency_id.position,
                        'digits': [69, self.currency_id.decimal_places],
                    })
                info['title'] = type_payment
                self.outstanding_credits_debits_widget = json.dumps(info)
                self.has_outstanding = True

    @api.multi
    def compute_invoice_totals(self, company_currency, invoice_move_lines):
        if self.type == 'out_account_collection':
            total = 0
            total_currency = 0
            for line in invoice_move_lines:
                if self.currency_id != company_currency:
                    currency = self.currency_id
                    date = \
                        self._get_currency_rate_date() or \
                        fields.Date.context_today(self)
                    if not (line.get('currency_id') and
                            line.get('amount_currency')):
                        line['currency_id'] = currency.id
                        line['amount_currency'] = currency.round(line['price'])
                        line['price'] = \
                            currency._convert(line['price'],
                                              company_currency,
                                              self.company_id, date)
                else:
                    line['currency_id'] = False
                    line['amount_currency'] = False
                    line['price'] = self.currency_id.round(line['price'])
                total += line['price']
                total_currency += line['amount_currency'] or line['price']
                line['price'] = - line['price']
            return total, total_currency, invoice_move_lines
        else:
            return super(AccountInvoice, self).compute_invoice_totals(
                company_currency, invoice_move_lines)

    @api.model
    def default_get(self, default_fields):
        # Account Collection
        AI.TYPE2JOURNAL.update({
            'out_account_collection': 'sale',
            'out_refund_account_collection': 'purchase'})
        AI.TYPE2REFUND.update({
            'out_account_collection': 'out_refund_account_collection',
            'out_refund_account_collection': 'out_account_collection'
        })
        return super(AccountInvoice, self).default_get(default_fields)

    @api.model
    def _default_journal(self):
        if self._context.get('type') != 'out_account_collection':
            return super(AccountInvoice, self)._default_journal()
        if self._context.get('default_journal_id', False):
            return self.env['account.journal'].browse(
                self._context.get('default_journal_id'))
        inv_type = self._context.get('type', 'out_account_collection')
        inv_types = inv_type if isinstance(inv_type, list) else [inv_type]
        company_id = self._context.get(
            'company_id', self.env.user.company_id.id)
        domain = [
            ('type', 'in', [AI.TYPE2JOURNAL[ty] for ty in inv_types
                            if ty in AI.TYPE2JOURNAL]),
            ('company_id', '=', company_id),
            ('code', '=', 'ACJ')]
        journal_with_currency = False
        if self._context.get('default_currency_id'):
            currency_clause = [
                ('currency_id', '=', self._context.get('default_currency_id'))]
            journal_with_currency = self.env[
                'account.journal'].search(domain + currency_clause, limit=1)
        return journal_with_currency or self.env[
            'account.journal'].search(domain, limit=1)

    @api.multi
    def name_get(self):
        TYPES = {
            'out_invoice': _('Invoice'),
            'in_invoice': _('Vendor Bill'),
            'out_refund': _('Credit Note'),
            'in_refund': _('Vendor Credit note'),
            'out_account_collection': _('Account Collection'),
            'out_refund_account_collection': _('Credit Account Collection'),
        }
        result = []
        for inv in self:
            result.append((
                inv.id, "%s %s" % (
                    inv.number or TYPES[inv.type], inv.name or '')))
        return result

    type = fields.Selection(selection_add=[
        ('out_account_collection', 'Out Account Collection'),
        ('out_refund_account_collection', 'Out Refund Account Collection')
    ])
    journal_id = fields.Many2one(
        'account.journal', string='Journal',
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=_default_journal,
        domain="[('type', 'in', {'out_invoice': ['sale'],"
               " 'out_refund': ['sale'], 'out_account_collection' : ['sale'],"
               " 'in_refund': ['purchase'], 'in_invoice': ['purchase']"
               "}.get(type, [])), ('company_id', '=', company_id)]")

    @api.model
    def _get_payments_vals(self):
        if not self.payment_move_line_ids:
            return []
        payment_vals = []
        currency_id = self.currency_id
        amount_currency = 0.0
        amount = 0.0
        for payment in self.payment_move_line_ids:
            payment_currency_id = False
            if self.type in ('out_invoice', 'in_refund',
                             'out_account_collection'):
                amount = sum([p.amount for p in payment.matched_debit_ids
                              if p.debit_move_id in self.move_id.line_ids])
                amount_currency = sum(
                    [p.amount_currency for p in payment.matched_debit_ids
                     if p.debit_move_id in self.move_id.line_ids])
                if payment.matched_debit_ids:
                    payment_currency_id = \
                        all([p.currency_id == payment.matched_debit_ids[
                            0].currency_id for p in payment.matched_debit_ids]
                            ) and payment.matched_debit_ids[
                            0].currency_id or False
            elif self.type in ('in_invoice', 'out_refund',
                               'out_refund_account_collection'):
                amount = sum([p.amount for p in payment.matched_credit_ids
                              if p.credit_move_id in self.move_id.line_ids])
                amount_currency = \
                    sum([p.amount_currency for p in payment.matched_credit_ids
                         if p.credit_move_id in self.move_id.line_ids])
                if payment.matched_credit_ids:
                    payment_currency_id = \
                        all([p.currency_id == payment.matched_credit_ids[
                            0].currency_id for p in payment.matched_credit_ids]
                            ) and payment.matched_credit_ids[0].currency_id \
                        or False
            # get the payment value in invoice currency
            if payment_currency_id and payment_currency_id == self.currency_id:
                amount_to_show = amount_currency
            else:
                currency = payment.company_id.currency_id
                amount_to_show = currency._convert(
                    amount, self.currency_id,
                    payment.company_id, self.date or fields.Date.today())
            if float_is_zero(amount_to_show,
                             precision_rounding=self.currency_id.rounding):
                continue
            payment_ref = payment.move_id.name
            if payment.move_id.ref:
                payment_ref += ' (' + payment.move_id.ref + ')'
            payment_vals.append({
                'name': payment.name,
                'journal_name': payment.journal_id.name,
                'amount': amount_to_show,
                'currency': currency_id.symbol,
                'digits': [69, currency_id.decimal_places],
                'position': currency_id.position,
                'date': payment.date,
                'payment_id': payment.id,
                'account_payment_id': payment.payment_id.id,
                'invoice_id': payment.invoice_id.id,
                'move_id': payment.move_id.id,
                'ref': payment_ref,
            })
        return payment_vals

    @api.multi
    def _get_report_base_filename(self):
        res = super(AccountInvoice, self)._get_report_base_filename()
        if not res:
            self.ensure_one()
            return \
                self.type == 'out_account_collection' \
                and self.state == 'draft' \
                and _('Draft Collection Invoice') \
                or self.type == 'out_account_collection'\
                and self.state in ('open', 'in_payment', 'paid') \
                and _('Invoice Collection - %s') % (self.number) \
                or self.type == 'out_refund_account_collection' \
                and self.state == 'draft' and _('Credit Collection Note') \
                or self.type == 'out_refund_account_collection' \
                and _('Credit Collection Note - %s') % (self.number)
