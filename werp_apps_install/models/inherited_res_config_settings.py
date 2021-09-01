# Copyright 2020-TODAY WSuite Products <wsuite-products@destiny.ws>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    module_hr_contract_completion = fields.Boolean(
        string="Allow Hr Contract Completion")
    module_hr_contract_extended = fields.Boolean(
        string="Allow Hr Contract Extended")
    module_hr_contract_termination_report = fields.Boolean(
        string="Allow Hr Contract Termination Report")
    module_hr_curriculum_vitae = fields.Boolean(
        string="Allow Hr Curriculum Vitae")
    module_hr_employee_extended = fields.Boolean(
        string="Allow Hr Employee Extended")
    module_hr_employee_policy = fields.Boolean(
        string="Allow Hr Employee Policy")
    module_hr_holiday_exclude_special_days = fields.Boolean(
        string="Allow Hr Holiday Exclude Special Days")
    module_hr_novelty = fields.Boolean(
        string="Allow Hr Novelty")
    module_hr_novelty_close = fields.Boolean(
        string="Allow Hr Novelty Close")
    module_hr_novelty_s3 = fields.Boolean(
        string="Allow Hr Novelty S3")
    module_hr_payroll_income_withholding = fields.Boolean(
        string="Allow Hr Payroll Income Withholding")
    module_hr_payroll_interface = fields.Boolean(
        string="Allow Hr Payroll Interface")
    module_hr_payroll_extended = fields.Boolean(
        string="Allow Hr Payroll")
    module_hr_payslip_special_settlement = fields.Boolean(
        string="Allow Hr Payslip Special Settlement")
    module_hr_extended = fields.Boolean(
        string="Allow Hr")
    module_hr_recruitment_extended = fields.Boolean(
        string="Allow Hr Recruitment Extended")
    is_all_payroll_colombian = fields.Boolean('All Payroll Colombian')

    @api.model
    def get_values(self):
        """Get the value."""
        res = super(ResConfigSettings, self).get_values()
        res['is_all_payroll_colombian'] = self.env[
            'ir.config_parameter'].sudo().get_param('is_all_payroll_colombian')
        return res

    @api.model
    def set_values(self):
        """Set the value."""
        self.env['ir.config_parameter'].sudo().set_param(
            'is_all_payroll_colombian', self.is_all_payroll_colombian)
        if self.is_all_payroll_colombian:
            for app in self.env['ir.module.module'].sudo().search([
                    ('name', 'in', (
                        'hr_contract_completion',
                        'hr_contract_extended', 'hr_contract_massive',
                        'hr_contract_report', 'hr_contract_termination_report',
                        'hr_employee_extended', 'hr_employee_flextime',
                        'hr_employee_policy', 'hr_novelty', 'hr_novelty_close',
                        'hr_extended', 'hr_payroll_income_withholding',
                    'hr_payroll_iw_recalc', 'hr_payslip_special_settlement',
                    'l10n_payroll_co', 'hr_payroll_extended')),
                    ('state', '=', 'uninstalled')]):
                app.button_immediate_install()
        super(ResConfigSettings, self).set_values()
