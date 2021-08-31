# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo
from odoo import http
from odoo import api, fields, models, _, registry, SUPERUSER_ID
from odoo.exceptions import ValidationError
import threading
import logging
_logger = logging.getLogger(__name__)
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
from odoo.http import request

not_use_field = [
    'id', 'display_name', 'activity_state', 'activity_date_deadline',
    'activity_summary', 'message_is_follower', 'message_unread',
    'message_unread_counter', 'message_needaction',
    'message_needaction_counter', 'message_has_error',
    'message_has_error_counter', 'message_attachment_count',
    '__last_update', 'create_uid', 'write_uid', 'message_main_attachment_id',
    'profile_image_url', 'message_partner_ids', 'message_channel_ids',
    'create_date', 'write_date']


class HrTransferEmployee(models.Model):
    """Hr Transfer Employee."""

    _name = "hr.transfer.employee"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Hr Transfer Employee"
    _rec_name = "database_origin"

    @api.multi
    def _check_transfer_visibility(self):
        for record in self:
            if record.database == self.env.cr.dbname:
                record.check_transfer = True
            else:
                record.check_transfer = False

    database_origin = fields.Char(default=lambda self: self.env.cr.dbname)
    employee_ids = fields.Many2many(
        'hr.employee', 'hr_employee_hr_transfer_employee_rel',
        'hr_transfer_employee_id', 'hr_employee_id')
    database = fields.Char('Database')
    data = fields.Selection([
        ('all_data', 'All Data'),
        ('final_data', 'Final Data')], default='final_data')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('step1', 'Step 1'),
        ('step2', 'Step 2'),
        ('step3', 'Step 3'),
        ('step4', 'Step 4'),
        ('transfered', 'Transfered'),
        ('cancelled', 'Cancelled')], default='draft')
    check_transfer = fields.Boolean(compute='_check_transfer_visibility', string='Check Transfer?')
    reference = fields.Integer('Reference Id')
    employee_multi_or_single = fields.Selection([
        ('single', 'Single Employee'),
        ('multi', 'Multi Employee')], string="Copy Single Or Multi Employee")
    employee_id = fields.Many2one('hr.employee', 'Employee')

    @api.constrains('database')
    def check_database(self):
        base_url = request.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        if not self.database.startswith(('werp')):
            db_list = http.db_list()
            if base_url == "http://dev-werp.wsuite.com":
                db_name = 'werpdev_' + self.database
                if db_name not in db_list:
                    raise ValidationError(_('\n  Prefix automatically set werpdev_ '
                                        '\n Database (%s) does not exists! '
                                        '\n Please Check Database Name.') % db_name)
            else:
                db_name = 'werp_' + self.database
                if db_name not in db_list:
                    raise ValidationError(_('\n  Prefix automatically set werp_ '
                                        '\n Database (%s) does not exists! '
                                        '\n Please Check Database Name.') % db_name)
            self.database = db_name

    @api.multi
    def action_aprroved(self):
        """Approve operation."""
        for rec in self:
            if rec.database_origin and rec.database_origin not in\
                    odoo.service.db.list_dbs(True):
                raise ValidationError(_(
                    'Please Check Database Name.'))
            # Create Transfer record in destination database.
            db_registry = registry(rec.database)
            with db_registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                other_hr_transfer_employee_obj = env['hr.transfer.employee']
                other_hr_transfer_employee_read_data = self.read(['database_origin', 'data', 'database'])
                other_hr_transfer_employee_read_data[0].update({
                    'state': 'approved',
                    'reference': self.id,
                    'employee_multi_or_single': self.employee_multi_or_single
                })
                other_hr_transfer_employee_obj.create(other_hr_transfer_employee_read_data[0])
            rec.state = 'approved'

    @api.multi
    def get_create_country(self, country_id):
        res_country_obj = self.env['res.country']
        other_country_id = False
        if not country_id:
            return other_country_id
        other_country_id = res_country_obj.search(['|', ('name', '=', country_id.name), ('code', '=', country_id.code)], limit=1)
        country_data_read = country_id.read(['address_format', 'address_view_id', 'code', 'enforce_cities', 'name', 'name_position', 'phone_code', 'vat_label'])
        if not other_country_id:
            other_country_id = res_country_obj.create(country_data_read[0])
        # else:
        #     other_country_id.write(country_data_read[0])
        return other_country_id

    @api.multi
    def get_create_state(self, state_id):
        other_state_id = False
        if not state_id:
            return False
        res_state_obj = self.env['res.country.state']
        other_state_id = res_state_obj.search([('name', '=', state_id.name)], limit=1)

        state_data_read = state_id.read(['code', 'display_name', 'name'])
        country_id = self.get_create_country(state_id.country_id)
        state_data_read[0].update({'country_id': country_id and country_id.id})

        if not other_state_id:
            other_state_id = res_state_obj.create(state_data_read[0])
        # else:
        #     other_state_id.write(state_data_read[0])
        return other_state_id

    @api.multi
    def get_create_res_partner_title_id(self, res_partner_title_id):
        other_res_partner_title_id = False
        if not res_partner_title_id:
            return False
        res_partner_title_id_obj = self.env['res.partner.title']
        other_res_partner_title_id = res_partner_title_id_obj.search([('name', '=', res_partner_title_id.name)], limit=1)
        res_partner_title_id_data_read = res_partner_title_id.read(['shortcut', 'name'])
        if not other_res_partner_title_id:
            other_res_partner_title_id = res_partner_title_id_obj.create(res_partner_title_id_data_read[0])
        else:
            other_res_partner_title_id.write(res_partner_title_id_data_read[0])
        return other_res_partner_title_id

    @api.multi
    def get_create_partner(self, partner_id):
        new_partner_id = self.get_create_partner_all(partner_id)
        if partner_id.parent_id:
            res_partner_obj = self.env['res.partner']
            parent_partner_id = partner_id.parent_id
            old_parent_partner_id = new_partner_id
            while parent_partner_id:
                new_parent_partner_id = res_partner_obj.search([('vat', '=', parent_partner_id.vat)], limit=1)
                if not new_parent_partner_id:
                    new_parent_partner_id = self.get_create_partner_all(new_parent_partner_id)
                parent_partner_id = parent_partner_id.parent_id or False
                old_parent_partner_id.write({
                    'parent_id': new_parent_partner_id.id,
                    })
                old_parent_partner_id = new_parent_partner_id
        return new_partner_id

    @api.multi
    def get_create_partner_all(self, partner_id):
        other_partner_id = False
        if not partner_id:
            return other_partner_id
        res_partner_obj = self.env['res.partner']

        if partner_id.vat:
            other_partner_id = res_partner_obj.search([('vat', '=', partner_id.vat)], limit=1)

        if not other_partner_id:
            partner_normal_fields = ['active', 'additional_info', 'agency', 'agency_type', 'barcode',
            'calendar_last_notif_ack', 'card_brand', 'card_last_four', 'city', 'client_reference', 'color', 'comment',
            'commercial_company_name', 'company', 'company_name', 'credit_limit', 'customer', 'customer_admin',
            'date', 'db_wp_id', 'debit_limit', 'display_name', 'email', 'employee', 'file_cv_name', 'file_cv_size',
            'first_name', 'function', 'gender', 'invoice_warn', 'invoice_warn_msg', 'is_afc', 'is_afp',
            'is_arl', 'is_company', 'is_compensation_box', 'is_eps', 'is_found_layoffs', 'is_prepaid_medicine',
            'is_unemployee_fund', 'is_vendor_portal', 'is_voluntary_contribution', 'l10n_co_document_type',
            'last_time_entries_checked', 'link', 'message_bounce', 'mobile', 'mobile_country_code',
            'name', 'neighborhood', 'partner_gid', 'partner_share', 'phone', 'phone_country_code', 'picking_warn',
            'picking_warn_msg', 'postulant', 'purchase_warn', 'purchase_warn_msg', 'ref', 'sale_warn', 'sale_warn_msg',
            'second_name', 'second_surname', 'signup_expiration', 'signup_token', 'signup_type', 'slug', 'sort_name',
            'state_selection', 'street', 'street2', 'stripe_id', 'stripe_token', 'supplier', 'surname', 'transaction_id',
            'trial_ends_at', 'type', 'tz', 'vat', 'zip']

            other_partner_data_read = partner_id.read(partner_normal_fields)

            state_id = self.get_create_state(partner_id.state_id)
            country_id = self.get_create_country(partner_id.country_id)
            city_id = self.get_create_place(partner_id.city_id)
            currency_id = self.env['res.currency'].search([('name', '=', partner_id.currency_id.name)], limit=1)
            function_id = self.get_create_hr_job(partner_id.function_id)
            title = self.get_create_res_partner_title_id(partner_id.title)

            other_partner_data_read[0].update({
                'state_id': state_id and state_id.id,
                'country_id': country_id and country_id.id,
                'city_id': city_id and city_id.id,
                'currency_id': currency_id and currency_id.id,
                'function_id': function_id and function_id.id,
                'title': title and title.id,
                })
            other_partner_id = res_partner_obj.create(other_partner_data_read[0])
        return other_partner_id

    @api.multi
    def get_create_macro_area(self, macro_area_id):
        other_macro_area_id = False
        if not macro_area_id:
            return other_macro_area_id
        other_macro_area_obj = self.env['macro.area']
        other_macro_area_id = other_macro_area_obj.search([('name', '=', macro_area_id.name)], limit=1)
        macro_area_data_read = macro_area_id.read(['description', 'name'])
        if not other_macro_area_id:
            other_macro_area_id = other_macro_area_obj.create(macro_area_data_read[0])
        else:
            other_macro_area_id.write(macro_area_data_read[0])
        return other_macro_area_id

    @api.multi
    def get_create_hr_job(self, resource_id):
        other_resource_id = False
        if not resource_id:
            return other_resource_id
        other_hr_reason_changed_obj = self.env['hr.reason.changed']
        other_jca_details_obj = self.env['jca.details']
        other_hr_job_obj = self.env['hr.job']

        other_resource_id = other_hr_job_obj.search([('name', '=', resource_id.name)], limit=1)
        if other_resource_id:
            return other_resource_id
        other_resource_data_read = resource_id.read(['codigo_holding', 'codigo_holding_principal', 'color', 'description',
            'experience', 'fte', 'holding', 'holding_principal', 'hour_value', 'jca_details_type',
            'level', 'name', 'observation', 'requirements', 'salary', 'state'])

        other_hr_reason_changed_id = False
        other_jca_details_id = False

        other_department_id = self.get_create_hr_department(resource_id.department_id)
        other_function_executed_id = self.get_create_function_executes(resource_id.function_executed_id)
        other_recruitment_reason_id = self.get_create_recruitment_reason_id(resource_id.recruitment_reason_id)
        other_work_group_id = self.get_create_work_group(resource_id.work_group_id)
        other_hr_responsible_id = self.get_create_res_users(resource_id.hr_responsible_id)
        other_macro_area_id = self.get_create_macro_area(resource_id.macro_area_id)
        other_group_id = self.get_create_res_groups(resource_id.group_id)
        other_manager_id = self.get_create_employee(resource_id.manager_id)
        other_user_id = self.get_create_res_users(resource_id.user_id)

        if resource_id.hr_reason_changed_id:
           other_hr_reason_changed_id = other_hr_reason_changed_obj.search([('name', '=', resource_id.hr_reason_changed_id.name)], limit=1)
        if resource_id.jca_details_id:
           other_jca_details_id = other_jca_details_obj.search([('name', '=', resource_id.jca_details_id.name)], limit=1)

        other_resource_data_read[0].update({
            'department_id': other_department_id and other_department_id.id,
            'function_executed_id': other_function_executed_id and other_function_executed_id.id,
            'group_id': other_group_id and other_group_id.id,
            'hr_reason_changed_id': other_hr_reason_changed_id and other_hr_reason_changed_id.id,
            'hr_responsible_id': other_hr_responsible_id and other_hr_responsible_id.id,
            'jca_details_id': other_jca_details_id and other_jca_details_id.id,
            'macro_area_id': other_macro_area_id and other_macro_area_id.id,
            'manager_id': other_manager_id and other_manager_id.id,
            'recruitment_reason_id': other_recruitment_reason_id and other_recruitment_reason_id.id,
            'work_group_id': other_work_group_id and other_work_group_id.id,
            'user_id': other_user_id and other_user_id.id
        })
        other_resource_id = other_hr_job_obj.create(other_resource_data_read[0])
        # else:
        #     other_resource_id.write(other_resource_data_read[0])
        return other_resource_id

    @api.multi
    def get_create_payroll_structure_type(self, type_id):
        hr_payroll_structure_type_obj = self.env['hr.payroll.structure.type']
        other_type_id = False
        if not type_id:
            return other_type_id
        other_type_id = hr_payroll_structure_type_obj.search([('name', '=', type_id.name)], limit=1)
        if not other_type_id:
            other_type_id = hr_payroll_structure_type_obj.create({
                'name': type_id.name,
                'description': type_id.description
                })
        else:
            other_type_id.write({
                'name': type_id.name,
                'description': type_id.description
                })
        return other_type_id

    @api.multi
    def get_create_salary_rule_category(self, category_id):
        hr_salary_rule_category_obj = self.env['hr.salary.rule.category']
        other_category_id = False
        if not category_id:
            return other_category_id
        other_category_id = hr_salary_rule_category_obj.search([('name', '=', category_id.name), ('code', '=', category_id.code)], limit=1)
        if other_category_id:
            return other_category_id
        vals = {
            'name': category_id.name,
            'note': category_id.note,
            'code': category_id.code,
            'active': category_id.active
        }
        if not other_category_id:
            other_category_id = hr_salary_rule_category_obj.create(vals)
        # else:
        #     other_category_id.write(vals)
        return other_category_id

    @api.multi
    def get_create_hr_contribution_register(self, register_id):
        other_register_id = False
        if not register_id:
            return other_register_id
        hr_contribution_register_obj = self.env['hr.contribution.register']
        other_register_id = hr_contribution_register_obj.search([('name', '=', register_id.name)], limit=1)
        register_partner_id = self.get_create_partner(register_id.partner_id)
        vals = {
            'name': register_id.name,
            'note': register_id.note,
            'partner_id': register_partner_id and register_partner_id,
        }
        if not other_register_id:
            other_register_id = hr_contribution_register_obj.create(vals)
        else:
            other_register_id.write(vals)
        return other_register_id

    @api.multi
    def get_create_salary_rule(self, salary_rule_id, check=True):
        other_salary_rule_id = False
        if not salary_rule_id:
            return other_salary_rule_id
        hr_salary_rule_obj = self.env['hr.salary.rule']
        domain = [('name', '=', salary_rule_id.name), ('code', '=', salary_rule_id.code)]
        # if salary_rule_id.category_id:
        #     domain += [('category_id.name', '=', salary_rule_id.category_id.name)]
        other_salary_rule_id = hr_salary_rule_obj.search(domain, limit=1)
        if other_salary_rule_id and not check:
            return other_salary_rule_id
        other_salary_rule_data_read = salary_rule_id.read(['accumulate', 'active', 'amount_fix', 'amount_percentage',
            'amount_percentage_base', 'amount_python_compute', 'amount_select', 'appears_on_payslip', 'asigned_base',
            'calculate_base', 'code', 'code_sara', 'condition_python', 'condition_range', 'condition_range_max',
            'condition_range_min', 'condition_select', 'fixed', 'id', 'is_flex', 'name', 'note', 'print_payslip',
            'projection_exempt', 'quantity', 'sequence', 'total_cost', 'value', 'work_days_value', 'autocomplete_flex'])
        if other_salary_rule_data_read[0].get('autocomplete_flex', False):
            other_salary_rule_id = hr_salary_rule_obj.search([('autocomplete_flex', '=', True)], limit=1)
            if other_salary_rule_id:
                return other_salary_rule_id
        prepaid_medicine_id = self.get_create_partner(salary_rule_id.prepaid_medicine_id)
        register_id = self.get_create_hr_contribution_register(salary_rule_id.register_id)
        category_id = self.get_create_salary_rule_category(salary_rule_id.category_id)
        other_salary_rule_data_read[0].update({
            'prepaid_medicine_id': prepaid_medicine_id and prepaid_medicine_id.id,
            'register_id': register_id and register_id.id,
            'category_id': category_id and category_id.id,
            })
        if not other_salary_rule_id:
            other_salary_rule_id = hr_salary_rule_obj.create(other_salary_rule_data_read[0])
        else:
            other_salary_rule_id.write(other_salary_rule_data_read[0])
        # Parent Salary Rule Category
        if salary_rule_id.category_id:
            parent_category_id = salary_rule_id.category_id
            old_parent_category_id = other_salary_rule_id
            while parent_category_id:
                new_parent_category_id = self.get_create_salary_rule_category(parent_category_id)
                # new_parent_category_id = get_create_salary_rule_category hr_salary_rule_category_obj.search([('name', '=', parent_category_id.name), ('code', '=', parent_category_id.code)], limit=1)
                # if not new_parent_category_id:
                #     category_read_data = parent_category_id.read(['code', 'name', 'note', 'active'])
                #     category_id = False
                #     if parent_category_id.category_id:
                #         category_id = self.get_create_salary_rule_category(parent_category_id.category_id)
                #     category_read_data[0].update({'category_id': category_id and category_id.id})
                #     new_parent_category_id = hr_salary_rule_category_obj.create(category_read_data[0])

                parent_category_id = parent_category_id.parent_id or False
                old_parent_category_id.write({
                    'category_id': new_parent_category_id.id,
                    })
                old_parent_category_id = new_parent_category_id
        return other_salary_rule_id

    @api.multi
    def get_create_hr_department(self, department_id):
        other_department_id = False
        if not department_id:
            return other_department_id
        hr_department_obj = self.env['hr.department']
        other_department_id = hr_department_obj.search([('name', '=', department_id.name)], limit=1)
        hr_department_data_read = department_id.read(['active', 'color', 'complete_name', 'name', 'note'])
        if not other_department_id:
            other_department_id = hr_department_obj.create(hr_department_data_read[0])
        else:
            other_department_id.write(hr_department_data_read[0])

        if department_id.parent_id:
            parent_department_id = department_id.parent_id
            old_parent_department_id = other_department_id
            while parent_department_id:
                new_parent_department_id = hr_department_obj.search([('name', '=', parent_department_id.name)], limit=1)
                category_read_data = parent_department_id.read(['active', 'color', 'complete_name', 'name', 'note'])

                if not new_parent_department_id:
                    new_parent_department_id = hr_department_obj.create(category_read_data[0])
                else:
                    new_parent_department_id.write(category_read_data[0])

                parent_department_id = parent_department_id.parent_id or False
                old_parent_department_id.write({
                    'parent_id': new_parent_department_id.id,
                    })
                old_parent_department_id = new_parent_department_id
        return other_department_id

    @api.multi
    def get_create_work_group(self, work_group_id):
        other_work_group_id = False
        if not work_group_id:
            return other_work_group_id
        work_group_obj = self.env['work.group']
        other_work_group_id = work_group_obj.search([('name', '=', work_group_id.name)], limit=1)
        work_group_data_read = work_group_id.read(['description', 'name'])
        if not other_work_group_id:
            other_work_group_id = work_group_obj.create(work_group_data_read[0])
        else:
            other_work_group_id.write(work_group_data_read[0])
        return other_work_group_id

    @api.multi
    def hr_contract_completion_withdrawal_reason_id(self, reason_id):
        other_reason_id = False
        if not reason_id:
            return other_reason_id
        hr_contract_completion_withdrawal_reason_obj = self.env['hr.contract.completion.withdrawal_reason']
        other_reason_id = hr_contract_completion_withdrawal_reason_obj.search([('name', '=', reason_id.name)], limit=1)
        reason_id_data_read = reason_id.read(['description', 'name'])
        if not other_reason_id:
            other_reason_id = hr_contract_completion_withdrawal_reason_obj.create(reason_id_data_read[0])
        else:
            other_reason_id.write(reason_id_data_read[0])
        return other_reason_id

    @api.multi
    def get_create_recruitment_reason_id(self, recruitment_reason_id):
        other_recruitment_reason_id = False
        if not recruitment_reason_id:
            return other_recruitment_reason_id
        recruitment_reason_obj = self.env['recruitment.reason']
        other_recruitment_reason_id = recruitment_reason_obj.search([('name', '=', recruitment_reason_id.name)], limit=1)
        recruitment_reason_data_read = recruitment_reason_id.read(['description', 'name', 'abbreviation'])
        if not other_recruitment_reason_id:
            other_recruitment_reason_id = recruitment_reason_obj.create(recruitment_reason_data_read[0])
        else:
            other_recruitment_reason_id.write(recruitment_reason_data_read[0])

    @api.multi
    def get_create_hr_payroll_structure(self, old_struct_id, check_first_time):
        _logger.info("==old_struct_id==%s, %s, %s", old_struct_id, old_struct_id.name, old_struct_id.code)
        struct_id = False
        if not old_struct_id:
            return struct_id
        hr_payroll_structure_obj = self.env['hr.payroll.structure']
        struct_id = hr_payroll_structure_obj.search([('name', '=', old_struct_id.name), ('code', '=', old_struct_id.code)], limit=1)
        if not check_first_time:
            return struct_id

        struct_data_read = old_struct_id.read(['code', 'name', 'note'])
        payroll_structure_type_id = self.get_create_payroll_structure_type(old_struct_id.type_id)
        rules_ids_list = []
        for rule_id in old_struct_id.rule_ids:
            new_rule_id = self.get_create_salary_rule(rule_id, True)
            if new_rule_id:
                rules_ids_list.append(new_rule_id.id)

        struct_data_read[0].update({
            'type_id': payroll_structure_type_id and payroll_structure_type_id.id,
            'parent_id': False,
            'rule_ids': [(6, 0, rules_ids_list)],
            })

        if not struct_id:
            struct_id = hr_payroll_structure_obj.create(struct_data_read[0])
        else:
            struct_id.write(struct_data_read[0])

        if old_struct_id.parent_id:
            parent_struct_id = old_struct_id.parent_id
            old_parent_struct_id = struct_id
            while parent_struct_id:
                new_parent_struct_id = hr_payroll_structure_obj.search([('name', '=', parent_struct_id.name), ('code', '=', parent_struct_id.code)], limit=1)
                category_read_data = parent_struct_id.read(['code', 'name', 'note'])
                parent_type_id = False
                if parent_struct_id.type_id:
                    parent_type_id = self.get_create_payroll_structure_type(parent_struct_id.type_id)

                rules_ids_list = []
                for rule_id in parent_struct_id.rule_ids:
                    new_rule_id = self.get_create_salary_rule(rule_id)
                    if new_rule_id:
                        rules_ids_list.append(new_rule_id.id)

                struct_data_read[0].update({
                    'type_id': parent_type_id and parent_type_id.id,
                    'parent_id': False,
                    'rule_ids': [(6, 0, rules_ids_list)],
                    })

                if not new_parent_struct_id:
                    new_parent_struct_id = hr_payroll_structure_obj.create(category_read_data[0])
                else:
                    new_parent_struct_id.write(category_read_data[0])

                parent_struct_id = parent_struct_id.parent_id or False
                old_parent_struct_id.write({
                    'parent_id': new_parent_struct_id.id,
                    })
                old_parent_struct_id = new_parent_struct_id
        return struct_id

    @api.multi
    def get_create_contract_id(self, employee_id, contract_id):
        other_contract_id = False
        if not contract_id:
            return other_contract_id
        hr_contract_obj = self.env['hr.contract']
        domain = [
            ('name', '=', contract_id.name),
            ('state', '=', contract_id.state),
            ('date_start', '=', contract_id.date_start),
            ('wage', '=', contract_id.wage),
            ('active', 'in', [True, False])]
        other_contract_id = hr_contract_obj.search(domain, limit=1)
        if other_contract_id:
            return other_contract_id

        normal_fields = ['active', 'advantages', 'arl_percentage', 'compare_amount',
        'contribution_pay', 'create_date', 'datas_fname', 'date_end', 'date_start',
        'exclude_from_seniority', 'fix_wage_amount', 'fix_wage_perc', 'flex_wage_amount',
        'flex_wage_perc', 'id', 'identification_id', 'integral_salary', 'name', 'notes',
        'reported_to_secretariat', 'ret_fue_2', 'schedule_pay', 'state', 'subcontract',
        'total_perc', 'trial_date_end', 'wage', 'write_date']
        other_contract_data_read = contract_id.read(normal_fields)
        department_id = currency_id = center_formation_id = agency_id = False
        institution_id = hr_contract_completion_withdrawal_reason_id = False
        type_id = recruitment_reason_id = reason_change_id = job_id = False
        if contract_id.agency_id:
            agency_id = self.get_create_partner(employee_id.afc_id)

        hr_center_formation_obj = self.env['hr.center.formation']
        res_currency_obj = self.env['res.currency']
        hr_leaves_generate_obj = self.env['hr.leaves.generate']
        hr_contract_reason_change_obj = self.env['hr.contract.reason.change']
        hr_contract_type_obj = self.env['hr.contract.type']
        hr_contract_flex_wage = self.env['ir.model'].search([('model', '=', 'hr.contract.flex_wage')])
        if not hr_contract_flex_wage:
            module_id = self.env['ir.module.module'].search([('name', '=', 'hr_employee_flextime')])
            module_id.button_immediate_install()
        flex_wage_obj = self.env['hr.contract.flex_wage']

        if contract_id.center_formation_id:
            center_formation_id = hr_center_formation_obj.search([('name', '=', contract_id.center_formation_id.name)], limit=1)
            center_formation_data_read = contract_id.center_formation_id.read(['description', 'name'])
            if not center_formation_id:
                center_formation_id = hr_center_formation_obj.create(center_formation_data_read[0])
            else:
                center_formation_id.write(center_formation_data_read[0])

        currency_id = res_currency_obj.search([('name', '=', contract_id.currency_id.name)], limit=1)
        department_id = self.get_create_hr_department(contract_id.department_id)
        hr_contract_completion_withdrawal_reason_id = self.hr_contract_completion_withdrawal_reason_id(contract_id.hr_contract_completion_withdrawal_reason_id)
        institution_id = self.get_create_hr_academic_institution(contract_id.institution_id)
        job_id = self.get_create_hr_job(contract_id.job_id)
        recruitment_reason_id = self.get_create_recruitment_reason_id(contract_id.recruitment_reason_id)
        struct_id = self.get_create_hr_payroll_structure(contract_id.struct_id, False)

        if contract_id.reason_change_id:
            reason_change_id = hr_contract_reason_change_obj.search([('name', '=', contract_id.reason_change_id.name)], limit=1)
            hr_contract_reason_change_data_read = contract_id.reason_change_id.read(['description', 'name'])
            if not reason_change_id:
                reason_change_id = hr_contract_reason_change_obj.create(hr_contract_reason_change_data_read[0])
            else:
                reason_change_id.write(hr_contract_reason_change_data_read[0])

        if contract_id.type_id:
            type_id = hr_contract_type_obj.search([('name', '=', contract_id.type_id.name)], limit=1)
            contract_type_data_read = contract_id.type_id.read(['date_end_required', 'name'])
            if not type_id:
                type_id = hr_contract_type_obj.create(contract_type_data_read[0])
            else:
                type_id.write(contract_type_data_read[0])

        flex_wage_ids = []
        for flex_wage_id in contract_id.flex_wage_ids:
            salary_rule_id = self.get_create_salary_rule(flex_wage_id.salary_rule_id, False)
            flex_wage_ids.append((0, 0, {
                'salary_rule_id': salary_rule_id and salary_rule_id.id,
                'fixed': flex_wage_id.fixed,
                'amount': flex_wage_id.amount,
                'percentage': flex_wage_id.percentage,
            }))

        other_contract_data_read[0].update({
            'agency_id': agency_id and agency_id.id,
            'center_formation_id': center_formation_id and center_formation_id.id,
            'currency_id': currency_id and currency_id.id,
            'department_id': department_id and department_id.id,
            'employee_id': employee_id and employee_id.id,
            'hr_contract_completion_withdrawal_reason_id': hr_contract_completion_withdrawal_reason_id and hr_contract_completion_withdrawal_reason_id.id,
            'institution_id': institution_id and institution_id.id,
            'job_id': job_id and job_id.id,
            'reason_change_id': reason_change_id and reason_change_id.id,
            'recruitment_reason_id': recruitment_reason_id and recruitment_reason_id.id,
            'type_id': type_id and type_id.id,
            'struct_id': struct_id and struct_id.id,
            'flex_wage_ids': flex_wage_ids,
            })

        other_contract_id = hr_contract_obj.create(other_contract_data_read[0])
        return other_contract_id

    @api.multi
    def get_create_bank(self, bank_id):
        other_bank_id = False
        if not bank_id:
            return other_bank_id
        res_bank_obj = self.env['res.bank']
        other_bank_id = res_bank_obj.search([('name', '=', bank_id.name)], limit=1)
        other_bank_data_read = bank_id.read(['name', 'bic', 'email', 'phone', 'active', 'street', 'street2', 'city', 'zip'])
        state_id = self.get_create_state(bank_id.state)
        country_id = self.get_create_country(bank_id.country)
        other_bank_data_read[0].update({
            'state': state_id and state_id.id,
            'country': country_id and country_id.id,
            })
        if not other_bank_id:
            other_bank_id = res_bank_obj.create(other_bank_data_read[0])
        else:
            other_bank_id.write(other_bank_data_read[0])
        return other_bank_id

    @api.multi
    def get_create_place(self, city_id):
        other_city_id = False
        if not city_id:
            return other_city_id

        res_city_obj = self.env['res.city']
        other_city_id = res_city_obj.search([('name', '=', city_id.name)], limit=1)

        other_city_data_read = city_id.read(['name', 'zipcode', 'display_name'])
        state_id = self.get_create_state(city_id.state_id)
        country_id = self.get_create_country(city_id.country_id)

        other_city_data_read[0].update({
            'state_id': state_id and state_id.id,
            'country_id': country_id and country_id.id,
            })
        if not other_city_id:
            other_city_id = res_city_obj.create(other_city_data_read[0])
        else:
            other_city_id.write(other_city_data_read[0])
        return other_city_id

    @api.multi
    def get_create_hr_employee_flextime(self, flex_id):
        other_flex_id = False
        if not flex_id:
            return other_flex_id
        hr_employee_flextime_obj = self.env['hr.employee.flextime']
        other_flex_id = hr_employee_flextime_obj.search([('name', '=', flex_id.name)], limit=1)
        other_employee_flextime_data_read = flex_id.read(['name', 'description', 'hour_end', 'hour_start', 'hour_end_type', 'hour_start_type'])
        if not other_flex_id:
            other_flex_id = hr_employee_flextime_obj.create(other_employee_flextime_data_read[0])
        else:
            other_flex_id.write(other_employee_flextime_data_read[0])
        return other_flex_id


    @api.multi
    def get_create_resource_calender_attendance(self, resource_calendar_attendance_id, calendar_id):
        other_resource_calendar_attendance_id = False
        if not resource_calendar_attendance_id:
            return other_resource_calendar_attendance_id
        resource_calendar_attendance_obj = self.env['resource.calendar.attendance']
        other_resource_calendar_attendance_id = resource_calendar_attendance_obj.search([('name', '=', resource_calendar_attendance_id.name)], limit=1)
        other_resource_calender_read = resource_calendar_attendance_id.read(['date_from', 'date_to', 'day_period', 'dayofweek', 'hour_from', 'hour_to', 'name'])
        other_resource_calender_read[0].update({'calendar_id': calendar_id and calendar_id.id})
        if not other_resource_calendar_attendance_id:
            other_resource_calendar_attendance_id = resource_calendar_attendance_obj.create(other_resource_calender_read[0])
        else:
            other_resource_calendar_attendance_id.write(other_resource_calender_read[0])
        return other_resource_calendar_attendance_id

    @api.multi
    def get_create_calendar_event_type(self, type_id):
        other_type_id = False
        if not type_id:
            return other_type_id
        calendar_event_type_obj = self.env['calendar.event.type']
        other_type_id = calendar_event_type_obj.search([('name', '=', type_id.name)], limit=1)
        if not other_type_id:
            other_type_id = calendar_event_type_obj.create({'name': type_id.name})
        else:
            other_type_id.write({'name': type_id.name})
        return other_type_id

    @api.multi
    def get_create_leave_type(self, leave_type_id):
        other_leave_type_id = False
        if not leave_type_id:
            return other_leave_type_id
        hr_leave_type_obj = self.env['hr.leave.type']
        other_leave_type_id = hr_leave_type_obj.search([('name', '=', leave_type_id.name)], limit=1)
        other_hr_leave_type_data_read = leave_type_id.read([
            'active', 'allocation_type', 'autocalculate_leave', 'color_name', 'exclude_calculate_payslip',
            'is_sumar_en_nomina', 'name', 'no_count_in_payroll', 'no_count_rent', 'request_unit', 'sequence',
            'time_type', 'unpaid', 'vacation_pay_31', 'validation_type', 'validity_start', 'validity_stop'])

        categ_id = self.get_create_calendar_event_type(leave_type_id.categ_id)

        other_hr_leave_type_data_read[0].update({
            'categ_id': categ_id and categ_id.id,
            })
        if not other_leave_type_id:
            other_leave_type_id = hr_leave_type_obj.create(other_hr_leave_type_data_read[0])
        else:
            other_leave_type_id.write(other_hr_leave_type_data_read[0])
        if other_leave_type_id.validity_start:
            other_leave_type_id.write({'validity_start': other_leave_type_id.validity_start - relativedelta(years=2)})
        if other_leave_type_id.validity_stop:
            other_leave_type_id.write({'validity_stop': other_leave_type_id.validity_stop + relativedelta(years=2)})
        return other_leave_type_id

    @api.multi
    def get_create_calendar_alarm(self, alarm_id):
        other_alarm_id = False
        if not alarm_id:
            return other_alarm_id
        calendar_alarm_obj = self.env['calendar.alarm']
        other_alarm_id = calendar_alarm_obj.search([('name', '=', alarm_id.name)], limit=1)
        other_alarm_data_read = alarm_id.read(['name', 'duration', 'duration_minutes', 'interval', 'type'])
        if not other_alarm_id:
            other_alarm_id = calendar_alarm_obj.create(other_alarm_data_read[0])
        else:
            other_alarm_id.write(other_alarm_data_read[0])
        return other_alarm_id

    @api.multi
    def get_create_calendar_event(self, meeting_id):
        other_meeting_id = False
        if not meeting_id:
            return other_meeting_id
        calendar_event_obj = self.env['calendar.event']
        other_meeting_id = calendar_event_obj.search([('name', '=', meeting_id.name)], limit=1)
        other_meeting_data_read = meeting_id.read(['active', 'allday', 'byday', 'count', 'day',
            'description', 'display_start', 'duration', 'end_type', 'final_date', 'fr', 'interval', 'location',
            'mo', 'month_by', 'name', 'privacy', 'recurrency', 'recurrent_id', 'recurrent_id_date', 'res_id',
            'res_model', 'rrule', 'rrule_type', 'sa', 'show_as', 'start', 'start_date', 'start_datetime',
            'state', 'stop', 'stop_date', 'stop_datetime', 'su', 'th', 'tu', 'we', 'week_list'])

        alarm_ids_list = []
        for alarm_id in meeting_id.alarm_ids:
            new_alarm_id = self.get_create_calendar_alarm(alarm_id)
            alarm_ids_list.append(new_alarm_id.id)

        categ_ids_list = []
        for categ_id in meeting_id.categ_ids:
            new_categ_id = self.get_create_calendar_event_type(categ_id)
            categ_ids_list.append(categ_id.id)

        partner_ids_list = []
        for partner_id in meeting_id.partner_ids:
            new_partner_id = self.get_create_partner(partner_id)
            partner_ids_list.append(new_partner_id.id)

        partner_id = self.get_create_partner(meeting_id.partner_id)
        res_model_id = self.env['ir.model'].search([('name', '=', meeting_id.res_model_id.name)], limit=1)
        user_id = self.get_create_res_users(meeting_id.user_id)

        other_meeting_data_read[0].update({
            'alarm_ids': [(6, 0, alarm_ids_list)],
            'categ_ids': [(6, 0, categ_ids_list)],
            'partner_ids': [(6, 0, partner_ids_list)],
            'partner_id': partner_id and partner_id.id,
            'res_model_id': res_model_id and res_model_id.id,
            'user_id': user_id and user_id.id,
            })
        if not other_meeting_id:
            other_meeting_id = calendar_event_obj.create(other_meeting_data_read[0])
        else:
            other_meeting_id.write(other_meeting_data_read[0])
        return other_meeting_id

    @api.multi
    def get_create_hr_leave(self, leave_id):
        other_leave_id = False
        if not leave_id:
            return other_leave_id
        hr_leave_obj = self.env['hr.leave']

        domain = [
            ('name', '=', leave_id.name),
            ('number_of_days', '=', leave_id.number_of_days),
            ('holiday_type', '=', leave_id.holiday_type),
        ]
        if leave_id.date_from:
            domain += [('date_from', '=', leave_id.date_from)]
        if leave_id.date_to:
            domain += [('date_to', '=', leave_id.date_to)]
        if leave_id.employee_id:
            domain += [('employee_id.name', '=', leave_id.employee_id.name)]
        if leave_id.holiday_status_id:
            domain += [('holiday_status_id.name', '=', leave_id.holiday_status_id.name)]
        if leave_id.department_id:
            domain += [('department_id.name', '=', leave_id.department_id.name)]

        other_leave_id = hr_leave_obj.search(domain, limit=1)
        if not other_leave_id:
            other_hr_leave_data_read = leave_id.read(['date_from', 'date_to', 'holiday_type',
                'is_arl', 'is_eps', 'name', 'notes', 'novelty_ref', 'number_of_days', 'payslip_status', 'report_note',
                'request_date_from', 'request_date_from_period', 'request_date_to', 'request_hour_from', 'request_hour_to',
                'request_unit_custom', 'request_unit_half', 'request_unit_hours', 'state'])

            department_id = self.get_create_hr_department(leave_id.department_id)
            employee_id = self.get_create_employee(leave_id.employee_id)
            first_approver_id = self.get_create_employee(leave_id.first_approver_id)
            holiday_status_id = self.get_create_leave_type(leave_id.holiday_status_id)
            manager_id = self.get_create_employee(leave_id.manager_id)
            second_approver_id = self.get_create_employee(leave_id.second_approver_id)
            # meeting_id = self.get_create_calendar_event(leave_id.meeting_id)
            other_hr_leave_data_read[0].update({
                'department_id': department_id and department_id.id,
                'employee_id': employee_id and employee_id.id,
                'first_approver_id': first_approver_id and first_approver_id.id,
                'holiday_status_id': holiday_status_id and holiday_status_id.id,
                'manager_id': manager_id and manager_id.id,
                'second_approver_id': second_approver_id and second_approver_id.id,
                # 'meeting_id': meeting_id and meeting_id.id,
            })
            other_leave_id = hr_leave_obj.create(other_hr_leave_data_read[0])
        # else:
        #     other_leave_id.write(other_hr_leave_data_read[0])
        return other_leave_id


    @api.multi
    def get_create_hr_leave_allocation(self, leave_allocation_id):
        other_leave_allocation_id = self.get_create_hr_leave_allocation_all(leave_allocation_id)
        # if leave_allocation_id.parent_id:
        #     O2M_parent_id = False
        #     leave_allocation_parent_id = leave_allocation_id.parent_id
        #     old_leave_allocation_id = other_leave_allocation_id
        #     while leave_allocation_parent_id:
        #         new_leave_allocation_id = self.get_create_hr_leave_allocation_all(leave_allocation_parent_id)
        #         leave_allocation_parent_id = leave_allocation_parent_id.parent_id or False
        #         old_leave_allocation_id.write({
        #             'parent_id': new_leave_allocation_id.id,
        #             })
        #         old_leave_allocation_id = new_leave_allocation_id
        #         for linked_request_id in leave_allocation_id.linked_request_ids:
        #             self.get_create_hr_leave_allocation_all(new_leave_allocation_id)
        return other_leave_allocation_id

    @api.multi
    def get_create_hr_leave_allocation_all(self, leave_allocation_id):
        other_leave_allocation_id = False
        if not leave_allocation_id:
            return other_leave_allocation_id
        leave_allocation_id_obj = self.env['hr.leave.allocation']

        domain = [('name', '=', leave_allocation_id.name), ('number_of_days', '=', leave_allocation_id.number_of_days), ('holiday_type', '=', leave_allocation_id.holiday_type)]
        if leave_allocation_id.employee_id:
            domain += [('employee_id.name', '=', leave_allocation_id.employee_id.name)]
        if leave_allocation_id.holiday_status_id:
            domain += [('holiday_status_id.name', '=', leave_allocation_id.holiday_status_id.name)]
        other_leave_allocation_id = leave_allocation_id_obj.search(domain, limit=1)
        if not other_leave_allocation_id:
    
            other_leave_allocation_id_data_read = leave_allocation_id.read(['accrual', 'accrual_limit', 'date_from', 'date_to',
                'holiday_type', 'interval_number', 'interval_unit', 'name', 'nextcall', 'notes',
                'number_of_days', 'number_per_interval', 'state', 'unit_per_interval'])

            department_id = self.get_create_hr_department(leave_allocation_id.department_id)
            employee_id = self.get_create_employee(leave_allocation_id.employee_id)
            first_approver_id = self.get_create_employee(leave_allocation_id.first_approver_id)
            holiday_status_id = self.get_create_leave_type(leave_allocation_id.holiday_status_id)
            second_approver_id = self.get_create_employee(leave_allocation_id.second_approver_id)
            # manager_id = self.get_create_employee(leave_allocation_id.manager_id)
            # meeting_id = self.get_create_calendar_event(leave_allocation_id.meeting_id)
            other_leave_allocation_id_data_read[0].update({
                'department_id': department_id and department_id.id,
                'employee_id': employee_id and employee_id.id,
                'first_approver_id': first_approver_id and first_approver_id.id,
                'holiday_status_id': holiday_status_id and holiday_status_id.id,
                'second_approver_id': second_approver_id and second_approver_id.id,
            })
            other_leave_allocation_id = leave_allocation_id_obj.create(other_leave_allocation_id_data_read[0])
        return other_leave_allocation_id


    @api.multi
    def get_create_global_leaves(self, global_leave_id, calendar_id):
        other_global_leave_id = False
        if not global_leave_id:
            return other_global_leave_id
        resource_calendar_leaves = self.env['resource.calendar.leaves']
        other_global_leave_id = resource_calendar_leaves.search([('name', '=', global_leave_id.name)], limit=1)
        other_resource_calender_read = global_leave_id.read(['date_from', 'date_to', 'time_type', 'name'])
        holiday_id = self.get_create_hr_leave(global_leave_id.holiday_id)
        if global_leave_id.holiday_id.parent_id:
            hr_leave_obj = self.env['hr.leave']
            parent_leave_id = global_leave_id.holiday_id.parent_id
            old_parent_leave_id = holiday_id
            while parent_leave_id:
                new_parent_leave_id = self.get_create_hr_leave(parent_leave_id)
                parent_leave_id = parent_leave_id.parent_id or False
                old_parent_leave_id.write({
                    'parent_id': new_parent_leave_id.id,
                    })
                old_parent_leave_id = new_parent_leave_id

        resource_id = self.get_create_resource_resource(global_leave_id.resource_id)
        other_resource_calender_read[0].update({
            'calendar_id': calendar_id and calendar_id.id,
            'resource_id': resource_id and resource_id.id,
            'holiday_id': holiday_id and holiday_id.id,
            })
        if not other_global_leave_id:
            other_global_leave_id = resource_calendar_leaves.create(other_resource_calender_read[0])
        else:
            other_global_leave_id.write(other_resource_calender_read[0])
        return other_global_leave_id

    @api.multi
    def get_create_resource_calender(self, calendar_id):
        other_calendar_id = False
        if not calendar_id:
            return other_calendar_id
        resource_calender_obj = self.env['resource.calendar']
        other_calendar_id = resource_calender_obj.search([('name', '=', calendar_id.name)], limit=1)
        other_resource_calender_read = calendar_id.read(['name', 'fix_days', 'hours_per_day', 'tz'])
        if not other_calendar_id:
            other_calendar_id = resource_calender_obj.create(other_resource_calender_read[0])
        else:
            other_calendar_id.write(other_resource_calender_read[0])

        for attendance_id in calendar_id.attendance_ids:
            self.get_create_resource_calender_attendance(attendance_id, other_calendar_id)
        for global_leave_id in calendar_id.global_leave_ids:
            self.get_create_global_leaves(global_leave_id, other_calendar_id)

        return other_calendar_id

    @api.multi
    def get_create_resource_resource(self, resource_id):
        other_resource_id = False
        if not resource_id:
            return other_resource_id
        resource_resource_obj = self.env['resource.resource']
        other_resource_id = resource_resource_obj.search([('name', '=', resource_id.name)], limit=1)

        other_resource_resource_read = resource_id.read(['name', 'active', 'resource_type', 'tz'])
        calendar_id = user_id = False
        if resource_id.calendar_id:
            calendar_id = self.get_create_resource_calender(resource_id.calendar_id)
        if resource_id.user_id:
           user_id = self.get_create_res_users(resource_id.user_id)
        other_resource_resource_read[0].update({
            'calendar_id': calendar_id and calendar_id.id,
            'user_id': user_id and user_id.id,
            })
        if not other_resource_id:
            other_resource_id = resource_resource_obj.create(other_resource_resource_read[0])
        else:
            other_resource_id.write(other_resource_resource_read[0])

        return other_resource_id

    @api.multi
    def get_create_function_executes(self, function_executed_id):
        other_function_executed_id = False
        if not function_executed_id:
            return other_function_executed_id
        function_executed_obj = self.env['function.executed']
        other_function_executed_id = function_executed_obj.search([('name', '=', function_executed_id.name)], limit=1)
        function_executed_data_read = function_executed_id.read(['description', 'name'])
        if not other_function_executed_id:
            other_function_executed_id = function_executed_obj.create(function_executed_data_read[0])
        else:
            other_function_executed_id.write(function_executed_data_read[0])
        return other_function_executed_id

    @api.multi
    def get_create_hr_retention_method_rf(self, retention_method_rf_id):
        other_retention_method_rf_id = False
        if not retention_method_rf_id:
            return other_retention_method_rf_id
        hr_retention_method_rf_obj = self.env['hr.retention.method.rf']
        other_retention_method_rf_id = hr_retention_method_rf_obj.search([('name', '=', retention_method_rf_id.name)], limit=1)
        retention_method_rf_data_read = retention_method_rf_id.read(['description', 'name'])
        if not other_retention_method_rf_id:
            other_retention_method_rf_id = hr_retention_method_rf_obj.create(retention_method_rf_data_read[0])
        else:
            other_retention_method_rf_id.write(retention_method_rf_data_read[0])
        return other_retention_method_rf_id

    @api.multi
    def get_create_hr_marital_status(self, marital_status_id):
        other_marital_status_id = False
        if not marital_status_id:
            return other_marital_status_id
        hr_marital_status_obj = self.env['hr.marital.status']
        other_marital_status_id = hr_marital_status_obj.search([('name', '=', marital_status_id.name)], limit=1)
        if not other_marital_status_id:
            other_marital_status_id = hr_marital_status_obj.create({'name': marital_status_id.name})
        else:
            other_marital_status_id.write({'name': marital_status_id.name})
        return other_marital_status_id

    @api.multi
    def get_create_res_users(self, user_id):
        other_user_id = False
        if not user_id:
            return other_user_id
        res_users_obj = self.env['res.users']
        other_user_id = res_users_obj.search(['|', ('login', '=', user_id.login), ('active', '=', False)], limit=1)
        # if not other_user_id:
        #     other_users_data_read = user_id.read(['login', 'name'])
        #     other_user_id = res_users_obj.create(other_users_data_read[0])
        return other_user_id

    @api.multi
    def get_create_academic_area(self, academic_area_id):
        other_academic_area_id = False
        if not academic_area_id:
            return other_academic_area_id
        hr_academic_area_obj = self.env['hr.academic.area']
        other_academic_area_id = hr_academic_area_obj.search([('name', '=', academic_area_id.name)], limit=1)
        other_academic_area_data_read = academic_area_id.read(['name', 'active', 'description'])
        if not other_academic_area_id:
            other_academic_area_id = hr_academic_area_obj.create(other_academic_area_data_read[0])
        else:
            other_academic_area_id.write(other_academic_area_data_read[0])
        return other_academic_area_id

    @api.multi
    def get_create_hr_academic_institution(self, academic_institution_id):
        other_academic_institution_id = False
        if not academic_institution_id:
            return other_academic_institution_id
        hr_academic_institution_obj = self.env['hr.academic.institution']
        other_academic_institution_id = hr_academic_institution_obj.search([('name', '=', academic_institution_id.name)], limit=1)
        institution_data_read = academic_institution_id.read(['description', 'name'])
        if not other_academic_institution_id:
            other_academic_institution_id = hr_academic_institution_obj.create(institution_data_read[0])
        else:
            other_academic_institution_id.write(institution_data_read[0])
        return other_academic_institution_id

    @api.multi
    def get_create_hr_cv_employee(self, hr_cv_employee_id):
        other_hr_cv_employee_id = False
        if not hr_cv_employee_id:
            return other_hr_cv_employee_id
        hr_cv_employee_obj = self.env['hr.cv.employee']
        other_hr_cv_employee_id = hr_cv_employee_obj.search([('name', '=', hr_cv_employee_id.name)], limit=1)
        hr_cv_employee_data_read = hr_cv_employee_id.read(['active', 'name'])

        academic_studies_ids = self.get_create_hr_cv_academic_studies(hr_cv_employee_id.academic_studies_ids)
        animal_pets_ids = self.get_create_animal_pets(hr_cv_employee_id.animal_pets_ids)
        family_group_ids = self.get_create_family_group(hr_cv_employee_id.family_group_ids)
        hobbies_ids = self.get_create_hobbies(hr_cv_employee_id.hobbies_ids)
        holding_ids = self.get_create_holding_ids(hr_cv_employee_id.holding_ids)
        laboral_experience_ids =self.get_create_laboral_experience_ids(hr_cv_employee_id.laboral_experience_ids)
        language_ids = self.get_create_language_ids(hr_cv_employee_id.language_ids)
        personal_employee_ids = self.get_create_personal_employee_ids(hr_cv_employee_id.personal_employee_ids)
        sport_ids = self.get_create_sport_ids(hr_cv_employee_id.sport_ids)

        hr_cv_employee_data_read[0].update({
            'academic_studies_ids': academic_studies_ids,
            'animal_pets_ids': animal_pets_ids,
            'family_group_ids': family_group_ids,
            'hobbies_ids': hobbies_ids,
            'holding_ids': holding_ids,
            'laboral_experience_ids': laboral_experience_ids,
            'language_ids': language_ids,
            'personal_employee_ids': personal_employee_ids,
            'sport_ids': sport_ids,
        })
        if not other_hr_cv_employee_id:
            other_hr_cv_employee_id = hr_cv_employee_obj.create(hr_cv_employee_data_read[0])
        else:
            other_hr_cv_employee_id.write(hr_cv_employee_data_read[0])
        return other_hr_cv_employee_id

    @api.multi
    def get_create_level_academic(self, level_academic_id):
        other_level_academic_id = False
        if not level_academic_id:
            return other_level_academic_id
        hr_academic_level_obj = self.env['hr.academic.level']
        other_level_academic_id = hr_academic_level_obj.search([('name', '=', level_academic_id.name)], limit=1)
        hr_academic_level_data_read = level_academic_id.read(['active', 'name', 'description'])
        if not other_level_academic_id:
            other_level_academic_id = hr_academic_level_obj.create(hr_academic_level_data_read[0])
        else:
            other_level_academic_id.write(hr_academic_level_data_read[0])
        return other_level_academic_id

    @api.multi
    def get_create_hr_cv_academic_studies(self, academic_studies_ids):
        if not academic_studies_ids:
            return []
        hr_cv_academic_studies_obj = self.env['hr.cv.academic.studies']
        academic_studies_ids_list = []
        for academic_studies_id in academic_studies_ids:
            academic_area_id = self.get_create_academic_area(academic_studies_id.academic_area_id)
            academic_institution_id = self.get_create_hr_academic_institution(academic_studies_id.academic_institution_id)
            country_id = self.get_create_country(academic_studies_id.country_id)
            state_id = self.get_create_state(academic_studies_id.state_id)
            city_id = self.get_create_place(academic_studies_id.city_id)

            hr_cv_employee_id = self.get_create_hr_cv_employee(academic_studies_id.hr_cv_employee_id)
            level_academic_id = self.get_create_level_academic(academic_studies_id.level_academic_id)

            academic_studies_ids_list.append((0, 0, {
                'name': academic_studies_id.name,
                'name_support': academic_studies_id.name_support,
                'support_attachment_url': academic_studies_id.support_attachment_url,
                'end_date': academic_studies_id.end_date,
                'start_date': academic_studies_id.start_date,
                'academic_area_id': academic_area_id and academic_area_id.id,
                'academic_institution_id': academic_institution_id and academic_institution_id.id,
                'city_id': city_id and city_id.id,
                'country_id': country_id and country_id.id,
                'state_id': state_id and state_id.id,
                'hr_cv_employee_id': hr_cv_employee_id and hr_cv_employee_id.id,
                'level_academic_id': level_academic_id and level_academic_id.id,
            }))
        return academic_studies_ids_list

    @api.multi
    def get_create_deductions_accumulate(self, deductions_accumulate_ids):
        if not deductions_accumulate_ids:
            return []
        deductions_accumulate_ids_list = []
        for deductions_accumulate_id in deductions_accumulate_ids:
            deductions_accumulate_ids_list.append((0, 0, {
                'name': deductions_accumulate_id.name,
                'accumulate': deductions_accumulate_id.accumulate,
                'year': deductions_accumulate_id.year,
            }))
        return deductions_accumulate_ids_list

    @api.multi
    def get_create_animal_race(self, animal_race_id):
        other_animal_race_id = False
        if not animal_race_id:
            return other_animal_race_id
        animal_race_obj = self.env['animal.race']
        other_animal_race_id = animal_race_obj.search([('name', '=', animal_race_id.name)], limit=1)
        animal_race_data_read = animal_race_id.read(['description', 'name'])
        if not other_animal_race_id:
            other_animal_race_id = animal_race_obj.create(animal_race_data_read[0])
        else:
            other_animal_race_id.write(animal_race_data_read[0])
        return other_animal_race_id

    @api.multi
    def get_create_animal_type(self, animal_type_id):
        other_animal_type_id = False
        if not animal_type_id:
            return other_animal_type_id
        animal_type_obj = self.env['animal.type']
        other_animal_type_id = animal_type_obj.search([('name', '=', animal_type_id.name)], limit=1)
        animal_type_data_read = animal_type_id.read(['description', 'name'])
        if not other_animal_type_id:
            other_animal_type_id = animal_type_obj.create(animal_type_data_read[0])
        else:
            other_animal_type_id.write(animal_type_data_read[0])
        return other_animal_type_id

    @api.multi
    def get_create_animal_pets(self, animal_pets_ids):
        if not animal_pets_ids:
            return []
        animal_pets_ids_list = []
        for animal_pets_id in animal_pets_ids:
            animal_race_id = self.get_create_animal_race(animal_pets_id.animal_race_id)
            animal_type_id = self.get_create_animal_type(animal_pets_id.animal_type_id)
            hr_cv_employee_id = self.get_create_hr_cv_employee(animal_pets_id.hr_cv_employee_id)
            animal_pets_ids_list.append((0, 0, {
                'name': animal_pets_id.name,
                'age': animal_pets_id.age,
                'dob': animal_pets_id.dob,
                'animal_race_id': animal_race_id and animal_race_id.id,
                'animal_type_id': animal_type_id and animal_type_id.id,
                'hr_cv_employee_id': hr_cv_employee_id and hr_cv_employee_id.id,
            }))
        return animal_pets_ids_list

    @api.multi
    def get_create_contact_reference(self, contact_reference_ids):
        if not contact_reference_ids:
            return []
        contact_reference_ids_list = []
        for contact_reference_id in contact_reference_ids:
            partner_id = self.get_create_partner(contact_reference_id.partner_id)
            contact_reference_ids_list.append((0, 0, {
                'contact': contact_reference_id.contact,
                'partner_id': partner_id and partner_id.id,
                'relation': contact_reference_id.relation,
            }))
        return contact_reference_ids_list

    @api.multi
    def get_create_hr_deduction_type_rf(self, hr_deduction_type_rf_id):
        other_hr_deduction_type_rf_id = False
        if not hr_deduction_type_rf_id:
            return other_hr_deduction_type_rf_id
        hr_deduction_rf_obj = self.env['hr.deduction.type.rf']
        other_hr_deduction_type_rf_id = hr_deduction_rf_obj.search([('name', '=', hr_deduction_type_rf_id.name)], limit=1)
        hr_deduction_data_read = hr_deduction_type_rf_id.read(['active','description', 'name', 'date_inactive', 'end_date', 'sequence'])
        if not other_hr_deduction_type_rf_id:
            other_hr_deduction_type_rf_id = hr_deduction_rf_obj.create(hr_deduction_data_read[0])
        else:
            other_hr_deduction_type_rf_id.write(hr_deduction_data_read[0])
        return other_hr_deduction_type_rf_id

    @api.multi
    def get_create_hr_deduction_rf(self, hr_deduction_id):
        other_hr_deduction_id = False
        if not hr_deduction_id:
            return other_hr_deduction_id
        hr_deduction_rf_obj = self.env['hr.deduction.rf']
        other_hr_deduction_id = hr_deduction_rf_obj.search([('name', '=', hr_deduction_id.name)], limit=1)
        hr_deduction_data_read = hr_deduction_id.read(['active','description', 'name', 'dependent', 'max_acumulate',
            'max_percentage', 'max_uvt', 'max_value'])
        type_id = self.get_create_hr_deduction_type_rf(hr_deduction_id.type_id)
        hr_deduction_data_read[0].update({'type_id': type_id and type_id.id})
        if not other_hr_deduction_id:
            other_hr_deduction_id = hr_deduction_rf_obj.create(hr_deduction_data_read[0])
        else:
            other_hr_deduction_id.write(hr_deduction_data_read[0])
        return other_hr_deduction_id

    @api.multi
    def get_create_hr_deduction_rf_employee(self, deductions_ids):
        hr_deduction_rf_employee_obj = self.env['hr.deductions.rf.employee']
        if not deductions_ids:
            return []
        deductions_ids_list = []
        for deductions_id in deductions_ids:
            hr_deduction_id = self.get_create_hr_deduction_rf(deductions_id.hr_deduction_id)
            hr_deduction_type_id = self.get_create_hr_deduction_type_rf(deductions_id.hr_deduction_type_id)
            new_deductions_id = hr_deduction_rf_employee_obj.create({
                'active': deductions_id.active,
                'name': deductions_id.name,
                'date_end': deductions_id.date_end,
                'end_date': deductions_id.end_date,
                'start_date': deductions_id.start_date,
                'value': deductions_id.value,
                'hr_deduction_id': hr_deduction_id and hr_deduction_id.id,
                'hr_deduction_type_id': hr_deduction_type_id and hr_deduction_type_id.id,
            })
            deductions_ids_list.append(new_deductions_id.id)
        return deductions_ids_list

    @api.multi
    def get_create_hr_family_group_categ(self, hr_family_group_categ_id):
        other_hr_family_group_categ_id = False
        if not hr_family_group_categ_id:
            return other_hr_family_group_categ_id
        hr_family_group_categ_obj = self.env['hr.family.group.categ']
        other_hr_family_group_categ_id = hr_family_group_categ_obj.search([('name', '=', hr_family_group_categ_id.name)], limit=1)
        family_rel_data_read = hr_family_group_categ_id.read(['active','description', 'name'])
        if not hr_family_group_categ_id:
            other_hr_family_group_categ_id = hr_family_group_categ_obj.create(family_rel_data_read[0])
        else:
            other_hr_family_group_categ_id.write(family_rel_data_read[0])
        return other_hr_family_group_categ_id

    @api.multi
    def get_create_family_rel(self, family_rel_id):
        other_family_rel_id = False
        if not family_rel_id:
            return other_family_rel_id
        hr_family_relationship_obj = self.env['hr.family.relationship']
        other_family_rel_id = hr_family_relationship_obj.search([('name', '=', family_rel_id.name)], limit=1)
        family_rel_data_read = family_rel_id.read(['active','description', 'name'])
        hr_family_group_categ_id = self.get_create_hr_family_group_categ(family_rel_id.hr_family_group_categ_id)
        family_rel_data_read[0].update({'hr_family_group_categ_id': hr_family_group_categ_id and hr_family_group_categ_id.id})
        if not other_family_rel_id:
            other_family_rel_id = hr_family_relationship_obj.create(family_rel_data_read[0])
        else:
            other_family_rel_id.write(family_rel_data_read[0])
        return other_family_rel_id

    @api.multi
    def get_create_occupation(self, occupation_id):
        other_occupation_id = False
        if not occupation_id:
            return other_occupation_id
        occupations_obj = self.env['hr.occupations']
        other_occupation_id = occupations_obj.search([('name', '=', occupation_id.name)], limit=1)
        occupation_data_read = occupation_id.read(['active','description', 'name'])
        if not other_occupation_id:
            other_occupation_id = occupations_obj.create(occupation_data_read[0])
        else:
            other_occupation_id.write(occupation_data_read[0])
        return other_occupation_id

    @api.multi
    def get_create_family_group(self, family_group_ids):
        if not family_group_ids:
            return []
        family_group_ids_list = []
        for family_group_id in family_group_ids:
            hr_cv_employee_id = self.get_create_hr_cv_employee(family_group_id.hr_cv_employee_id)
            family_rel_id = self.get_create_family_rel(family_group_id.family_rel_id)
            partner_id = self.get_create_partner(family_group_id.partner_id)
            occupation_id = self.get_create_occupation(family_group_id.occupation_id)
            family_group_ids_list.append((0, 0, {
                'active': family_group_id.active,
                'name': family_group_id.name,
                'contact_emergency': family_group_id.contact_emergency,
                'same_home': family_group_id.same_home,
                'birthdate': family_group_id.birthdate,
                'age': family_group_id.age,
                'gender': family_group_id.gender,
                'partner_id': partner_id and partner_id.id,
                'family_rel_id': family_rel_id and family_rel_id.id,
                'hr_cv_employee_id': hr_cv_employee_id and hr_cv_employee_id.id,
                'occupation_id': occupation_id and occupation_id.id,
            }))
        return family_group_ids_list

    @api.multi
    def get_create_hobby(self, hobby_id):
        other_hobby_id = False
        if not hobby_id:
            return other_hobby_id
        hr_hobbies_obj = self.env['hr.hobbies']
        other_hobby_id = hr_hobbies_obj.search([('name', '=', hobby_id.name)], limit=1)
        hobby_id_data_read = hobby_id.read(['active', 'name'])
        if not other_hobby_id:
            other_hobby_id = hr_hobbies_obj.create(hobby_id_data_read[0])
        else:
            other_hobby_id.write(hobby_id_data_read[0])
        return other_hobby_id

    @api.multi
    def get_create_hobbies(self, hobbies_ids):
        if not hobbies_ids:
            return []
        hobbies_ids_list = []
        for hobbies_id in hobbies_ids:
            hr_cv_employee_id = self.get_create_hr_cv_employee(hobbies_id.hr_cv_employee_id)
            hobby_id = self.get_create_hobby(hobbies_id.hobby_id)
            hobbies_ids_list.append((0, 0, {
                'active': hobbies_id.active,
                'hr_cv_employee_id': hr_cv_employee_id and hr_cv_employee_id.id,
                'hobby_id': hobby_id and hobby_id.id,
            }))
        return hobbies_ids_list

    @api.multi
    def get_create_holding(self, holding_id):
        other_holding_id = False
        if not holding_id:
            return other_holding_id
        hr_holding_obj = self.env['hr.holding']
        other_holding_id = hr_holding_obj.search([('name', '=', holding_id.name)], limit=1)
        holding_id_data_read = holding_id.read(['active', 'name'])
        if not other_holding_id:
            other_holding_id = hr_holding_obj.create(holding_id_data_read[0])
        else:
            other_holding_id.write(holding_id_data_read[0])
        return other_holding_id

    @api.multi
    def get_create_holding_ids(self, holding_ids):
        if not holding_ids:
            return []
        holding_ids_list = []
        for holding_id in holding_ids:
            hr_cv_employee_id = self.get_create_hr_cv_employee(holding_id.hr_cv_employee_id)
            r_holding_id = self.get_create_holding(holding_id.holding_id)
            holding_ids_list.append((0, 0, {
                'active': holding_id.active,
                'hr_cv_employee_id': hr_cv_employee_id and hr_cv_employee_id.id,
                'holding_id': r_holding_id and r_holding_id.id,
            }))
        return holding_ids_list

    @api.multi
    def get_create_hr_competition_language(self, competition_id):
        other_competition_id = False
        if not competition_id:
            return other_competition_id
        hr_competition_language_obj = self.env['hr.competition.language']
        other_competition_id = hr_competition_language_obj.search([('name', '=', competition_id.name)], limit=1)
        competition_id_data_read = competition_id.read(['active','description', 'name'])
        if not other_competition_id:
            other_competition_id = hr_competition_language_obj.create(competition_id_data_read[0])
        else:
            other_competition_id.write(competition_id_data_read[0])
        return other_competition_id

    @api.multi
    def get_create_language(self, language_id):
        other_language_id = False
        if not language_id:
            return other_language_id
        hr_language_obj = self.env['hr.language']
        other_language_id = hr_language_obj.search([('name', '=', language_id.name)], limit=1)
        language_id_data_read = language_id.read(['active', 'name'])
        if not other_language_id:
            other_language_id = hr_language_obj.create(language_id_data_read[0])
        else:
            other_language_id.write(language_id_data_read[0])
        return other_language_id.id

    @api.multi
    def get_create_hr_competition_level_language(self, competition_level_language_id):
        other_competition_level_language_id = False
        if not competition_level_language_id:
            return other_competition_level_language_id
        hr_competition_level_language_obj = self.env['hr.competition.level.language']
        other_competition_level_language_id = hr_competition_level_language_obj.search([('name', '=', competition_level_language_id.name)], limit=1)
        competition_level_language_id_data_read = competition_level_language_id.read(['active','description', 'name'])
        if not other_competition_level_language_id:
            other_competition_level_language_id = hr_competition_level_language_obj.create(competition_level_language_id_data_read[0])
        else:
            other_competition_level_language_id.write(competition_level_language_id_data_read[0])
        return other_competition_level_language_id

    @api.multi
    def get_create_language_ids(self, language_ids):
        # hr.cv.language.employee
        if not language_ids:
            return []
        language_ids_list = []
        for language_id in language_ids:
            hr_cv_employee_id = self.get_create_hr_cv_employee(language_id.hr_cv_employee_id)
            competition_id = self.get_create_hr_competition_language(language_id.competition_id)
            level_id = self.get_create_hr_competition_level_language(language_id.level_id)
            language_ids_list.append((0, 0, {
                'active': language_id.active,
                'hr_cv_employee_id': hr_cv_employee_id and hr_cv_employee_id.id,
                'language_id': self.get_create_language(language_id.language_id),
                'competition_id': competition_id and competition_id.id,
                'level_id': level_id and level_id.id,
            }))
        return language_ids_list


    @api.multi
    def get_create_sport(self, sport_id):
        other_sport_id = False
        if not sport_id:
            return other_sport_id
        hr_sports_obj = self.env['hr.sports']
        other_sport_id = hr_sports_obj.search([('name', '=', sport_id.name)], limit=1)
        sport_id_data_read = sport_id.read(['active', 'name', 'description'])
        if not other_sport_id:
            other_sport_id = hr_sports_obj.create(sport_id_data_read[0])
        else:
            other_sport_id.write(sport_id_data_read[0])
        return other_sport_id.id

    @api.multi
    def get_create_sport_ids(self, sport_ids):
        if not sport_ids:
            return []
        sport_ids_list = []
        for sport_id in sport_ids:
            sport_ids_list.append((0, 0, {
                'sport_id': self.get_create_sport(sport_id.sport_id),
            }))
        return sport_ids_list

    @api.multi
    def get_create_hr_acumulated_rules(self, rules_ids):
        # hr.acumulated.rules
        if not rules_ids:
            return []
        rules_ids_list = []
        for rules_id in rules_ids:
            salary_rule_id = self.get_create_salary_rule(rules_id.rule_id, False)
            rules_ids_list.append((0, 0, {
                'sign': rules_id.sign,
                'rule_id': salary_rule_id and salary_rule_id.id,
            }))
        return rules_ids_list

    @api.multi
    def get_create_hr_rules_acumulate(self, hr_rules_acumulate_id):
        other_hr_rules_acumulate_id = False
        if not hr_rules_acumulate_id:
            return other_hr_rules_acumulate_id
        hr_conf_acumulated_obj = self.env['hr.conf.acumulated']
        other_hr_rules_acumulate_id = hr_conf_acumulated_obj.search([('name', '=', hr_rules_acumulate_id.name)], limit=1)

        hr_rules_acumulate_id_data_read = hr_rules_acumulate_id.read(['active', 'name'])
        rules_add_ids = self.get_create_hr_acumulated_rules(hr_rules_acumulate_id.rules_add_ids)
        rules_substract_ids = self.get_create_hr_acumulated_rules(hr_rules_acumulate_id.rules_substract_ids)
        hr_rules_acumulate_id_data_read[0].update({
            'rules_add_ids': rules_add_ids,
            'rules_substract_ids': rules_substract_ids,
            })
        if not other_hr_rules_acumulate_id:
            other_hr_rules_acumulate_id = hr_conf_acumulated_obj.create(hr_rules_acumulate_id_data_read[0])
        else:
            other_hr_rules_acumulate_id.write(hr_rules_acumulate_id_data_read[0])
        return other_hr_rules_acumulate_id.id

    @api.multi
    def get_create_res_groups_all_details(self, old_group_id):
        new_group_id = self.get_create_res_groups(old_group_id)
        trans_implied_ids = []
        for trans_implied_id in old_group_id.trans_implied_ids:
            new_trans_implied_id = self.get_create_res_groups(trans_implied_id)
            trans_implied_ids.append(new_trans_implied_id.id)

        implied_ids = []
        for implied_id in old_group_id.implied_ids:
            new_implied_id = self.get_create_res_groups(implied_id)
            implied_ids.append(new_implied_id.id)

        if new_group_id:
            new_group_id.write({
                'trans_implied_ids': [(6, 0, trans_implied_ids)],
                'implied_ids': [(6, 0, implied_ids)],
            })
        return new_group_id

    @api.multi
    def get_create_res_groups(self, group_id):
        other_group_id = False
        if not group_id:
            return other_group_id
        group_obj = self.env['res.groups']
        ir_ui_menu_obj = self.env['ir.ui.menu']
        ir_rule_obj = self.env['ir.rule']
        ir_ui_view_obj = self.env['ir.ui.view']
        ir_model_access_obj = self.env['ir.model.access']
        other_group_id = group_obj.search([('name', '=', group_id.name)], limit=1)
        group_id_data_read = group_id.read(['name'])


        category_id = self.env['ir.module.category'].search([('name', '=', group_id.name)])
        users_list = []
        for user_id in group_id.users:
            new_user_id = self.get_create_res_users(user_id)
            if new_user_id:
                users_list.append(new_user_id.id)

        # menu_ids = []
        # for menu_id in group_id.menu_access:
        #     new_menu_id = ir_ui_menu_obj.search([('complete_name', '=', menu_id.complete_name)], limit=1)
        #     menu_ids.append(new_menu_id.id)

        # rule_groups_list = []
        # for rule_group_id in group_id.rule_groups:
        #     new_rule_group_id = ir_rule_obj.search([('name', '=', rule_group_id.name), ('model_id.model', '=', rule_group_id.model_id.model)], limit=1)
        #     rule_groups_list.append(new_rule_group_id.id)

        # view_list = []
        # for view_id in group_id.view_access:
        #     new_view_id = ir_ui_view_obj.search([('name', '=', view_id.name)], limit=1)
        #     view_list.append(new_user_id.id)


        # model_access_list = []
        # for model_access_id in group_id.model_access:
        #     new_model_access_id = ir_model_access_obj.search([('name', '=', model_access_id.name)], limit=1)
        #     model_access_list.append(model_access_id.id)

        group_id_data_read[0].update({
            'users': [(6, 0, users_list)],
            'category_id': category_id and category_id.id,
            # 'menu_access': [(6,0, menu_ids)],
            # 'rule_groups': [(6,0, rule_groups_list)],
            # 'view_access': [(6,0, view_list)],
            # 'model_access': [(6, 0, model_access_list)]
            })

        if not other_group_id:
            other_group_id = group_obj.create(group_id_data_read[0])
        # else:
        #     other_group_id.write(group_id_data_read[0])
        return other_group_id

    @api.multi
    def get_create_hr_novelty_type(self, type_id):
        other_type_id = False
        if not type_id:
            return other_type_id
        hr_novelty_type_obj = self.env['hr.novelty.type']
        other_type_id = hr_novelty_type_obj.search([('name', '=', type_id.name)], limit=1)

        type_id_data_read = type_id.read(['description', 'name'])
        if not other_type_id:
            other_type_id = hr_novelty_type_obj.create(type_id_data_read[0])
        else:
            other_type_id.write(type_id_data_read[0])
        return other_type_id

    @api.multi
    def get_create_hr_novelty_event_type_subtype(self, subtype_id):
        other_subtype_id = False
        if not subtype_id:
            return other_subtype_id
        hr_novelty_type_subtype_obj = self.env['hr.novelty.type.subtype']
        other_subtype_id = hr_novelty_type_subtype_obj.search([('name', '=', subtype_id.name)], limit=1)

        subtype_id_data_read = subtype_id.read(['description', 'name'])
        type_id = self.get_create_hr_novelty_type(subtype_id.type_id)

        subtype_id_data_read[0].update({
            'type_id': type_id and type_id.id,
            })
        if not other_subtype_id:
            other_subtype_id = hr_novelty_type_subtype_obj.create(subtype_id_data_read[0])
        else:
            other_subtype_id.write(subtype_id_data_read[0])
        return other_subtype_id


    @api.model
    def get_create_you_model_id_all(self, you_model_id):
        new_you_model_id = self.get_create_you_model_id(you_model_id)
        if you_model_id.parent_id:
            novelty_you_model_id = you_model_id.parent_id
            old_employee_id = new_you_model_id
            while novelty_you_model_id:
                new_parent_you_model_id = self.get_create_you_model_id(novelty_you_model_id)
                novelty_you_model_id = novelty_you_model_id.parent_id or False
                old_employee_id.write({
                    'parent_id': new_parent_you_model_id.id,
                    })
                old_employee_id = new_parent_you_model_id
        return new_you_model_id

    @api.model
    def get_create_you_model_id(self, you_model_id):
        other_you_model_id = False
        if not you_model_id:
            return other_you_model_id
        hr_module_you_obj = self.env['hr.module.you']
        other_you_model_id = hr_module_you_obj.search([('name', '=', you_model_id.name)], limit=1)

        you_model_id_data_read = you_model_id.read(['description', 'name', 'reference_module', 'show', 'tag'])
        group_id = self.get_create_res_groups(you_model_id.group_id)

        you_model_id_data_read[0].update({
            'group_id': group_id and group_id.id,
            })

        if not other_you_model_id:
            other_you_model_id = hr_module_you_obj.create(you_model_id_data_read[0])
        else:
            other_you_model_id.write(you_model_id_data_read[0])
        return other_you_model_id

    @api.multi
    def get_create_hr_novelty_event(self, novelty_event_id):
        other_novelty_event_id = False
        if not novelty_event_id:
            return other_novelty_event_id
        hr_novelty_obj = self.env['hr.novelty.event']
        other_novelty_event_id = hr_novelty_obj.search([('name', '=', novelty_event_id.name)], limit=1)

        novelty_event_id_data_read = novelty_event_id.read(['active', 'advance_holidays', 'affectation', 'approver',
            'attachment_required', 'calendar_type', 'company_only', 'description', 'income_withholding',
            'increase_salary', 'is_adjunto_obligatorio', 'is_aplica_fecha_final', 'is_end_business_day',
            'is_h_e_procedimiento', 'is_horas_fijas', 'is_motivo_de_retiro', 'is_optional_approver',
            'is_optional_approver_2', 'is_recruitment', 'is_requiere_adjunto', 'is_tipo_de_incapacidad',
            'limit_advance', 'max_days', 'min_days', 'name', 'new_recruitment', 'projection_vacation',
            'requered_account', 'requered_attachment_lic', 'responsible_required', 'restriction_day', 'sara',
            'second_approver_required', 'show_you', 'unjustified'])

        group_ids = []
        for group_id in novelty_event_id.group_ids:
            new_group_id = self.get_create_res_groups_all_details(group_id)
            group_ids.append(new_group_id.id)

        grupo_de_seguidores_ids = []
        for group_id in novelty_event_id.grupo_de_seguidores_ids:
            new_group_id = self.get_create_res_groups_all_details(group_id)
            grupo_de_seguidores_ids.append(new_group_id.id)

        deduction_id = self.get_create_hr_deduction_rf(novelty_event_id.deduction_id)
        leave_type_id = self.get_create_leave_type(novelty_event_id.leave_type_id)
        
        optional_approver2_group_id = self.get_create_res_groups_all_details(novelty_event_id.optional_approver2_group_id)
        optional_approver_group_id = self.get_create_res_groups_all_details(novelty_event_id.optional_approver_group_id)
        prepaid_medicine_id = self.get_create_partner(novelty_event_id.prepaid_medicine_id)
        second_approver_group_id = self.get_create_res_groups_all_details(novelty_event_id.second_approver_group_id)

        subtype_id = self.get_create_hr_novelty_event_type_subtype(novelty_event_id.subtype_id)
        type_id = self.get_create_hr_novelty_type(novelty_event_id.type_id)
        you_model_id = self.get_create_you_model_id_all(novelty_event_id.you_model_id)

        if novelty_event_id_data_read[0].get('min_days') == 1.0:
            novelty_event_id_data_read[0].update({'min_days': 0.0})

        novelty_event_id_data_read[0].update({
            'group_ids': [(6,0, group_ids)],
            'grupo_de_seguidores_ids': [(6,0,grupo_de_seguidores_ids)],
            'deduction_id': deduction_id and deduction_id.id,
            'leave_type_id': leave_type_id and leave_type_id.id,
            'optional_approver2_group_id': optional_approver2_group_id and optional_approver2_group_id.id,
            'optional_approver_group_id': optional_approver_group_id and optional_approver_group_id.id,
            'prepaid_medicine_id': prepaid_medicine_id and prepaid_medicine_id.id,
            'second_approver_group_id': second_approver_group_id and second_approver_group_id.id,
            'subtype_id': subtype_id and subtype_id.id,
            'type_id': type_id and type_id.id,
            'you_model_id': you_model_id and you_model_id.id,
            })
        if not other_novelty_event_id:
            other_novelty_event_id = hr_novelty_obj.create(novelty_event_id_data_read[0])
        else:
            other_novelty_event_id.write(novelty_event_id_data_read[0])
        return other_novelty_event_id

    @api.model
    def get_create_hr_experience_time(self, experience_id):
        other_experience_id = False
        if not experience_id:
            return other_experience_id
        experience_obj = self.env['hr.experience.time']
        other_experience_id = experience_obj.search([('name', '=', experience_id.name)], limit=1)
        experience_id_data_read = experience_id.read(['description', 'name', 'active'])
        if not other_experience_id:
            other_experience_id = experience_obj.create(experience_id_data_read[0])
        else:
            other_experience_id.write(experience_id_data_read[0])
        return other_experience_id

    @api.multi
    def get_create_hr_leave_code_id(self, leave_code_id):
        other_leave_code_id = False
        if not leave_code_id:
            return other_leave_code_id
        leave_code_id_obj = self.env['hr.leave.code']
        other_leave_code_id = leave_code_id_obj.search([('name', '=', leave_code_id.name)], limit=1)
        leave_code_id_data_read = leave_code_id.read(['name', 'code'])
        if not other_leave_code_id:
            other_leave_code_id = leave_code_id_obj.create(leave_code_id_data_read[0])
        else:
            other_leave_code_id.write(leave_code_id_data_read[0])
        return other_leave_code_id

    @api.multi
    def get_create_motivo_talento_id(self, motivo_talento_id):
        other_motivo_talento_id = False
        if not motivo_talento_id:
            return other_motivo_talento_id
        motivo_talento_id_obj = self.env['motivo.talento']
        other_motivo_talento_id = motivo_talento_id_obj.search([('name', '=', motivo_talento_id.name)], limit=1)
        motivo_talento_id_data_read = motivo_talento_id.read(['name'])
        if not other_motivo_talento_id:
            other_motivo_talento_id = motivo_talento_id_obj.create(motivo_talento_id_data_read[0])
        else:
            other_motivo_talento_id.write(motivo_talento_id_data_read[0])
        return other_motivo_talento_id

    @api.multi
    def get_create_language_level_details(self, language_level_ids):
        # language.level.details
        if not language_level_ids:
            return []
        language_level_ids_list = []
        for language_level_id in language_level_ids:
            language_id = self.get_create_language(language_level_id.language_id)
            level_id = self.get_create_hr_competition_level_language(language_level_id.leave_id)
            language_level_ids_list.append((0, 0, {
                'language_id': language_id,
                'level_id': level_id and level_id.id,
            }))
        return language_level_ids_list

    @api.multi
    def get_create_hr_novelty(self, novelty_id):
        other_novelty_id = False
        if not novelty_id:
            return other_novelty_id
        hr_novelty_obj = self.env['hr.novelty']
        res_currency_obj = self.env['res.currency']
        domain = [['name', '=', novelty_id.name], ['start_date', '=', novelty_id.start_date]]
        if novelty_id.employee_id:
            domain += [['employee_id.name', '=', novelty_id.employee_id.name]]
        if novelty_id.event_id:
            domain += [['event_id.name', '=', novelty_id.event_id.name]]
        if novelty_id.type_id:
            domain += [['type_id.name', '=', novelty_id.type_id.name]]
        if novelty_id.subtype_id:
            domain += [['subtype_id.name', '=', novelty_id.subtype_id.name]]
        other_novelty_id = hr_novelty_obj.search(domain, limit=1)
        if not other_novelty_id:
            novelty_id_data_read = novelty_id.read(['Fix_wage_assing', 'amount', 'approved_date',
                'approved_ip_date', 'approved_ip_from', 'approved_location', 'confidential', 'date', 'description',
                'end_business_day', 'end_date', 'file_name', 'h_e_procedimiento', 'hiring_type',  'identification_id',
                'increase_salary', 'ip_from', 'is_arl', 'is_eps', 'leave_message', 'location', 'name',
                'observation_increase', 'observation_recruitment', 'project_type', 'reject_reason', 'start_date',
                'start_date_period', 'state', 'support_attachment_url', 'support_name', 'support_size', 'total_days',
                'total_fix_hours', 'total_horas_fijas', 'unit_half', 'wage_assign'])

            approved_by = self.get_create_res_users(novelty_id.approved_by)
            bank_account_id = self.get_create_bank_account(novelty_id.bank_account_id)
            contact_id = self.get_create_partner(novelty_id.contact_id)
            employee_id = self.get_create_employee(novelty_id.employee_id)
            contract_id = self.get_create_contract_id(employee_id, novelty_id.contract_id)
            contract_terminated_id = self.get_create_hr_contract_completion(novelty_id.contract_terminated_id)
            currency_id = res_currency_obj.search([('name', '=', novelty_id.currency_id.name)], limit=1)

            deduction_employee_id = self.get_create_hr_deduction_rf_employee(novelty_id.deduction_employee_id)
            event_id = self.get_create_hr_novelty_event(novelty_id.event_id)
            experience_id = self.get_create_hr_experience_time(novelty_id.experience_id)
            hr_job_id = self.get_create_hr_job(novelty_id.hr_job_id)
            leave_code_id = self.get_create_hr_leave_code_id(novelty_id.leave_code_id)
            leave_id = self.get_create_hr_leave(novelty_id.leave_id)
            motivo_nomina_id = self.hr_contract_completion_withdrawal_reason_id(novelty_id.motivo_nomina_id)
            motivo_talento_id = self.get_create_motivo_talento_id(novelty_id.motivo_talento_id)
            partner_id = self.get_create_partner(novelty_id.partner_id)
            reason_talent_id = self.hr_contract_completion_withdrawal_reason_id(novelty_id.reason_talent_id)
            recruitment_reason_id = self.get_create_recruitment_reason_id(novelty_id.recruitment_reason_id)
            relationship_id = self.get_create_family_rel(novelty_id.relationship_id)
            responsible_id = self.get_create_employee(novelty_id.responsible_id)
            subtype_id  = self.get_create_hr_novelty_event_type_subtype(novelty_id.subtype_id)
            type_id = self.get_create_hr_novelty_type(novelty_id.type_id)
            work_group_id = self.get_create_work_group(novelty_id.work_group_id)
            language_level_ids = self.get_create_language_level_details(novelty_id.language_level_ids)
            novelty_id_data_read[0].update({
                'approved_by': approved_by and approved_by.id,
                'bank_account_id': bank_account_id and bank_account_id.id,
                'contact_id': contact_id and contact_id.id,
                'contract_id': contract_id and contract_id.id,
                'contract_terminated_id': contract_terminated_id and contract_terminated_id.id,
                'currency_id': currency_id and currency_id.id,
                'deduction_employee_id': deduction_employee_id and deduction_employee_id[0],
                'employee_id': employee_id and employee_id.id,
                'event_id': event_id and event_id.id,
                'experience_id': experience_id and experience_id.id,
                'hr_job_id': hr_job_id and hr_job_id.id,
                'leave_code_id': leave_code_id and leave_code_id.id,
                'leave_id': leave_id and leave_id.id,
                'motivo_nomina_id': motivo_nomina_id and motivo_nomina_id.id,
                'motivo_talento_id': motivo_talento_id and motivo_talento_id.id,
                'partner_id': partner_id and partner_id.id,
                'reason_talent_id': reason_talent_id and reason_talent_id.id,
                'recruitment_reason_id': recruitment_reason_id and recruitment_reason_id.id,
                'relationship_id': relationship_id and relationship_id.id,
                'responsible_id': responsible_id and responsible_id.id,
                'subtype_id': subtype_id and subtype_id.id,
                'type_id': type_id and type_id.id,
                'work_group_id': work_group_id and work_group_id.id,
                'language_level_ids': language_level_ids,

                })
            state = False
            if novelty_id_data_read[0].get('state') == 'approved':
                novelty_id_data_read[0].update({'state': 'draft'})
                state = 'approved'

            other_novelty_id = hr_novelty_obj.with_context({'transfer': True}).create(novelty_id_data_read[0])
            if state:
                other_novelty_id.state = state
            other_novelty_id.name = novelty_id.name
        # else:
        #     other_novelty_id.write(novelty_id_data_read[0])
        return other_novelty_id.id

    @api.multi
    def get_create_hr_contract_completion(self, contract_completion_id):
        other_contract_completion_id = False
        if not contract_completion_id:
            return other_contract_completion_id
        hr_contract_completion_obj = self.env['hr.contract.completion']
        other_contract_completion_id = hr_contract_completion_obj.search([
            ('name', '=', contract_completion_id.name),
            ('employee_id.name', '=', contract_completion_id.employee_id.name),
            ('employee_id.work_email', '=', contract_completion_id.employee_id.work_email),
            ('contract_id.name', '=', contract_completion_id.contract_id.name)
            ], limit=1)

        employee_id = self.get_create_employee(contract_completion_id.employee_id)
        contract_id = self.get_create_contract_id(employee_id, contract_completion_id.contract_id)

        contract_completion_id_data_read = contract_completion_id.read([
            'state', 'no_debts_proof', 'unjustified', 'no_debts_proof_filename', 'date', 'reverse_reason'])

        novelty_id = self.get_create_hr_novelty(contract_completion_id.novelty_id)
        withdrawal_reason_id = self.hr_contract_completion_withdrawal_reason_id(contract_completion_id.withdrawal_reason_id)

        contract_completion_id_data_read[0].update({
            'contract_id': contract_id and contract_id.id,
            'employee_id': employee_id and employee_id.id,
            'novelty_id': novelty_id and novelty_id.id,
            'withdrawal_reason_id': withdrawal_reason_id and withdrawal_reason_id.id,

            })
        if not other_contract_completion_id:
            other_contract_completion_id = hr_contract_completion_obj.create(contract_completion_id_data_read[0])
        else:
            other_contract_completion_id.write(contract_completion_id_data_read[0])
        return other_contract_completion_id.id

    @api.multi
    def get_create_account_type(self, user_type_id):
        other_user_type_id = False
        if not user_type_id:
            return other_user_type_id
        user_type_id_obj = self.env['account.account.type']
        other_user_type_id = user_type_id_obj.search([('name', '=', user_type_id.name)], limit=1)
        user_type_id_data_read = user_type_id.read(['include_initial_balance', 'name', 'internal_group', 'type', 'note'])
        if not other_user_type_id:
            other_user_type_id = user_type_id_obj.sudo().create(user_type_id_data_read[0])
        else:
            other_user_type_id.sudo().write(user_type_id_data_read[0])
        return other_user_type_id

    @api.multi
    def get_create_account_id(self, account_id):
        other_account_id = False
        if not account_id:
            return other_account_id
        account_id_obj = self.env['account.account']
        other_account_code_id = account_id_obj.search([('code', '=', account_id.code), ('company_id', '=', account_id.company_id.id)], limit=1)
        if other_account_code_id:
            return other_account_code_id

        other_account_id = account_id_obj.search([('name', '=', account_id.name)], limit=1)

        # account_id_normal_fields = ['deprecated', 'is_payroll', 'reconcile', 'last_time_entries_checked', 
        #     'code', 'name', 'opening_credit', 'opening_debit', 'internal_group', 'note']
        # account_id_data_read = account_id.read(account_id_normal_fields)
        # if not other_account_id:
        #     account_id_data_read = account_id.read(['name', 'code'])
        #     currency_id = self.env['res.currency'].search([('name', '=', account_id.currency_id.name)], limit=1)
        #     user_type_id = self.get_create_account_type(account_id.user_type_id)
        #     account_id_data_read[0].update({
        #         'currency_id': currency_id and currency_id.id,
        #         'user_type_id': user_type_id and user_type_id.id
        #         })
        #     other_account_id = account_id_obj.sudo().create(account_id_data_read[0])
        return other_account_id

    @api.multi
    def get_create_ir_sequence_date_range(self, ir_sequence_id, main_ir_sequence_id):
        other_ir_sequence_id = False
        if not ir_sequence_id:
            return other_ir_sequence_id
        ir_sequence_id_obj = self.env['ir.sequence.date_range']
        ir_sequence_id_data_read = ir_sequence_id.read(['date_from', 'date_to', 'number_next', 'number_next_actual'])
        ir_sequence_id_data_read[0].update({'sequence_id': main_ir_sequence_id.id})
        other_ir_sequence_id = ir_sequence_id_obj.create(ir_sequence_id_data_read[0])
        return other_ir_sequence_id

    @api.multi
    def get_create_ir_sequence(self, ir_sequence_id):
        other_ir_sequence_id = False
        if not ir_sequence_id:
            return other_ir_sequence_id
        ir_sequence_id_obj = self.env['ir.sequence']
        other_ir_sequence_id = ir_sequence_id_obj.search([('name', '=', ir_sequence_id.name), ('code', '=', ir_sequence_id.code)], limit=1)
        if not other_ir_sequence_id:
            ir_sequence_id_data_read = ir_sequence_id.read(['active', 'use_date_range', 'code', 'name', 'prefix', 'suffix',
                'number_increment', 'number_next', 'number_next_actual', 'padding', 'implementation'])
            other_ir_sequence_id = ir_sequence_id_obj.create(ir_sequence_id_data_read[0])

        for date_range_id in ir_sequence_id.date_range_ids:
            new_date_range_id = self.get_create_ir_sequence_date_range(date_range_id, other_ir_sequence_id)

        return other_ir_sequence_id

    @api.multi
    def get_create_journal_id(self, journal_id):
        other_journal_id = False
        if not journal_id:
            return other_journal_id
        journal_id_obj = self.env['account.journal'].search([('name', '=', journal_id.name)])
        other_journal_id = journal_id_obj.search([('name', '=', journal_id.name)], limit=1)

        if not other_journal_id:
            journal_id_normal_fields = ['active', 'at_least_one_inbound', 'at_least_one_outbound', 'bank_statements_source',
            'code', 'color', 'group_invoice_lines', 'is_payroll', 'name', 'post_at_bank_rec', 'refund_sequence',
            'sequence', 'show_on_dashboard', 'type', 'update_posted']

            journal_id_data_read = journal_id.read(journal_id_normal_fields)

            bank_account_id = self.get_create_bank_account(journal_id.bank_account_id)
            bank_id = self.get_create_bank(journal_id.bank_id)
            currency_id = self.env['res.currency'].search([('name', '=', journal_id.currency_id.name)], limit=1)
            default_credit_account_id = self.get_create_account_id(journal_id.default_credit_account_id)
            default_debit_account_id = self.get_create_account_id(journal_id.default_debit_account_id)
            loss_account_id = self.get_create_account_id(journal_id.loss_account_id)
            profit_account_id = self.get_create_account_id(journal_id.profit_account_id)
            refund_sequence_id = self.get_create_ir_sequence(journal_id.refund_sequence_id)
            sequence_id = self.get_create_ir_sequence(journal_id.sequence_id)
            journal_id_data_read[0].update({
                'bank_account_id': bank_account_id and bank_account_id.id,
                'bank_id': bank_id and bank_id.id,
                'currency_id': currency_id and currency_id.id,
                'default_credit_account_id': default_credit_account_id and default_credit_account_id.id,
                'default_debit_account_id': default_debit_account_id and default_debit_account_id.id,
                'loss_account_id': loss_account_id and loss_account_id.id,
                'profit_account_id': profit_account_id and profit_account_id.id,
                'refund_sequence_id': refund_sequence_id and refund_sequence_id.id,
                'sequence_id': sequence_id and sequence_id.id,
                })
            other_journal_id = journal_id_obj.create(journal_id_data_read[0])
        # else:
        #     other_journal_id.write(journal_id_data_read[0])
        return other_journal_id

    @api.multi
    def get_create_payslip_run_id(self, payslip_run_id):
        other_payslip_run_id = False
        if not payslip_run_id:
            return other_payslip_run_id
        payslip_run_id_obj = self.env['hr.payslip.run']
        other_payslip_run_id = payslip_run_id_obj.search([('name', '=', payslip_run_id.name)], limit=1)

        payslip_normal_fields = ['credit_note', 'pay_annual', 'pay_biannual', 'name', 'date_end', 'date_start', 'state', 'result_process']
        payslip_run_id_data_read = payslip_run_id.read(payslip_normal_fields)

        rule_id_list = []
        for rule_id in payslip_run_id.rule_ids:
            new_rule_id = self.get_create_salary_rule(rule_id, False)
            rule_id_list.append(new_rule_id.id)

        journal_id = self.get_create_journal_id(payslip_run_id.journal_id)

        payslip_run_id_data_read[0].update({
            'rule_ids': [(6, 0, rule_id_list)],
            'journal_id': journal_id and journal_id.id,
            })

        if not other_payslip_run_id:
            other_payslip_run_id = payslip_run_id_obj.create(payslip_run_id_data_read[0])
        else:
            other_payslip_run_id.write(payslip_run_id_data_read[0])
        return other_payslip_run_id

    @api.multi
    def get_create_hr_rule_input(self, hr_rule_input_id):
        other_hr_rule_input_id = False
        if not hr_rule_input_id:
            return other_hr_rule_input_id
        hr_rule_input_id_obj = self.env['hr.rule.input']
        other_hr_rule_input_id = hr_rule_input_id_obj.search([('name', '=', hr_rule_input_id.name)], limit=1)
        hr_rule_input_id_data_read = hr_rule_input_id.read(['name', 'code'])
        input_id = self.get_create_salary_rule(hr_rule_input_id.input_id, False)
        hr_rule_input_id_data_read[0].update({
            'input_id': input_id and input_id.id,
            })
        if not other_hr_rule_input_id:
            other_hr_rule_input_id = hr_rule_input_id_data_read.create(hr_rule_input_id_data_read[0])
        else:
            other_hr_rule_input_id.write(hr_rule_input_id_data_read[0])
        return other_hr_rule_input_id

    @api.multi
    def get_create_hr_payslip_line(self, slip_id, employee_id, line_ids):
        _logger.info("get_create_hr_payslip_line==%s=%s=%s=>", slip_id, employee_id, line_ids)
        if not line_ids:
            return []
        hr_payslip_line_obj = self.env['hr.payslip.line']
        hr_payslip_line_list = []
        payslip_normal_fields = ['accumulate', 'active', 'amount', 'amount_fix', 'amount_percentage',
        'amount_percentage_base', 'amount_python_compute', 'amount_select', 'appears_on_payslip',
        'asigned_base', 'autocomplete_flex', 'base', 'calculate_base', 'code', 'code_sara',
        'condition_python', 'condition_range', 'condition_range_max', 'condition_range_min',
        'condition_select', 'create_date', 'fixed', 'id', 'is_flex', 'name', 'note', 'print_payslip',
        'projection_exempt', 'quantity', 'rate', 'sequence', 'total', 'total_cost', 'value', 'work_days_value']
        count = 0
        for line_id in line_ids:
            _logger.info("line_id==%s=>", line_id)
            count += 1
            pay_slip_id_data_read = line_id.read(payslip_normal_fields)
            category_id = self.get_create_salary_rule_category(line_id.category_id)
            contract_id = self.get_create_contract_id(employee_id, line_id.contract_id)
            parent_rule_id = self.get_create_salary_rule(line_id.parent_rule_id, False)
            prepaid_medicine_id = self.get_create_partner(line_id.prepaid_medicine_id)
            register_id = self.get_create_hr_contribution_register(line_id.register_id)
            salary_rule_id = self.get_create_salary_rule(line_id.salary_rule_id, False)
            child_ids_list = []
            for child_id in line_id.child_ids:
                _logger.info("child_id ===%s=>", child_id)
                new_salary_rule_id = self.get_create_salary_rule(child_id, False)
                child_ids_list.append(new_salary_rule_id.id)

            input_ids_list = []
            for input_id in line_id.input_ids:
                _logger.info("input_id===%s=>", input_id)
                new_input_id = self.get_create_hr_rule_input(input_id)
                input_ids_list.append(new_input_id.id)

            pay_slip_id_data_read[0].update({
                'category_id': category_id and category_id.id,
                'slip_id': slip_id and slip_id.id,
                'contract_id': contract_id and contract_id.id,
                'employee_id': slip_id.employee_id and slip_id.employee_id.id,
                'parent_rule_id': parent_rule_id and parent_rule_id.id,
                'prepaid_medicine_id': prepaid_medicine_id and prepaid_medicine_id.id,
                'register_id': register_id and register_id.id,
                'salary_rule_id': salary_rule_id and salary_rule_id.id,
                'child_ids': [(6, 0, child_ids_list)],
                'input_ids': [(6, 0, input_ids_list)],
                })
            pay_line_id = hr_payslip_line_obj.create(pay_slip_id_data_read[0])
            hr_payslip_line_list.append(pay_line_id.id)
        return hr_payslip_line_list

    @api.multi
    def get_create_hr_payslip_deductions_rf(self, new_pay_slip_id, ps_deductions_id):
        _logger.info("get_create_hr_payslip_deductions_rf==%s=%s=>", new_pay_slip_id, ps_deductions_id)
        other_ps_deductions_id = False
        if not ps_deductions_id:
            return other_ps_deductions_id
        ps_deductions_id_obj = self.env['hr.payslip.deductions.rf']
        ps_deductions_id_data_read = ps_deductions_id.read(['value_final', 'value_reference', 'sequence'])

        hr_deduction_type_id = self.get_create_hr_deduction_type_rf(ps_deductions_id.hr_deduction_type_id)
        hr_deductions_rf_employee_id = self.get_create_hr_deduction_rf_employee(ps_deductions_id.hr_deductions_rf_employee_id)
        ps_deductions_id_data_read[0].update({
            'hr_deduction_type_id': hr_deduction_type_id and hr_deduction_type_id.id,
            'hr_deductions_rf_employee_id': hr_deductions_rf_employee_id and hr_deductions_rf_employee_id[0],
            'hr_payslip_id': new_pay_slip_id and new_pay_slip_id.id,
            })
        other_ps_deductions_id = ps_deductions_id_obj.create(ps_deductions_id_data_read[0])
        return other_ps_deductions_id

    @api.multi
    def get_create_hr_payslip_input_not_rf(self, new_pay_slip_id, ps_input_no_rf_id):
        _logger.info("get_create_hr_payslip_input_not_rf==%s=%s=>", new_pay_slip_id, ps_input_no_rf_id)
        other_ps_input_no_rf_id = False
        if not ps_input_no_rf_id:
            return other_ps_input_no_rf_id
        ps_input_no_rf_id_obj = self.env['hr.payslip.input.not.rf']
        ps_input_no_rf_id_data_read = ps_input_no_rf_id.read(['name', 'value_final', 'sequence'])
        rule_id = self.get_create_salary_rule(ps_input_no_rf_id.rule_id, False)
        ps_input_no_rf_id_data_read[0].update({
            'rule_id': rule_id and rule_id.id,
            'hr_payslip_id': new_pay_slip_id and new_pay_slip_id.id,
            })
        other_ps_input_no_rf_id = ps_input_no_rf_id_obj.create(ps_input_no_rf_id_data_read[0])
        return other_ps_input_no_rf_id

    @api.multi
    def get_create_hr_payslip_input_rf(self, new_pay_slip_id, ps_input_rf_id):
        _logger.info("get_create_hr_payslip_input_rf==%s=%s=>", new_pay_slip_id, ps_input_rf_id)
        other_ps_input_rf_id = False
        if not ps_input_rf_id:
            return other_ps_input_rf_id
        ps_input_rf_id_obj = self.env['hr.payslip.input.rf']
        ps_input_rf_id_data_read = ps_input_rf_id.read(['name', 'value_final', 'sequence'])
        rule_id = self.get_create_salary_rule(ps_input_rf_id.rule_id, False)
        ps_input_rf_id_data_read[0].update({
            'rule_id': rule_id and rule_id.id,
            'hr_payslip_id': new_pay_slip_id and new_pay_slip_id.id,
            })
        other_ps_input_rf_id = ps_input_rf_id_obj.create(ps_input_rf_id_data_read[0])
        return other_ps_input_rf_id

    @api.multi
    def get_create_hr_payslip_worked_days(self, new_pay_slip_id, worked_days_line_id):
        _logger.info("get_create_hr_payslip_worked_days==%s=%s=>", new_pay_slip_id, worked_days_line_id)
        other_worked_days_line_id = False
        if not worked_days_line_id:
            return other_worked_days_line_id
        worked_days_line_id_obj = self.env['hr.payslip.worked_days']
        worked_days_line_id_data_read = worked_days_line_id.read(['name', 'code', 'sequence', 'number_of_days', 'number_of_hours'])
        employee_id = self.get_create_employee(worked_days_line_id.employee_id)
        contract_id = self.get_create_contract_id(employee_id, worked_days_line_id.contract_id)
        worked_days_line_id_data_read[0].update({
            'contract_id': contract_id and contract_id.id,
            'employee_id': employee_id and employee_id.id,
            'payslip_id': new_pay_slip_id and new_pay_slip_id.id,
            })
        other_worked_days_line_id = worked_days_line_id_obj.create(worked_days_line_id_data_read[0])
        return other_worked_days_line_id

    @api.multi
    def get_create_hr_payslip(self, employee_id, pay_slip_id, check=True):
        other_pay_slip_id = False
        if not pay_slip_id:
            return other_pay_slip_id
        hr_payslip_obj = self.env['hr.payslip']

        domain = [('name', '=', pay_slip_id.name), ('employee_id.name', '=', pay_slip_id.employee_id.name), ('struct_id.name', '=', pay_slip_id.struct_id.name)]
        if pay_slip_id.date_from:
            domain += [('date_from', '=', pay_slip_id.date_from)]
        if pay_slip_id.date_to:
            domain += [('date_to', '=', pay_slip_id.date_to)]
        if pay_slip_id.contract_id:
            domain += [('contract_id.name', '=', pay_slip_id.contract_id.name), ('contract_id.state', '=', pay_slip_id.contract_id.state),('contract_id.date_start', '=', pay_slip_id.contract_id.date_start),('contract_id.wage', '=', pay_slip_id.contract_id.wage)]
        if pay_slip_id.number:
            domain += [('number', '=', pay_slip_id.number)]

        other_pay_slip_id = hr_payslip_obj.search(domain, limit=1)
        if other_pay_slip_id and not check:
            return other_pay_slip_id
        payslip_normal_fields = ['attachment_url', 'base_income_retention',
                                 'base_income_retention_cont', 'calculate_renting_exempt', 'calculate_renting_exempt_cont',
                                 'contract_completion', 'create_date', 'credit_note', 'date', 'date_from', 'date_to',
                                 'identification_id', 'income_represented_uvt', 'income_represented_uvt_cont', 'inputs_rent',
                                 'name', 'note', 'number', 'paid', 'pay_annual', 'pay_biannual',
                                 'percentage_renting_calculate', 'process_status', 'state', 'subtotal_1', 'subtotal_2',
                                 'subtotal_3', 'subtotal_3_cont', 'subtotal_4', 'subtotal_4_cont', 'total', 'total_amount',
                                 'total_deductions_renting', 'total_deductions_renting_cont', 'total_renting_excempt',
                                 'total_retention_income', 'total_retention_income_cont', 'unjustified', 'write_date']
        pay_slip_id_data_read = pay_slip_id.read(payslip_normal_fields)

        rule_id_list = []
        for rule_id in pay_slip_id.rule_ids:
            new_rule_id = self.get_create_salary_rule(rule_id, False)
            rule_id_list.append(new_rule_id.id)
        afc_id = self.get_create_partner(pay_slip_id.afc_id)
        arl_id = self.get_create_partner(pay_slip_id.arl_id)
        bank_account_id = self.get_create_bank_account(pay_slip_id.bank_account_id)
        contract_completion_id = self.get_create_hr_contract_completion(pay_slip_id.contract_completion_id)

        contract_id = self.get_create_contract_id(employee_id, pay_slip_id.contract_id)
        eps_id = self.get_create_partner(pay_slip_id.eps_id)
        journal_id = self.get_create_journal_id(pay_slip_id.journal_id)
        payslip_run_id = self.get_create_payslip_run_id(pay_slip_id.payslip_run_id)
        pension_fund_id = self.get_create_partner(pay_slip_id.pension_fund_id)
        prepaid_medicine2_id = self.get_create_partner(pay_slip_id.prepaid_medicine2_id)
        prepaid_medicine_id = self.get_create_partner(pay_slip_id.prepaid_medicine_id)
        struct_id = self.get_create_hr_payroll_structure(pay_slip_id.struct_id, False)
        unemployment_fund_id = self.get_create_partner(pay_slip_id.unemployment_fund_id)
        voluntary_contribution_id = self.get_create_partner(pay_slip_id.voluntary_contribution_id)

        pay_slip_id_data_read[0].update({
            'rule_ids': [(6, 0, rule_id_list)],
            'afc_id': afc_id and afc_id.id,
            'arl_id': arl_id and arl_id.id,
            'bank_account_id': bank_account_id and bank_account_id.id,
            'contract_completion_id': contract_completion_id and contract_completion_id.id,
            'contract_id': contract_id and contract_id.id,
            'employee_id': employee_id and employee_id.id,
            'eps_id': eps_id and eps_id.id,
            'journal_id': journal_id and journal_id.id,
            'payslip_run_id': payslip_run_id and payslip_run_id.id,
            'pension_fund_id': pension_fund_id and pension_fund_id.id,
            'prepaid_medicine2_id': prepaid_medicine2_id and prepaid_medicine2_id.id,
            'prepaid_medicine_id': prepaid_medicine_id and prepaid_medicine_id.id,
            'struct_id': struct_id and struct_id.id,
            'unemployment_fund_id': unemployment_fund_id and unemployment_fund_id.id,
            'voluntary_contribution_id': voluntary_contribution_id and voluntary_contribution_id.id,
        })
        if not other_pay_slip_id:
            other_pay_slip_id = hr_payslip_obj.create(pay_slip_id_data_read[0])

        # details_by_salary_rule_category = self.get_create_hr_payslip_line(other_pay_slip_id, employee_id, pay_slip_id.details_by_salary_rule_category)
        line_ids = self.get_create_hr_payslip_line(other_pay_slip_id, employee_id, pay_slip_id.line_ids)
        other_pay_slip_id.write({
            # 'details_by_salary_rule_category': details_by_salary_rule_category,
            'line_ids': [(6, 0, line_ids)],  # 'line_ids': line_ids,
        })

        for ps_deductions_id in pay_slip_id.ps_deductions_ids:
            other_pay_slip_id.ps_deductions_ids.unlink()
            self.get_create_hr_payslip_deductions_rf(other_pay_slip_id, ps_deductions_id)

        for ps_exempt_income_id in pay_slip_id.ps_exempt_income_ids:
            other_pay_slip_id.ps_exempt_income_ids.unlink()
            self.get_create_hr_payslip_deductions_rf(other_pay_slip_id, ps_exempt_income_id)

        for ps_input_no_rf_id in pay_slip_id.ps_input_no_rf_ids:
            other_pay_slip_id.ps_input_no_rf_ids.unlink()
            self.get_create_hr_payslip_input_not_rf(other_pay_slip_id, ps_input_no_rf_id)

        for ps_input_rf_id in pay_slip_id.ps_input_rf_ids:
            other_pay_slip_id.ps_input_rf_ids.unlink()
            self.get_create_hr_payslip_input_rf(other_pay_slip_id, ps_input_rf_id)

        for ps_renting_additional_id in pay_slip_id.ps_renting_additional_ids:
            other_pay_slip_id.ps_renting_additional_ids.unlink()
            self.get_create_hr_payslip_deductions_rf(other_pay_slip_id, ps_renting_additional_id)

        for worked_days_line_id in pay_slip_id.worked_days_line_ids:
            other_pay_slip_id.worked_days_line_ids.unlink()
            self.get_create_hr_payslip_worked_days(other_pay_slip_id, worked_days_line_id)
        # else:
        #     other_pay_slip_id.write(pay_slip_id_data_read[0])
        # other_pay_slip_id.compute_sheet()
        other_pay_slip_id.action_update_entities()
        return other_pay_slip_id

    @api.multi
    def get_create_hr_employee_acumulate_ids(self, employee_id, hr_employee_acumulate_ids):
        # hr.employee.acumulate
        if not hr_employee_acumulate_ids:
            return []
        hr_employee_acumulate_ids_list = []
        for hr_employee_acumulate_id in hr_employee_acumulate_ids:
            hr_rules_acumulate_id = self.get_create_hr_rules_acumulate(hr_employee_acumulate_id.hr_rules_acumulate_id)
            pay_slip_id = self.get_create_hr_payslip(employee_id, hr_employee_acumulate_id.pay_slip_id, False)
            hr_employee_acumulate_ids_list.append((0, 0, {
                'name': hr_employee_acumulate_id.name,
                'hr_rules_acumulate_id': hr_rules_acumulate_id,
                'total_acumulate': hr_employee_acumulate_id.total_acumulate,
                'pay_slip_id': pay_slip_id and pay_slip_id.id,
            }))
        return hr_employee_acumulate_ids_list

    @api.multi
    def get_create_hr_employee_work_group_ids(self, hr_employee_work_group_ids):
        # hr.employee.work.group
        if not hr_employee_work_group_ids:
            return []
        hr_employee_work_group_ids_list = []
        for hr_employee_work_group_id in hr_employee_work_group_ids:
            work_group_id = self.get_create_work_group(hr_employee_work_group_id.work_group_id)
            hr_employee_work_group_ids_list.append((0, 0, {
                'name': hr_employee_work_group_id.name,
                'secuence': hr_employee_work_group_id.secuence,
                'work_group_id': work_group_id and work_group_id.id,
            }))
        return hr_employee_work_group_ids_list

    @api.multi
    def get_create_conract_type(self, contract_type_id):
        other_contract_type_id = False
        if not contract_type_id:
            return other_contract_type_id
        hr_type_contract_obj = self.env['hr.type.contract']
        other_contract_type_id = hr_type_contract_obj.search([('name', '=', contract_type_id.name)], limit=1)
        contract_type_id_data_read = contract_type_id.read(['active', 'name', 'description'])
        if not other_contract_type_id:
            other_contract_type_id = hr_type_contract_obj.create(contract_type_id_data_read[0])
        else:
            other_contract_type_id.write(contract_type_id_data_read[0])
        return other_contract_type_id

    @api.multi
    def get_create_experience_area_id(self, experience_area_id):
        other_experience_area_id = False
        if not experience_area_id:
            return other_experience_area_id
        hr_experience_area_obj = self.env['hr.experience.area']
        other_experience_area_id = hr_experience_area_obj.search([('name', '=', experience_area_id.name)], limit=1)
        experience_area_id_data_read = experience_area_id.read(['active', 'name', 'description'])
        if not other_experience_area_id:
            other_experience_area_id = hr_experience_area_obj.create(experience_area_id_data_read[0])
        else:
            other_experience_area_id.write(experience_area_id_data_read[0])
        return other_experience_area_id

    @api.multi
    def get_create_ext_job_position_id(self, ext_job_position_id):
        other_ext_job_position_id = False
        if not ext_job_position_id:
            return other_ext_job_position_id
        hr_external_job_position_obj = self.env['hr.external.job.position']
        other_ext_job_position_id = hr_external_job_position_obj.search([('name', '=', ext_job_position_id.name)], limit=1)
        ext_job_position_id_data_read = ext_job_position_id.read(['active', 'name', 'description'])
        if not other_ext_job_position_id:
            other_ext_job_position_id = hr_external_job_position_obj.create(ext_job_position_id_data_read[0])
        else:
            other_ext_job_position_id.write(ext_job_position_id_data_read[0])
        return other_ext_job_position_id

    @api.multi
    def get_create_laboral_experience_ids(self, laboral_experience_ids):
        # hr.cv.laboral.experience
        if not laboral_experience_ids:
            return []
        laboral_experience_ids_list = []
        for laboral_experience_id in laboral_experience_ids:

            contract_type_id = self.get_create_conract_type(laboral_experience_id.contract_type_id)
            country_id = self.get_create_country(laboral_experience_id.country_id)
            state_id = self.get_create_state(laboral_experience_id.state_id)
            experience_area_id = self.get_create_experience_area_id(laboral_experience_id.experience_area_id)
            ext_job_position_id = self.get_create_ext_job_position_id(laboral_experience_id.ext_job_position_id)
            hr_cv_employee_id = self.get_create_hr_cv_employee(laboral_experience_id.hr_cv_employee_id)

            laboral_experience_ids_list.append((0, 0, {
                'active': laboral_experience_id.active,
                'withdrawal_reason': laboral_experience_id.withdrawal_reason,
                'end_date': laboral_experience_id.end_date,
                'start_date': laboral_experience_id.start_date,
                'wage': laboral_experience_id.wage,
                'contract_type_id': contract_type_id and contract_type_id.id,
                'country_id': country_id and country_id.id,
                'experience_area_id': experience_area_id and experience_area_id.id,
                'ext_job_position_id': ext_job_position_id and ext_job_position_id.id,
                'state_id': state_id and state_id.id,
                'hr_cv_employee_id': hr_cv_employee_id and hr_cv_employee_id.id,
            }))
        return laboral_experience_ids_list

    @api.multi
    def get_create_personal_employee_id_type(self, personal_employee_type_id):
        other_personal_employee_type_id = False
        if not personal_employee_type_id:
            return other_personal_employee_type_id
        personal_employee_type_obj = self.env['hr.cv.personal.employee.type']
        other_personal_employee_type_id = personal_employee_type_obj.search([('name', '=', personal_employee_type_id.name)], limit=1)
        personal_employee_type_id_data_read = personal_employee_type_id.read(['active', 'name', 'description'])
        if not other_personal_employee_type_id:
            other_personal_employee_type_id = personal_employee_type_obj.create(personal_employee_type_id_data_read[0])
        else:
            other_personal_employee_type_id.write(personal_employee_type_id_data_read[0])
        return other_personal_employee_type_id

    @api.multi
    def get_create_personal_employee_ids(self, personal_employee_ids):
        # hr.cv.personal.employee
        if not personal_employee_ids:
            return []
        personal_employee_ids_list = []
        for personal_employee_id in personal_employee_ids:

            hr_cv_employee_id = self.get_create_hr_cv_employee(personal_employee_id.hr_cv_employee_id)
            occupation_id = self.get_create_occupation(personal_employee_id.occupation_id)
            partner_id = self.get_create_partner(personal_employee_id.partner_id)
            type_id = self.get_create_personal_employee_id_type(personal_employee_id.type_id)

            personal_employee_ids_list.append((0, 0, {
                'active': personal_employee_id.active,
                'name': personal_employee_id.name,
                'occupation_name': personal_employee_id.occupation_name,
                'gender': personal_employee_id.gender,
                'hr_cv_employee_id': hr_cv_employee_id and hr_cv_employee_id.id,
                'occupation_id': occupation_id and occupation_id.id,
                'partner_id': partner_id and partner_id.id,
                'type_id': type_id and type_id.id,
            }))
        return personal_employee_ids_list

    @api.multi
    def get_create_hr_policy_id(self, policy_id):
        other_policy_id = False
        if not policy_id:
            return other_policy_id
        hr_policy_obj = self.env['hr.policy']
        other_policy_id = hr_policy_obj.search([('name', '=', policy_id.name)], limit=1)
        policy_id_data_read = policy_id.read(['name', 'description'])
        if not other_policy_id:
            other_policy_id = hr_policy_obj.create(policy_id_data_read[0])
        else:
            other_policy_id.write(policy_id_data_read[0])
        return other_policy_id

    @api.multi
    def get_create_policy_ids(self, policy_ids):
        # hr.employee.policy
        if not policy_ids:
            return []
        policy_ids_list = []
        for policy_id in policy_ids:
            # if policy_id.hr_policy_id.policy_for_employee:
            #     continue
            hr_policy_id = self.get_create_hr_policy_id(policy_id.hr_policy_id)
            template_id = self.env['mail.template'].search([('name', '=', policy_id.name)])
            policy_ids_list.append((0, 0, {
                'answer_type': policy_id.answer_type,
                'check_read': policy_id.check_read,
                'date': policy_id.date,
                'description': policy_id.description,
                'name': policy_id.name,
                'hr_policy_id': hr_policy_id and hr_policy_id.id,
                'template_id': template_id and template_id.id,
            }))
        return policy_ids_list

    @api.multi
    def get_create_bank_account(self, bank_account_id):
        other_bank_account_id = False
        if not bank_account_id:
            return other_bank_account_id
        res_partner_bank_obj = self.env['res.partner.bank']
        bank_partner_id = self.get_create_partner(bank_account_id.partner_id)
        other_bank_account_id = res_partner_bank_obj.search([('partner_id.vat', '=', bank_partner_id.vat), ('acc_number', '=', bank_account_id.acc_number)], limit=1)
        if not other_bank_account_id:
            bank_account_data_read = bank_account_id.read(['type', 'acc_number', 'acc_type', 'acc_holder_name'])
            bank_id = self.get_create_bank(bank_account_id.bank_id)
            bank_account_data_read[0].update({
                'partner_id': bank_partner_id and bank_partner_id.id,
                'bank_id': bank_id and bank_id.id,
                })
            other_bank_account_id = res_partner_bank_obj.create(bank_account_data_read[0])
        # else:
        #     other_bank_account_id.write(bank_account_data_read[0])
        return other_bank_account_id

    @api.multi
    def get_create_employee(self, employee_id):
        if not employee_id:
            return False
        employee_obj = self.env['hr.employee']

        domain = [('name', '=', employee_id.name), ('active', 'in', [True, False])]
        if employee_id.work_email:
            domain += [('work_email', '=', employee_id.work_email)]
        new_employee_id = employee_obj.search(domain, limit=1)

        if not new_employee_id:
            employee_normal_fields = ['active', 'additional_note', 'allocation_leaves_count',
                'approval_limit', 'arl_percentage', 'birthday', 'blood_type', 'certificate',
                'children', 'class_llibreta_militar', 'color', 'create_date', 'emergency_contact',
                'emergency_phone', 'entry_date', 'gender', 'google_drive_link', 'id',
                'ident_issuance_date', 'is_dependientes', 'job_title', 'km_home_work',
                'last_update', 'leave_days_count', 'manager', 'marital', 'medic_exam',
                'mobile_phone', 'name', 'notes', 'number_of_llibreta_militar', 'passport_id',
                'permit_expire', 'permit_no', 'place_of_birth', 'profile_image_url',
                'remaining_leaves_count', 'required_restriction', 'response_message',
                'response_time', 'sinid', 'spouse_birthdate', 'spouse_complete_name', 'ssnid',
                'stratum', 'study_field', 'study_school', 'type_of_housing', 'update_info', 'vehicle',
                'visa_expire', 'visa_no', 'withholding_2', 'work_email', 'work_location',
                'work_phone', 'write_date']
            employee_data_read = employee_id.read(employee_normal_fields)
            address_home_id = self.get_create_partner(employee_id.address_home_id)
            address_id = self.get_create_partner(employee_id.address_id)
            afc_id = self.get_create_partner(employee_id.afc_id)
            arl_id = self.get_create_partner(employee_id.arl_id)
            bank_account_id = self.get_create_bank_account(employee_id.bank_account_id)
            country_id = self.get_create_country(employee_id.country_id)
            country_of_birth = self.get_create_country(employee_id.country_of_birth)
            state_of_birth_id = self.get_create_state(employee_id.state_of_birth_id)
            place_of_birth_id = self.get_create_place(employee_id.place_of_birth_id)
            department_id = self.get_create_hr_department(employee_id.department_id)
            eps_id = self.get_create_partner(employee_id.eps_id)
            flex_id = self.get_create_hr_employee_flextime(employee_id.flex_id)
            found_layoffs_id = self.get_create_partner(employee_id.found_layoffs_id)
            function_executed_id = self.get_create_function_executes(employee_id.function_executed_id)
            ident_issuance_city_id = self.get_create_place(employee_id.ident_issuance_city_id)
            job_id = self.get_create_hr_job(employee_id.job_id)

            macro_area_id = self.get_create_macro_area(employee_id.macro_area_id)
            pension_fund_id = self.get_create_partner(employee_id.pension_fund_id)
            unemployment_fund_id = self.get_create_partner(employee_id.unemployment_fund_id)
            prepaid_medicine2_id = self.get_create_partner(employee_id.prepaid_medicine2_id)
            prepaid_medicine_id = self.get_create_partner(employee_id.prepaid_medicine_id)
            resource_id = self.get_create_resource_resource(employee_id.resource_id)
            marital_status_id = self.get_create_hr_marital_status(employee_id.marital_status_id)
            retention_method_id = self.get_create_hr_retention_method_rf(employee_id.retention_method_id)
            # user_id = self.get_create_res_users(employee_id.user_id)
            voluntary_contribution_id = self.get_create_partner(employee_id.voluntary_contribution_id)
            work_group_id = self.get_create_work_group(employee_id.work_group_id)

            academic_studies_ids = self.get_create_hr_cv_academic_studies(employee_id.academic_studies_ids)
            animal_pets_ids = self.get_create_animal_pets(employee_id.animal_pets_ids)
            contact_reference_ids = self.get_create_contact_reference(employee_id.contact_reference_ids)
            deductions_accumulate_ids = self.get_create_deductions_accumulate(employee_id.deductions_accumulate_ids)
            deductions_ids = self.get_create_hr_deduction_rf_employee(employee_id.deductions_ids)
            family_group_ids = self.get_create_family_group(employee_id.family_group_ids)
            hobbies_ids = self.get_create_hobbies(employee_id.hobbies_ids)
            holding_ids = self.get_create_holding_ids(employee_id.holding_ids)
            hr_employee_work_group_ids = self.get_create_hr_employee_work_group_ids(employee_id.hr_employee_work_group_ids)
            laboral_experience_ids =self.get_create_laboral_experience_ids(employee_id.laboral_experience_ids)
            language_ids = self.get_create_language_ids(employee_id.language_ids)
            personal_employee_ids = self.get_create_personal_employee_ids(employee_id.personal_employee_ids)
            sport_ids = self.get_create_sport_ids(employee_id.sport_ids)
            policy_ids = self.get_create_policy_ids(employee_id.policy_ids)

            employee_data_read[0].update({
                'address_home_id': address_home_id and address_home_id.id,
                'address_id': address_id and address_id.id,
                'afc_id': afc_id and afc_id.id,
                'arl_id': arl_id and arl_id.id,
                'bank_account_id': bank_account_id and bank_account_id.id,
                'country_id': country_id and country_id.id,
                'country_of_birth': country_of_birth and country_of_birth.id,
                'state_of_birth_id': state_of_birth_id and state_of_birth_id.id,
                'place_of_birth_id': place_of_birth_id and place_of_birth_id.id,
                'department_id': department_id and department_id.id,
                'eps_id': eps_id and eps_id.id,
                'found_layoffs_id': found_layoffs_id and found_layoffs_id.id,
                'function_executed_id': function_executed_id and function_executed_id.id,
                'ident_issuance_city_id': ident_issuance_city_id and ident_issuance_city_id.id,
                'job_id': job_id and job_id.id,
                'macro_area_id': macro_area_id and macro_area_id.id,
                'marital_status_id': marital_status_id and marital_status_id.id,
                'pension_fund_id': pension_fund_id and pension_fund_id.id,
                'prepaid_medicine2_id': prepaid_medicine2_id and prepaid_medicine2_id.id,
                'prepaid_medicine_id': prepaid_medicine_id and prepaid_medicine_id.id,
                'resource_id': resource_id and resource_id.id,
                'retention_method_id': retention_method_id and retention_method_id.id,
                'unemployment_fund_id': unemployment_fund_id and unemployment_fund_id.id,
                # 'user_id': user_id and user_id.id,
                'voluntary_contribution_id': voluntary_contribution_id and voluntary_contribution_id.id,
                'work_group_id': work_group_id and work_group_id.id,
                'academic_studies_ids': academic_studies_ids,
                'deductions_accumulate_ids': deductions_accumulate_ids,
                'animal_pets_ids': animal_pets_ids,
                'contact_reference_ids': contact_reference_ids,
                'deductions_ids': [(6, 0, deductions_ids)],
                'family_group_ids': family_group_ids,
                'hobbies_ids': hobbies_ids,
                'holding_ids': holding_ids,
                'hr_employee_work_group_ids': hr_employee_work_group_ids,
                'laboral_experience_ids': laboral_experience_ids,
                'language_ids': language_ids,
                'personal_employee_ids': personal_employee_ids,
                'sport_ids': sport_ids,
                'policy_ids': policy_ids,
                })
            new_employee_id = employee_obj.create(employee_data_read[0])
        return new_employee_id

    def check_duplicate_date(self, obj):
        novelty_ids = obj.search([])
        unlink_list = []
        for novelty_id in novelty_ids:
            proper_novelty_list = []
            for novelty_id_employee_id in obj.search([('employee_id', '=', novelty_id.employee_id.id)]):
                my_date = novelty_id_employee_id.start_date.date()
                if str(my_date) not in proper_novelty_list:
                    proper_novelty_list.append(str(my_date))
                else:
                    unlink_list.append(novelty_id_employee_id.id)
        final_list = list(set(unlink_list))

    @api.multi
    def get_create_unity(self, unity_id):
        other_unity_id = False
        if not unity_id:
            return other_unity_id
        other_employee_unity_obj = self.env['hr.employee.unity']
        other_unity_id = other_employee_unity_obj.search([
            ('name', '=', unity_id.name),
            ('code', '=', unity_id.code)], limit=1)
        employee_unity_data_read = unity_id.read(['description', 'name', 'code'])
        if not other_unity_id:
            other_unity_id = other_employee_unity_obj.create(employee_unity_data_read[0])
        else:
            other_unity_id.write(employee_unity_data_read[0])
        return other_unity_id

    @api.multi
    def get_create_zone(self, zone_id):
        other_zone_id = False
        if not zone_id:
            return other_zone_id
        other_employee_zone_obj = self.env['hr.employee.zone']
        other_zone_id = other_employee_zone_obj.search([
            ('name', '=', zone_id.name),
            ('code', '=', zone_id.code)], limit=1)
        employee_zone_data_read = zone_id.read(['description', 'name', 'code'])
        if not other_zone_id:
            other_zone_id = other_employee_zone_obj.create(employee_zone_data_read[0])
        else:
            other_zone_id.write(employee_zone_data_read[0])
        return other_zone_id

    @api.multi
    def get_create_hr_cost_center(self, hr_cost_center_id):
        other_hr_cost_center_id = False
        if not hr_cost_center_id:
            return other_hr_cost_center_id
        other_hr_cost_center_obj = self.env['hr.cost.center']
        other_hr_cost_center_id = other_hr_cost_center_obj.search([
            ('name', '=', hr_cost_center_id.name),
            ('code', '=', hr_cost_center_id.code)], limit=1)
        hr_cost_center_data_read = hr_cost_center_id.read(['description', 'name', 'code', 'name_interface'])
        if not other_hr_cost_center_id:
            other_hr_cost_center_id = other_hr_cost_center_obj.create(hr_cost_center_data_read[0])
        else:
            other_hr_cost_center_id.write(hr_cost_center_data_read[0])
        return other_hr_cost_center_id

    @api.multi
    def get_create_hr_cost_line(self, hr_cost_line_id):
        other_hr_cost_line_id = False
        if not hr_cost_line_id:
            return other_hr_cost_line_id
        other_hr_cost_line_obj = self.env['hr.cost.line']
        other_hr_cost_line_id = other_hr_cost_line_obj.search([
            ('name', '=', hr_cost_line_id.name),
            ('code', '=', hr_cost_line_id.code)], limit=1)
        hr_cost_line_data_read = hr_cost_line_id.read(['description', 'name', 'code', 'name_interface'])
        if not other_hr_cost_line_id:
            other_hr_cost_line_id = other_hr_cost_line_obj.create(hr_cost_line_data_read[0])
        else:
            other_hr_cost_line_id.write(hr_cost_line_data_read[0])
        return other_hr_cost_line_id

    @api.multi
    def action_transfered_step_1(self):
        """Transfer Employee."""
        try:
            for rec in self:
                db_registry = registry(rec.database_origin)
                with db_registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    hr_transfer_employee_id = env['hr.transfer.employee'].search([('id', '=', self.reference)], limit=1)
                    hr_transfer_employee_id.state = 'in_progress'
                    type = hr_transfer_employee_id.employee_multi_or_single
                    if type == 'single':
                        employee_id = hr_transfer_employee_id.employee_id
                        if not employee_id:
                            return False
                        employee_obj = self.env['hr.employee']
                        domain = [('name', '=', employee_id.name), ('active', 'in', [True, False])]
                        if employee_id.work_email:
                            domain += [('work_email', '=', employee_id.work_email)]
                        new_employee_id = employee_obj.search(domain, limit=1)
                        if not new_employee_id:
                            employee_normal_fields = env['ir.model.fields'].search([
                                    ('model_id.model', '=', 'hr.employee'),
                                    ('ttype', 'not in', ['many2one', 'one2many', 'many2many', 'binary']),
                                    ('store', '=', True)]).mapped('name')
                            afc_id = self.get_create_partner(employee_id.afc_id)
                            arl_id = self.get_create_partner(employee_id.arl_id)
                            prepaid_medicine2_id = self.get_create_partner(employee_id.prepaid_medicine2_id)
                            prepaid_medicine_id = self.get_create_partner(employee_id.prepaid_medicine_id)
                            voluntary_contribution_id = self.get_create_partner(employee_id.voluntary_contribution_id)
                            voluntary_contribution2_id = self.get_create_partner(employee_id.voluntary_contribution2_id)
                            pension_fund_id = self.get_create_partner(employee_id.pension_fund_id)
                            unemployment_fund_id = self.get_create_partner(employee_id.unemployment_fund_id)
                            eps_id = self.get_create_partner(employee_id.eps_id)
                            address_home_id = self.get_create_partner(employee_id.address_home_id)
                            department_id = self.get_create_hr_department(employee_id.department_id)
                            macro_area_id = self.get_create_macro_area(employee_id.macro_area_id)
                            work_group_id = self.get_create_work_group(employee_id.work_group_id)
                            function_executed_id = self.get_create_function_executes(employee_id.function_executed_id)
                            policy_ids = self.get_create_policy_ids(employee_id.policy_ids)
                            deductions_ids = self.get_create_hr_deduction_rf_employee(employee_id.deductions_ids)
                            academic_studies_ids = self.get_create_hr_cv_academic_studies(employee_id.academic_studies_ids)
                            family_group_ids = self.get_create_family_group(employee_id.family_group_ids)
                            hobbies_ids = self.get_create_hobbies(employee_id.hobbies_ids)
                            holding_ids = self.get_create_holding_ids(employee_id.holding_ids)
                            language_ids = self.get_create_language_ids(employee_id.language_ids)
                            laboral_experience_ids = self.get_create_laboral_experience_ids(employee_id.laboral_experience_ids)
                            personal_employee_ids = self.get_create_personal_employee_ids(employee_id.personal_employee_ids)
                            contact_reference_ids = self.get_create_contact_reference(employee_id.contact_reference_ids)
                            animal_pets_ids = self.get_create_animal_pets(employee_id.animal_pets_ids)
                            sport_ids = self.get_create_sport_ids(employee_id.sport_ids)
                            deductions_accumulate_ids = self.get_create_deductions_accumulate(
                                employee_id.deductions_accumulate_ids)

                            job_id = self.get_create_hr_job(employee_id.job_id)
                            country_id = self.get_create_country(employee_id.country_id)
                            ident_issuance_city_id = self.get_create_place(employee_id.ident_issuance_city_id)
                            country_of_birth = self.get_create_country(employee_id.country_of_birth)
                            state_of_birth_id = self.get_create_state(employee_id.state_of_birth_id)
                            place_of_birth_id = self.get_create_place(employee_id.place_of_birth_id)
                            unity_id = self.get_create_unity(employee_id.unity_id)
                            zone_id = self.get_create_zone(employee_id.zone_id)
                            hr_cost_center_id = self.get_create_hr_cost_center(
                                employee_id.cost_center_id)
                            hr_cost_line_id = self.get_create_hr_cost_line(
                                employee_id.cost_line_id)
                            retention_method_id = self.get_create_hr_retention_method_rf(
                                employee_id.retention_method_id)
                            bank_account_id = self.get_create_bank_account(employee_id.bank_account_id)

                            employee_data_read = employee_id.read(employee_normal_fields)
                            employee_data_read[0].update({
                                'address_home_id': address_home_id and address_home_id.id,
                                'department_id': department_id and department_id.id,
                                'function_executed_id': function_executed_id and function_executed_id.id,
                                'macro_area_id': macro_area_id and macro_area_id.id,
                                'work_group_id': work_group_id and work_group_id.id,
                                'academic_studies_ids': academic_studies_ids,
                                'animal_pets_ids': animal_pets_ids,
                                'contact_reference_ids': contact_reference_ids,
                                'deductions_ids': [(6, 0, deductions_ids)],
                                'family_group_ids': family_group_ids,
                                'hobbies_ids': hobbies_ids,
                                'holding_ids': holding_ids,
                                'laboral_experience_ids': laboral_experience_ids,
                                'language_ids': language_ids,
                                'personal_employee_ids': personal_employee_ids,
                                'sport_ids': sport_ids,
                                'policy_ids': policy_ids,
                                'deductions_accumulate_ids': deductions_accumulate_ids,
                                'afc_id': afc_id and afc_id.id,
                                'arl_id': arl_id and arl_id.id,
                                'prepaid_medicine2_id': prepaid_medicine2_id and prepaid_medicine2_id.id,
                                'prepaid_medicine_id': prepaid_medicine_id and prepaid_medicine_id.id,
                                'voluntary_contribution_id': voluntary_contribution_id and voluntary_contribution_id.id,
                                'voluntary_contribution2_id': voluntary_contribution2_id and voluntary_contribution2_id.id,
                                'pension_fund_id': pension_fund_id and pension_fund_id.id,
                                'unemployment_fund_id': unemployment_fund_id and unemployment_fund_id.id,
                                'eps_id': eps_id and eps_id.id,
                                'job_id': job_id and job_id.id,
                                'country_id': country_id and country_id.id,
                                'ident_issuance_city_id': ident_issuance_city_id and ident_issuance_city_id.id,
                                'country_of_birth': country_of_birth and country_of_birth.id,
                                'state_of_birth_id': state_of_birth_id and state_of_birth_id.id,
                                'place_of_birth_id': place_of_birth_id and place_of_birth_id.id,
                                'unity_id': unity_id and unity_id.id,
                                'zone_id': zone_id and zone_id.id,
                                'cost_center_id': hr_cost_center_id and hr_cost_center_id.id,
                                'cost_line_id': hr_cost_line_id and hr_cost_line_id.id,
                                'retention_method_id': retention_method_id and retention_method_id.id,
                                'bank_account_id': bank_account_id and bank_account_id.id,
                            })
                            new_employee_id = employee_obj.create(employee_data_read[0])
                        self.write({
                            'employee_id': new_employee_id.id,
                            'employee_ids': [(6, 0, new_employee_id.ids)],
                            'state': 'step1'
                            })
                        hr_transfer_employee_id.state = 'step1'
                        self.message_post(body="Data transfer successfully of Step 1")
                        _logger.info("Data transfer successfully of Step 1")
        except Exception as error:
            self.message_post(body=error)
            _logger.error(error)

    @api.multi
    def action_transfered_step_2(self):
        """Transfer Employee."""
        try:
            db_registry = registry(self.database_origin)
            with db_registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                hr_transfer_employee_id = env['hr.transfer.employee'].search([('id', '=', self.reference)], limit=1)
                hr_leave_allocation_obj = env['hr.leave.allocation']
                hr_novelty_obj = env['hr.novelty']
                hr_leave_obj = env['hr.leave']
                old_db_employee_id = hr_transfer_employee_id.employee_id
                _logger.info("==action_transfered_step_2==1")
                # Bank
                bank_account_id = self.get_create_bank_account(old_db_employee_id.bank_account_id)
                _logger.info("==action_transfered_step_2==2")
                self.employee_id.bank_account_id = bank_account_id and bank_account_id.id

                # Contract
                for old_contract_id in old_db_employee_id.contract_ids:
                    contract_id = self.get_create_contract_id(self.employee_id, old_contract_id)
                    if old_contract_id == self.employee_id.contract_id:
                        self.employee_id.contract_id = contract_id.id
                    father_contract_id = False
                    if old_contract_id.father_contract_id:
                        father_contract_id = self.get_create_contract_id(self.employee_id,
                                                                         old_contract_id.father_contract_id)
                    contract_id.write({'father_contract_id': father_contract_id and father_contract_id.id,
                                       'employee_id': self.employee_id and self.employee_id.id,
                                       })

                # HR Leave Allocation
                for hr_leave_allocation_id in hr_leave_allocation_obj.search([('employee_id', '=', old_db_employee_id.id)]):
                    _logger.info("==hr_leave_allocation_id==%s", hr_leave_allocation_id)
                    self.get_create_hr_leave_allocation(hr_leave_allocation_id)

                # HR Leave
                for hr_leave_id in hr_leave_obj.search([('employee_id', '=', old_db_employee_id.id)]):
                    _logger.info("==hr_leave_id==%s", hr_leave_id)
                    self.get_create_hr_leave(hr_leave_id)

                # HR Novelty
                for hr_novelty_id in hr_novelty_obj.search([('employee_id', '=', old_db_employee_id.id), ('event_id', '!=', False)]):
                    _logger.info("==hr_novelty_id==%s", hr_novelty_id)
                    self.get_create_hr_novelty(hr_novelty_id)

                self.write({
                    'state': 'step2'
                })

                hr_transfer_employee_id.state = 'step2'
                self.message_post(body="Data transfer successfully of Step 2")
                _logger.info("Data transfer successfully of Step 2")
        except Exception as error:
            _logger.error(error)
            self.message_post(body=error)

    @api.multi
    def action_transfered_step_3(self):
        """Transfer Employee."""
        try:
            db_registry = registry(self.database_origin)
            with db_registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                hr_transfer_employee_id = env['hr.transfer.employee'].search([('id', '=', self.reference)], limit=1)
                old_db_employee_id = hr_transfer_employee_id.employee_id

                if self.data == 'final_data':
                    current_date = fields.Date.today()
                    payslip_ids = old_db_employee_id.slip_ids.filtered(
                        lambda p: p.date_from <= current_date <= p.date_to)

                    if not payslip_ids:
                        from dateutil.relativedelta import relativedelta
                        date_start = current_date - relativedelta(months=1)
                        payslip_ids = old_db_employee_id.slip_ids.filtered(
                            lambda p: p.date_from <= date_start <= p.date_to)
                    if not payslip_ids:
                        payslip_ids = old_db_employee_id.slip_ids and old_db_employee_id.slip_ids[-1]
                else:
                    payslip_ids = old_db_employee_id.slip_ids
                    _logger.info("payslip_ids==%s===>", payslip_ids)

                # slip_ids
                for pay_slip_id in payslip_ids:
                    self.get_create_hr_payslip(self.employee_id, pay_slip_id, True)

                # Accumulate
                hea_ids = env['hr.employee.acumulate'].search([('id', 'in', old_db_employee_id.hr_employee_acumulate_ids.ids), ('pay_slip_id', 'in', payslip_ids.ids)])
                _logger.info("acumulate_ids==%s===>", hea_ids)
                if hea_ids:
                    hr_employee_acumulate_ids = self.get_create_hr_employee_acumulate_ids(self.employee_id, hea_ids)
                    self.employee_id.write({'hr_employee_acumulate_ids': hr_employee_acumulate_ids})

                self.write({
                    'state': 'transfered'
                })
                hr_transfer_employee_id.state = 'transfered'
                self.message_post(body="Data transfer successfully of Step 3")
                _logger.info("Data transfer successfully of Step 3")
        except Exception as error:
            self.message_post(body=error)
            _logger.error(error)

    @api.multi
    def action_transfered(self):
        """Transfer Employee."""
        try:
            for rec in self:
                db_registry = registry(rec.database_origin)
                with db_registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    # normal_fields = env['ir.model.fields'].search([
                    #         ('model_id.model', '=', 'hr.leave.allocation'),
                    #         ('ttype', 'not in', ['many2one', 'one2many', 'many2many', 'binary']),
                    #         ('store', '=', True)]).mapped('name')
                    # print("==normal_fields===", normal_fields)
                    hr_transfer_employee_id = env['hr.transfer.employee'].search([('id', '=', self.reference)], limit=1)
                    hr_transfer_employee_id.state = 'in_progress'
                    _logger.info("==Process Start===")
                    employee_id_list = []
                    total_employee_list = []
                    finaltotal_employee_list = []
                    hr_leave_allocation_obj = env['hr.leave.allocation']
                    hr_leave_obj = env['hr.leave']
                    hr_novelty_obj = env['hr.novelty']
                    hr_payroll_structure_obj = env['hr.payroll.structure']
                    hr_salary_rule_obj = env['hr.salary.rule']
                    hr_employee_obj = env['hr.employee']
                    job_obj = env['hr.job']

                    for job_id in job_obj.search([]):
                        self.get_create_hr_job(job_id)

                    for rule_id in hr_salary_rule_obj.search([]):
                        self.get_create_salary_rule(rule_id, True)

                    for struct_id in hr_payroll_structure_obj.search([('parent_id', '=', False)]):
                        self.get_create_hr_payroll_structure(struct_id, True)

                    for struct_id in hr_payroll_structure_obj.search([('parent_id', '!=', False)]):
                        self.get_create_hr_payroll_structure(struct_id, True)

                    # self.check_duplicate_date(hr_novelty_obj)

                    for employee_id in hr_transfer_employee_id.employee_ids:
                        _logger.info("==employee_id==%s, %s", employee_id, employee_id.child_ids)
                        new_employee_id = self.get_create_employee(employee_id)
                        employee_id_list.append(new_employee_id.id)
                        total_employee_list.append(employee_id)

                        if employee_id.coach_id:
                            employee_coach_id = employee_id.coach_id
                            old_employee_id = new_employee_id
                            while employee_coach_id:
                                new_employee_coach_id = self.get_create_employee(employee_coach_id)
                                total_employee_list.append(employee_coach_id)
                                employee_coach_id = employee_coach_id.parent_id or False
                                old_employee_id.write({
                                    'coach_id': new_employee_coach_id.id,
                                    })
                                old_employee_id = new_employee_coach_id

                        if employee_id.parent_id:
                            employee_parent_id = employee_id.parent_id
                            old_employee_id = new_employee_id
                            while employee_parent_id:
                                new_employee_parent_id = self.get_create_employee(employee_parent_id)
                                total_employee_list.append(employee_parent_id)
                                employee_parent_id = employee_parent_id.parent_id or False
                                old_employee_id.write({
                                    'parent_id': new_employee_parent_id.id,
                                    })
                                old_employee_id = new_employee_parent_id

                        # Three Level check ckild
                        for child_id in employee_id.child_ids:
                            new_child_id = self.get_create_employee(child_id)
                            total_employee_list.append(child_id)
                            new_child_id.write({'parent_id': new_employee_id.id})
                            for child_child_id in child_id.child_ids:
                                new_child_child_id = self.get_create_employee(child_child_id)
                                total_employee_list.append(child_child_id)
                                new_child_child_id.write({'parent_id': new_child_id.id})
                                for sub_child in child_child_id.child_ids:
                                    new_sub_child = self.get_create_employee(sub_child)
                                    total_employee_list.append(sub_child)
                                    new_sub_child.write({'parent_id': new_child_child_id.id})

                    _logger.info("\n\n\n\n==total_employee_list==%s",list(set(total_employee_list)))
                    for employee_id_main in list(set(total_employee_list)):
                        employee_id = employee_id_main
                        new_employee_id = self.get_create_employee(employee_id)
                        if employee_id.coach_id:
                            employee_coach_id = employee_id.coach_id
                            old_employee_id = new_employee_id
                            while employee_coach_id:
                                new_employee_coach_id = self.get_create_employee(employee_coach_id)
                                finaltotal_employee_list.append(employee_coach_id)
                                employee_coach_id = employee_coach_id.parent_id or False
                                old_employee_id.write({
                                    'coach_id': new_employee_coach_id.id,
                                    })
                                old_employee_id = new_employee_coach_id

                        if employee_id.parent_id:
                            employee_parent_id = employee_id.parent_id
                            old_employee_id = new_employee_id
                            while employee_parent_id:
                                new_employee_parent_id = self.get_create_employee(employee_parent_id)
                                finaltotal_employee_list.append(employee_parent_id)
                                employee_parent_id = employee_parent_id.parent_id or False
                                old_employee_id.write({
                                    'parent_id': new_employee_parent_id.id,
                                    })
                                old_employee_id = new_employee_parent_id

                        for child_id in employee_id.child_ids:
                            new_child_id = self.get_create_employee(child_id)
                            finaltotal_employee_list.append(child_id)
                            new_child_id.write({'parent_id': new_employee_id.id})
                            for child_child_id in child_id.child_ids:
                                new_child_child_id = self.get_create_employee(child_child_id)
                                finaltotal_employee_list.append(child_child_id)
                                new_child_child_id.write({'parent_id': new_child_id.id})
                                for sub_child in child_child_id.child_ids:
                                    new_sub_child = self.get_create_employee(sub_child)
                                    finaltotal_employee_list.append(sub_child)
                                    new_sub_child.write({'parent_id': new_child_child_id.id})
                        finaltotal_employee_list.extend(total_employee_list)

                    final_total_employee_list = list(set(finaltotal_employee_list))
                    _logger.info("\n\n\n\n==final_total_employee_list==%s",final_total_employee_list)

                    #  for child emplyee
                    for total_employee_id in final_total_employee_list:
                        _logger.info("==total_employee_id==%s",total_employee_id)
                        employee_id = total_employee_id
                        new_employee_id = self.get_create_employee(employee_id)

                        for old_contract_id in employee_id.contract_ids:
                            contract_id = self.get_create_contract_id(new_employee_id, old_contract_id)
                            if old_contract_id == employee_id.contract_id:
                                new_employee_id.contract_id = contract_id.id
                            father_contract_id = False
                            if old_contract_id.father_contract_id:
                                father_contract_id = self.get_create_contract_id(new_employee_id, old_contract_id.father_contract_id)
                            contract_id.write({'father_contract_id': father_contract_id and father_contract_id.id,
                                'employee_id': new_employee_id and new_employee_id.id,
                                })

                        hr_employee_acumulate_ids = self.get_create_hr_employee_acumulate_ids(new_employee_id, employee_id.hr_employee_acumulate_ids)
                        new_employee_id.write({'hr_employee_acumulate_ids': hr_employee_acumulate_ids})

                        # slip_ids
                        for pay_slip_id in employee_id.slip_ids:
                            _logger.info("==pay_slip_id==%s",pay_slip_id)
                            pay_slip_new = self.get_create_hr_payslip(new_employee_id, pay_slip_id, True)
                            # pay_slip_new.compute_sheet()

                        # HR Leave Allocation
                        for hr_leave_allocation_id in hr_leave_allocation_obj.search([('employee_id', '=', employee_id.id)]):
                            _logger.info("==hr_leave_allocation_id==%s",hr_leave_allocation_id)
                            self.get_create_hr_leave_allocation(hr_leave_allocation_id)

                        # HR Leave
                        for hr_leave_id in hr_leave_obj.search([('employee_id', '=', employee_id.id)]):
                            _logger.info("==hr_leave_id==%s",hr_leave_id)
                            self.get_create_hr_leave(hr_leave_id)

                        # HR Novelty
                        for hr_novelty_id in hr_novelty_obj.search([('employee_id', '=', employee_id.id), ('event_id', '!=', False)]):
                            _logger.info("==hr_novelty_id==%s",hr_novelty_id)
                            self.get_create_hr_novelty(hr_novelty_id)

                    hr_ltobject = self.env['hr.leave.type']
                    hr_leave_type_ids = env['hr.leave.type'].search([])
                    for hr_leave_type_id in hr_leave_type_ids:
                        hr_lti = hr_ltobject.search([('name', '=', hr_leave_type_id.name)])
                        if hr_leave_type_id.validity_stop:
                            hr_lti.write({'validity_stop': hr_leave_type_id.validity_stop})
                        if hr_leave_type_id.validity_start:
                            hr_lti.write({'validity_start': hr_leave_type_id.validity_start})

                    self.write({
                        'employee_ids': [(6, 0, employee_id_list)],
                        'state': 'transfered'
                        })
                    hr_transfer_employee_id.state = 'transfered'
                    self.message_post(body="Data transfer successfully")
                    _logger.info("Data transfer successfully")
        except Exception as error:
            self.message_post(body=error)
            _logger.error(error)

    @api.multi
    def action_transfer_datas(self):
        self.state = 'in_progress'
        thread = threading.Thread(target=self.action_transfered_data_call, args=())
        thread.start()

    @api.multi
    def action_transfered_data_call(self):
        try:
            with api.Environment.manage():
                new_cr = self.pool.cursor()
                self = self.with_env(self.env(cr=new_cr))
                self.action_transfered()
                new_cr.commit()
                new_cr.close()
            return {'type': 'ir.actions.act_window_close'}
        except Exception as error:
            _logger.error(error)

    @api.multi
    def action_cancelled(self):
        """Cancelled operation."""
        for rec in self:
            rec.state = 'cancelled'
