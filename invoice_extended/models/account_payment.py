# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api
from odoo.addons.account.models import account_payment as AP


class account_abstract_payment(models.AbstractModel):
    _inherit = "account.abstract.payment"

    @api.model
    def default_get(self, fields):
        AP.MAP_INVOICE_TYPE_PARTNER_TYPE.update({
            'out_account_collection': 'customer',
            'out_refund_account_collection': 'supplier'
        })
        AP.MAP_INVOICE_TYPE_PAYMENT_SIGN.update({
            'out_account_collection': 1,
            'out_refund_account_collection': -1
        })
        res = super(account_abstract_payment, self).default_get(fields)
        if self._context.get('type') == 'out_account_collection':
            res['payment_type'] = 'inbound'
        return res

    @api.onchange('journal_id')
    def _onchange_journal(self):
        res = super(account_abstract_payment, self)._onchange_journal()
        if self._context.get('type') == 'out_account_collection':
            self.payment_type = 'inbound'
        return res
