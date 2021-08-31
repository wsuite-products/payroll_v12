# -*- coding: utf-8 -*-

import json
import logging
import threading
from odoo import models, api, _

_logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    @api.multi
    def action_webhook(self):
        webhook_ids = self.env['webhook'].search([
            ('model_id.model', '=', self._name),
            ('trigger', 'in', ['on_write', 'on_create_or_write']),
            ('url_type', '=', 'you')])
        for webhook_id in webhook_ids:
            final_data = {'from': {}, 'to': {}, 'data': [],
                          'webhook_type': 4,
                          'default_data': json.loads(
                              webhook_id.default_json or '{}'),
                          'webhook_history_id': {},
                          'reference': '%s,%s' % (self._name, self.id)
                          }
            final_data['to'].update({
                'employee_id': self.employee_id.id,
                'emp_name': self.employee_id.name,
                'email': self.employee_id.work_email,
                'token': ''})
            if self.employee_id.parent_id:
                final_data['from'].update(
                    {'employee_id': self.employee_id.parent_id.id,
                     'parent_name': self.employee_id.parent_id.name,
                     'email': self.employee_id.parent_id.work_email,
                     'token': ''})
            object_confg = self.env['object.confg'].search([
                ('object_id.model', '=', self._name)], limit=1, order='sequence')
            fields_data = object_confg.get_data(self)
            final_data.update(fields_data)

            webhook_history_id = \
                self.env['webhook.history'].action_webhook_history_create(
                    final_data)
            if webhook_history_id:
                final_data['webhook_history_id'] = webhook_history_id.id
                thread = threading.Thread(
                    target=webhook_id.sent_data,
                    args=(webhook_id.model_name, final_data, self))
                thread.start()
                return True

    @api.multi
    def action_payslip_done(self):
        self.action_webhook()
        return super(HrPayslip, self).action_payslip_done()
