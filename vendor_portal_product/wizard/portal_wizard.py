# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Kunjal Patel <kunjalpatel@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class PortalWizard(models.TransientModel):

    _inherit = 'portal.wizard'

    @api.multi
    def action_apply(self):
        if self.env.context.get('active_model') == 'res.partner':
            partner = \
                self.env['res.partner'].browse(
                    self.env.context.get('active_id'))
            if partner.supplier:
                ctx = dict(
                    self.env.context,
                    vendor_portal=True)
                res = super(PortalWizard,
                            self.with_context(ctx)).action_apply()
                partner.write({'is_vendor_portal': True})
                return res
        res = super(PortalWizard, self).action_apply()
        return res
