# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo
import logging
from odoo import http
from odoo import api, models, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class ChangePasswordUser(models.TransientModel):
    _inherit = 'change.password.user'

    @api.multi
    def update_password(self, line, cr):
        cr.execute("SELECT id FROM ir_model WHERE model='base.synchro.server'")
        if cr.fetchone():
            cr.execute('UPDATE base_synchro_server SET password=%s WHERE login=%s', (line.new_passwd, line.user_id.login))

    @api.multi
    def change_password_button(self):
        """ Override this method for change password in all database"""
        current_cr = self._cr
        for line in self:
            if not line.new_passwd:
                raise UserError(_("Before clicking on 'Change Password', you have to write a new password."))
            db_list = odoo.service.db.list_dbs(True)
            _logger.info(" db_list : %s", db_list)
            for db in db_list:
                if not http.db_filter([db]):
                    continue
                _logger.info(" db : %s", db)
                try:
                    if db == current_cr.dbname:
                        self.update_password(line, current_cr)
                        continue
                    new_db = odoo.sql_db.db_connect(db)
                    with new_db.cursor() as cr:
                        cr.execute('SELECT id from res_company where generate_process_in_other_db=True')
                        result = cr.fetchone()
                        _logger.info(" result ==>: %s", result)
                        if not result:
                            continue
                        cr.execute('UPDATE res_users SET password=%s WHERE login=%s', (line.new_passwd, line.user_id.login))
                        self.update_password(line, cr)
                    odoo.sql_db.close_db(db)
                except:
                    raise UserError(_(
                        'There seems a problem in the database:- ' + str(db)))
            line.user_id.write({'password': line.new_passwd})
        # don't keep temporary passwords in the database longer than necessary
        self.write({'new_passwd': False})
