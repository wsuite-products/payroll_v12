# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo
from odoo import http
from odoo import api, fields, models, _, registry, SUPERUSER_ID
import threading
import logging
_logger = logging.getLogger(__name__)


class OtherDBAssigndataWizard(models.TransientModel):
    _name = 'other.db.assign.data.wizard'
    _description = 'Other DB Assign Data Wizard'

    @api.multi
    def get_message(self):
        if self.env.context.get("message", False):
            return self.env.context.get("message")
        return False

    message = fields.Text(
        string="Message",
        readonly=True,
        default=get_message)


class AssignBrandWizard(models.TransientModel):
    _name = 'other.db.assign.brand.wizard'
    _description = 'Assign Brand Wizard'

    @api.model
    def default_get(self, fields):
        res = super(AssignBrandWizard, self).default_get(fields)
        active_ids = self._context.get('active_ids')
        multi_brand_ids = self.env['multi.brand'].browse(active_ids)
        res.update({'brand_ids': [(6, 0, multi_brand_ids.ids)]})
        return res

    @api.model
    def _get_db_list(self):
        db_list = http.db_list()
        Databases = {}
        for db in db_list:
            Databases.update({db:db})
        Databases.pop(self._cr.dbname)
        return list(Databases.items())

    #db_name = fields.Selection(_get_db_list, 'Select Database Name')
    db_name = fields.Char('Database Name')
    brand_ids = fields.Many2many('multi.brand', string='Brands')

    @api.multi
    def action_multi_brand_assign_process_both(self):
        message = 'Once this process finish it will give message in log of branch!'
        view_id = self.env.ref('multi_brand.other_db_assign_data_wizard')
        thread = threading.Thread(target=self.assign_process_assets_plan_data, args=())
        thread.start()
        res = {
            'name': _('Information'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'other.db.assign.data.wizard',
            'view_id': view_id and view_id.id,
            'target': 'new',
            'context': {'message': message},
        }
        return res

    @api.multi
    def assign_process_assets_plan_data(self):
        try:
            with api.Environment.manage():
                new_cr = self.pool.cursor()
                self = self.with_env(self.env(cr=new_cr))
                self.action_multi_brand_assign_process_both_1()
                new_cr.commit()
                new_cr.close()
                _logger.info("Asigned Process done successfuly")
            return {'type': 'ir.actions.act_window_close'}
        except Exception as error:
            _logger.info(error)

    @api.multi
    def action_multi_brand_assign_process_both_1(self):
        db_registry = registry(self.db_name)
        current_db_name = self._cr.dbname
        product_template_obj = self.env['product.template']
        crm_lead_type_obj = self.env['crm.lead.type']
        bom_obj = self.env['mrp.bom']
        with db_registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            other_crm_lead_type_obj = env['crm.lead.type']
            other_multi_brand_obj = env['multi.brand']
            other_crm_stage_obj = env['crm.stage']
            other_step_step_obj = env['step.step']
            other_step_stage_obj = env['step.stage']
            other_step_page_obj = env['step.page']
            other_step_page_question_obj = env['step.question']
            other_step_label_obj = env['step.label']
            other_res_users_obj = env['res.users']
            other_res_partner_obj = env['res.partner']
            other_step_page_comment_obj = env['step.page.comment']
            other_res_group_obj = env['res.groups']
            other_res_state_obj = env['res.country.state']
            other_product_category_obj = env['product.category']
            other_ir_model_category_obj = env['ir.module.category']
            other_multi_brand_obj = env['multi.brand']
            other_product_template_obj = env['product.template']
            other_product_product_obj = env['product.product']
            other_product_category_obj = env['product.category']
            other_product_attribute_obj = env['product.attribute']
            other_product_attribute_value_obj = env['product.attribute.value']
            other_product_template_attribute_line_obj = env['product.template.attribute.line']
            other_bom_obj = env['mrp.bom']
            other_res_partner_obj = env['res.partner']
            other_account_tax_obj = env['account.tax']
            other_product_attribute = env['product.attribute']
            other_bom_obj = env['mrp.bom']
            other_mrp_routing_obj = env['mrp.routing']
            other_mrp_routing_workcenter_obj = env['mrp.routing.workcenter']
            other_hr_job_obj = env['hr.job']
            other_mrp_workcenter_obj = env['mrp.workcenter']

            other_hr_department_obj = env['hr.department']
            other_function_executed_obj = env['function.executed']
            other_hr_reason_changed_obj = env['hr.reason.changed']
            other_jca_details_obj = env['jca.details']
            other_macro_area_obj = env['macro.area']
            other_hr_employee_obj = env['hr.employee']
            other_recruitment_reason_obj = env['recruitment.reason']
            other_work_group_obj = env['work.group']

            for current_brand_id in self.brand_ids:
                # Multi Brand
                other_brand_id = other_multi_brand_obj.search([('name', '=', current_brand_id.name)], limit=1)
                if not other_brand_id:
                    brand_vals = current_brand_id.read(['brand_reference', 'description', 'file_name', 'folder_config', 'image_url', 'is_default', 'name', 'provision_complete', 'provision_fail', 'service_agreement'])
                    other_partner_id = False
                    partner_id = current_brand_id.partner_id
                    if partner_id:
                        if partner_id.vat:
                            other_partner_id = other_res_partner_obj.search([('vat', '=', partner_id.vat)], limit=1)
                        if not other_partner_id:
                            other_partner_data_read = partner_id.read(['name', 'mobile', 'email', 'l10n_co_document_type', 'vat'])
                            state_id = False
                            if partner_id.state_id:
                                state_id = other_res_state_obj.search([('name', '=', partner_id.state_id.name)])
                            other_partner_data_read[0].update({'state_id': state_id and state_id.id})
                            other_partner_id = other_res_partner_obj.create(other_partner_data_read[0])
                    brand_vals[0].update({'name': current_brand_id.name, 'partner_id': other_partner_id and other_partner_id.id})
                    other_brand_id = other_multi_brand_obj.create(brand_vals[0])

                crm_lead_type_ids = crm_lead_type_obj.search([('brand_id', '=', current_brand_id.id)])
                for crm_lead_type_id in crm_lead_type_ids:
                    _logger.info("crm_lead_type_id==> %s", crm_lead_type_id)
                    # Product Category
                    categ_ids_list = []
                    for categ_id in crm_lead_type_id.brand_id.categ_ids:
                        other_product_category_id = other_product_category_obj.search([('name', '=', categ_id.name), ('brand_id.name', '=', current_brand_id.name)], limit=1)
                        if not other_product_category_id:
                           category_read_data = categ_id.read(['name', 'media', 'fringe', 'channel', 'no_show', 'quotation_template_category', 'description'])
                           category_read_data[0].update({'brand_id': other_brand_id.id})
                           other_product_category_id = other_product_category_obj.create(category_read_data[0])

                        parent_categ_id = categ_id.parent_id
                        old_parent_id = other_product_category_id
                        while parent_categ_id:
                            new_parent_categ_id = other_product_category_obj.search([('name', '=', parent_categ_id.name), ('brand_id.name', '=', current_brand_id.name)], limit=1)
                            if not new_parent_categ_id:
                               category_read_data = parent_categ_id.read(['name', 'media', 'fringe', 'channel', 'no_show', 'quotation_template_category', 'description'])
                               category_read_data[0].update({'brand_id': other_brand_id.id})
                               new_parent_categ_id = other_product_category_obj.create(category_read_data[0])

                            parent_categ_id = parent_categ_id.parent_id or False
                            old_parent_id.write({
                                'parent_id': new_parent_categ_id.id,
                                'brand_id': other_brand_id.id,
                                })
                            old_parent_id = new_parent_categ_id

                        categ_ids_list.append(other_product_category_id.id)
                    other_brand_id.write({'categ_ids': [(6, 0, categ_ids_list)]})

                    # CRM Lead Type
                    new_parent_id = False
                    if crm_lead_type_id.parent_crm_lead_type:
                        new_parent_id = other_crm_lead_type_obj.search([('name', '=', crm_lead_type_id.parent_crm_lead_type.name), ('brand_id.name', '=', current_brand_id.name)], limit=1)
                        if not new_parent_id:
                            new_parent_read = crm_lead_type_id.parent_crm_lead_type.read(['name', 'description', 'image_url', 'color'])
                            new_parent_read[0].update({'brand_id': other_brand_id.id})
                            new_parent_id = other_crm_lead_type_obj.create(new_parent_read[0])
                    first_parent_id = new_parent_id

                    flow_ids = []
                    for flow_id in crm_lead_type_id.flows_ids:
                        _logger.info("flow_id==> %s", flow_id)
                        # Flow (CRM Stage)
                        # other_flow_id = other_crm_stage_obj.search([('name', '=', flow_id.name), ('brand_id.name', '=', current_brand_id.name)], limit=1)
                        # if not other_flow_id:
                        flow_data_read = flow_id.read(['name', 'fold', 'on_change', 'probability', 'requirements', 'feedback', 'feedback_category',
                            'step_flag', 'feedback_type', 'category_css', 'is_loghour', 'sequence', 'image_url', 'mandatory', 'color', 'approved_by', 'step_id'])
                        other_group_id = False
                        other_step_id = False

                        # Group
                        if flow_id.approved_by and flow_data_read[0].get('approved_by', False):
                            group_name = flow_data_read[0]['approved_by'][1]
                            other_group_id = other_res_group_obj.search([('name', '=', group_name), ('category_id.name', '=', flow_id.approved_by.category_id.name)], limit=1)
                            if not other_group_id:
                                if flow_id.approved_by.category_id:
                                    other_ir_model_category_id = other_ir_model_category_obj.search([('name', '=', flow_id.approved_by.category_id.name)])
                                    if not other_ir_model_category_id:
                                        other_ir_model_category_id = other_ir_model_category_obj.create({'name': flow_id.approved_by.category_id.name})
                                    group_data_read[0].update({'category_id': other_ir_model_category_id.id})
                                group_data_read = flow_id.approved_by.read(['share', 'cost_per_hour', 'name', 'permission_json'])
                                other_group_id = other_res_group_obj.create(group_data_read[0])

                        # Step Step
                        if flow_id.step_id and flow_data_read[0].get('step_id', False):
                            # step_name = flow_data_read[0]['step_id'][1]
                            # other_step_id = other_step_step_obj.search([('title', '=', step_name), ('brand_reference', '=', other_brand_id.id)], limit=1)
                            # if not other_step_id:
                            step_data_read = flow_id.step_id.read(['description', 'designed', 'display_name', 'is_closed', 'quizz_mode', 'sequence',
                                'thank_you_message', 'title', 'users_can_go_back'])
                            stage_id = flow_id.step_id.stage_id
                            other_step_stage_id = other_step_stage_obj.search([('name', '=', stage_id.name)], limit=1)

                            # Step Stage
                            if not other_step_stage_id:
                                step_stage_data_read = stage_id.read(['name', 'sequence', 'closed', 'fold'])
                                other_step_stage_id = other_step_stage_obj.create(step_stage_data_read[0])
                            step_data_read[0].update({'brand_reference': other_brand_id.id and other_brand_id.id, 'stage_id': other_step_stage_id.id})
                            other_step_id = other_step_step_obj.create(step_data_read)

                            # Step Pages
                            for page_id in flow_id.step_id.page_ids:
                                page_data_read = page_id.read(['description','display_name','form_config','is_loghour','sequence','task_id', 'title'])
                                page_data_read[0].update({'step_id': other_step_id.id})
                                other_page_id = other_step_page_obj.create(page_data_read[0])

                                # Step Comments
                                for comment_id in page_id.comment_ids:
                                    comment_data_read = comment_id.read(['comment','file_name','display_name','sequence', 'attachment_url'])
                                    comment_data_read[0].update({'page_id': other_page_id.id, 'step_id': other_step_id.id})
                                    other_user_id = other_res_users_obj.search([('login', '=', comment_id.user_id.login)])
                                    if other_user_id:
                                        comment_data_read[0].update({'user_id': other_user_id.id})
                                    other_step_page_comment_obj.create(comment_data_read[0])

                                # Step Questions
                                for question_id in page_id.question_ids:
                                    question_data_read = question_id.read(['column_nb','comment_count_as_answer','comments_allowed','comments_message', 'constr_error_msg', 'constr_mandatory',
                                        'description','display_mode','display_name','field_config', 'matrix_subtype', 'question', 'sequence', 'type', 'validation_email',
                                        'validation_error_msg','validation_length_max','validation_length_min','validation_max_date', 'validation_max_float_value', 'validation_min_date', 'validation_min_float_value', 'validation_required'])
                                    question_data_read[0].update({'page_id': other_page_id.id, 'step_id': other_step_id.id})
                                    other_page_question_id = other_step_page_question_obj.create(question_data_read[0])

                                    # Step Labels
                                    for labels_id in question_id.labels_ids:
                                        label_data_read = labels_id.read(['display_name','quizz_mark','value','sequence'])
                                        label_data_read[0].update({'question_id': other_page_question_id.id})
                                        other_step_label_obj.create(label_data_read[0])

                                flow_data_read[0].update({'step_id': other_step_id.id})
                            flow_data_read[0].update({'brand_id': other_brand_id.id, 'approved_by': other_group_id and other_group_id.id})
                            other_flow_id = other_crm_stage_obj.create(flow_data_read[0])
                            flow_ids.append(other_flow_id.id)

                    vals = {
                        'name': crm_lead_type_id.name,
                        'description': crm_lead_type_id.description,
                        'image_url': crm_lead_type_id.image_url,
                        'color': crm_lead_type_id.color,
                        'brand_id': other_brand_id.id,
                        'parent_crm_lead_type': first_parent_id and first_parent_id.id,
                        'flows_ids': [(6, 0, flow_ids)],
                    }
                    if not other_crm_lead_type_obj.search([('name', '=', crm_lead_type_id.name), ('brand_id.name', '=', current_brand_id.name)], limit=1):
                        crm_lead_type_created_id= other_crm_lead_type_obj.create(vals)

                categ_ids_list = []
                for categ_id in current_brand_id.categ_ids:

                    # Product Category
                    other_product_category_id = other_product_category_obj.search([('name', '=', categ_id.name), ('brand_id.name', '=', current_brand_id.name)], limit=1)
                    if not other_product_category_id:
                       category_read_data = categ_id.read(['name', 'media', 'fringe', 'channel', 'no_show', 'quotation_template_category', 'description'])
                       category_read_data[0].update({'brand_id': other_brand_id.id})
                       other_product_category_id = other_product_category_obj.create(category_read_data[0])

                    parent_categ_id = categ_id.parent_id
                    old_parent_id = other_product_category_id
                    while parent_categ_id:
                        new_parent_categ_id = other_product_category_obj.search([('name', '=', parent_categ_id.name), ('brand_id.name', '=', current_brand_id.name)], limit=1)
                        if not new_parent_categ_id:
                           category_read_data = parent_categ_id.read(['name', 'media', 'fringe', 'channel', 'no_show', 'quotation_template_category', 'description'])
                           category_read_data[0].update({'brand_id': other_brand_id.id})
                           new_parent_categ_id = other_product_category_obj.create(category_read_data[0])

                        parent_categ_id = parent_categ_id.parent_id or False
                        old_parent_id.write({
                            'parent_id': new_parent_categ_id.id,
                            'brand_id': other_brand_id.id,
                            })
                        old_parent_id = new_parent_categ_id
                    categ_ids_list.append(other_product_category_id.id)

                    # Product Template
                    for template_id in product_template_obj.search([('categ_id', 'child_of', categ_id.ids)]):
                        _logger.info("template_id==> %s", template_id)
                        other_product_template_id = other_product_template_obj.search([('name', '=', template_id.name), ('brand_id.name', '=', current_brand_id.name),('copy_brand_reference', '=', template_id.id)], limit=1)
                        categ_id = False
                        client_id = False
                        if not other_product_template_id:

                            # Product Category
                            categ_id = other_product_category_obj.search([('name', '=', template_id.categ_id.name), ('brand_id.name', '=', current_brand_id.name)], limit=1)
                            if not categ_id:
                               category_read_data = template_id.categ_id.read(['name', 'media', 'fringe', 'channel', 'no_show', 'quotation_template_category', 'description'])
                               category_read_data[0].update({'brand_id': other_brand_id.id})
                               categ_id = other_product_category_obj.create(category_read_data[0])
                            client_id = other_res_partner_obj.search([('name', '=', template_id.client_id.name)], limit=1)

                            # Supplier Taxes
                            supplier_taxes_id_list = []
                            for st_id in template_id.supplier_taxes_id:
                                other_account_tax_id = other_account_tax_obj.search([('name', '=', st_id.name)], limit=1)
                                if not other_account_tax_id:
                                    account_tax_read_data = st_id.read(['name', 'type_tax_use', 'amount_type', 'amount', 'description', 'hide_tax_exigibility', 'include_base_amount', 'price_include', 'sequence', 'tax_exigibility'])
                                    other_account_tax_id = other_account_tax_id.create(account_tax_read_data[0])
                                supplier_taxes_id_list.append(other_account_tax_id.id)

                            # Customer Taxes
                            taxes_id_list = []
                            for st_id in template_id.taxes_id:
                                other_account_tax_id = other_account_tax_obj.search([('name', '=', st_id.name)], limit=1)
                                if not other_account_tax_id:
                                    account_tax_read_data = st_id.read(['name', 'type_tax_use', 'amount_type', 'amount', 'description', 'hide_tax_exigibility', 'include_base_amount', 'price_include', 'sequence', 'tax_exigibility'])
                                    other_account_tax_id = other_account_tax_id.create(account_tax_read_data[0])
                                taxes_id_list.append(other_account_tax_id.id)

                            # Product Template
                            product_template_read_data = template_id.read(['name', 'type', 'wsuite', 'is_default', 'image_url', 'barcode', 'description',
                                'color', 'default_code', 'display_name', 'flow_config_json', 'flow_json', 'is_product_variant', 'list_price',
                                'lst_price', 'price', 'pwi_id', 'task_id'])
                            product_template_read_data[0].update({
                                'brand_id': other_brand_id.id,
                                'categ_id': categ_id and categ_id.id,
                                'client_id': client_id and client_id.id,
                                'copy_brand_reference': template_id.id,
                                'supplier_taxes_id': [(6, 0, supplier_taxes_id_list)],
                                'taxes_id': [(6, 0, taxes_id_list)]
                                })

                            other_product_template_id = other_product_template_obj.create(product_template_read_data[0])

                            # Attributes
                            for attribute in template_id.attribute_line_ids:
                                other_product_attribute_id = other_product_attribute_obj.search([('name', '=', attribute.attribute_id.name)])
                                if not other_product_attribute_id:
                                    product_attribute_data_read = attribute.attribute_id.read(['name', 'type', 'create_variant'])
                                    other_product_attribute_id = other_product_attribute_obj.create(product_attribute_data_read[0])
                                other_product_attribute_value_ids = []
                                for value_id in attribute.value_ids:
                                    other_product_attribute_value_id = other_product_attribute_value_obj.search([('name', '=', value_id.name)])
                                    if not other_product_attribute_value_id:
                                        product_attribute_value_data_read = value_id.read(['name', 'is_custom', 'html_color'])
                                        product_attribute_value_data_read[0].update({'attribute_id': other_product_attribute_id.id})
                                        other_product_attribute_value_id = other_product_attribute_value_obj.create(product_attribute_value_data_read[0])
                                    other_product_attribute_value_ids.append(other_product_attribute_value_id.id)
                                vals = {
                                    'attribute_id': other_product_attribute_id.id,
                                    'value_ids': [(6, 0, other_product_attribute_value_ids)],
                                    'product_tmpl_id': other_product_template_id.id
                                    }
                                other_product_template_attribute_line_obj.create(vals)
                            # other_product_template_id.create_variant_ids()

                        # Product
                        product_ids = self.env['product.product'].search([('product_tmpl_id', '=', template_id.id)])
                        for product_id in product_ids:
                            other_product_variant_id = other_product_product_obj.search([('brand_id.name', '=', current_brand_id.name), ('copy_brand_reference', '=', product_id.id)], limit=1)
                            if not other_product_variant_id:
                                product_variant_read_data = product_id.read([
                                    'name', 'code', 'type', 'wsuite', 'is_default', 'image_url', 'barcode', 'description',
                                    'color', 'default_code', 'display_name', 'flow_config_json', 'flow_json',
                                    'is_product_variant', 'list_price', 'lst_price', 'price', 'pwi_id', 'task_id',
                                    'profit_type', 'profit_percentage', 'direct_cost', 'indirect_cost', 'income',
                                    'product_name', 'estimated_live_date', 'quotation_deadline', 'public_price'])

                                # Supplier Taxes
                                supplier_taxes_id_list = []
                                for st_id in template_id.supplier_taxes_id:
                                    other_account_tax_id = other_account_tax_obj.search([('name', '=', st_id.name)], limit=1)
                                    if not other_account_tax_id:
                                        account_tax_read_data = st_id.read(['name', 'type_tax_use', 'amount_type', 'amount', 'description', 'hide_tax_exigibility', 'include_base_amount', 'price_include', 'sequence', 'tax_exigibility'])
                                        other_account_tax_id = other_account_tax_id.create(account_tax_read_data[0])
                                    supplier_taxes_id_list.append(other_account_tax_id.id)

                                # Customer Taxes
                                taxes_id_list = []
                                for st_id in template_id.taxes_id:
                                    other_account_tax_id = other_account_tax_obj.search([('name', '=', st_id.name)], limit=1)
                                    if not other_account_tax_id:
                                        account_tax_read_data = st_id.read(['name', 'type_tax_use', 'amount_type', 'amount', 'description', 'hide_tax_exigibility', 'include_base_amount', 'price_include', 'sequence', 'tax_exigibility'])
                                        other_account_tax_id = other_account_tax_id.create(account_tax_read_data[0])
                                    taxes_id_list.append(other_account_tax_id.id)

                                attribute_value_names = product_id.attribute_value_ids.mapped('name')
                                other_product_attribute_value_ids = other_product_attribute_value_obj.search([('name', 'in', attribute_value_names)])
                                product_variant_read_data[0].update({
                                    'brand_id': other_brand_id.id,
                                    'categ_id': categ_id and categ_id.id,
                                    'client_id': client_id and client_id.id,
                                    'supplier_taxes_id': [(6, 0, supplier_taxes_id_list)],
                                    'taxes_id': [(6, 0, taxes_id_list)],
                                    'product_tmpl_id': other_product_template_id.id,
                                    'copy_brand_reference': product_id.id,
                                    'attribute_value_ids': [(6, 0, other_product_attribute_value_ids and other_product_attribute_value_ids.ids)],
                                })
                                other_product_varient_id = other_product_product_obj.create(product_variant_read_data[0])

                                unlink_default_product_ids = other_product_product_obj.search([('product_tmpl_id', '=', other_product_template_id.id), ('brand_id', '=', False)])
                                if unlink_default_product_ids:
                                    cr.execute("""delete from product_product WHERE id IN %s""", [tuple(unlink_default_product_ids.ids)])

                                # BOM
                                bom_ids = self.env['mrp.bom'].search([('product_id', '=', product_id.id)])
                                for bom_id in bom_ids:
                                    other_routing_id = False
                                    if bom_id.routing_id:
                                        other_routing_id = other_mrp_routing_obj.create({'name': bom_id.routing_id.name})
                                        for operation_id in bom_id.routing_id.operation_ids:
                                            other_hr_job_id = other_hr_job_obj.search([('name', '=', operation_id.resource_id.name)], limit=1)
                                            resource_id = operation_id.resource_id
                                            if not other_hr_job_id and resource_id:
                                                other_resource_data_read = resource_id.read(['codigo_holding', 'codigo_holding_principal', 'color', 'description',
                                                    'display_name', 'experience', 'fte', 'holding', 'holding_principal', 'hour_value', 'jca_details_type',
                                                    'level', 'name', 'observation', 'requirements', 'salary', 'state'])

                                                other_department_id = False
                                                other_function_executed_id = False
                                                other_group_id = False
                                                other_hr_reason_changed_id = False
                                                other_hr_responsible_id = False
                                                other_jca_details_id = False
                                                other_macro_area_id = False
                                                other_manager_id = False
                                                other_recruitment_reason_id = False
                                                other_work_group_id = False
                                                other_user_id = False

                                                if resource_id.department_id:
                                                   other_department_id = other_hr_department_obj.search([('name', '=', resource_id.department_id.name)], limit=1)

                                                if resource_id.function_executed_id:
                                                   other_function_executed_id = other_function_executed_obj.search([('name', '=', resource_id.function_executed_id.name)], limit=1)

                                                if resource_id.group_id:
                                                   other_group_id = other_res_group_obj.search([('name', '=', resource_id.group_id.name)], limit=1)

                                                if resource_id.hr_reason_changed_id:
                                                   other_hr_reason_changed_id = other_hr_reason_changed_obj.search([('name', '=', resource_id.hr_reason_changed_id.name)], limit=1)

                                                if resource_id.hr_responsible_id:
                                                   other_hr_responsible_id = other_res_users_obj.search([('login', '=', resource_id.hr_responsible_id.login)], limit=1)

                                                if resource_id.jca_details_id:
                                                   other_jca_details_id = other_jca_details_obj.search([('name', '=', resource_id.jca_details_id.name)], limit=1)

                                                if resource_id.macro_area_id:
                                                   other_macro_area_id = other_macro_area_obj.search([('name', '=', resource_id.macro_area_id.name)], limit=1)

                                                if resource_id.manager_id:
                                                   other_manager_id = other_hr_employee_obj.search([('name', '=', resource_id.manager_id.name)], limit=1)

                                                if resource_id.recruitment_reason_id:
                                                   other_recruitment_reason_id = other_recruitment_reason_obj.search([('name', '=', resource_id.recruitment_reason_id.name)], limit=1)

                                                if resource_id.work_group_id:
                                                   other_work_group_id = other_work_group_obj.search([('name', '=', resource_id.work_group_id.name)], limit=1)

                                                if resource_id.user_id:
                                                   user_id = other_res_users_obj.search([('login', '=', resource_id.user_id.login)], limit=1)

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
                                                other_hr_job_id = other_hr_job_obj.create(other_resource_data_read[0])
                                            other_workcenter_id = other_mrp_workcenter_obj.search([('name', '=', operation_id.name)], limit=1)
                                            if not other_workcenter_id:
                                                other_workcenter_id = other_mrp_workcenter_obj.create({'name': operation_id.name})
                                            other_routing_workcenter_data_read = operation_id.read(['batch', 'batch_size', 'display_name', 'is_operational', 'name', 'note', 'sequence', 'task_form_json', 'time_cycle', 'time_cycle_manual', 'time_mode', 'time_mode_batch'])
                                            other_routing_workcenter_data_read[0].update({
                                                'resource_id': other_hr_job_id and other_hr_job_id.id or False,
                                                'routing_id': other_routing_id.id,
                                                'workcenter_id': other_workcenter_id.id
                                                })
                                            other_mrp_routing_workcenter_obj.create(other_routing_workcenter_data_read[0])
                                    other_bom_data_read = bom_id.read(['code', 'display_name', 'product_qty', 'ready_to_produce', 'sequence', 'type'])
                                    other_bom_data_read[0].update({
                                        'brand_id': other_brand_id.id,
                                        'product_id': other_product_varient_id and other_product_varient_id.id,
                                        'product_tmpl_id': other_product_template_id and other_product_template_id.id,
                                        'routing_id': other_routing_id and other_routing_id.id,
                                        })
                                    other_bom_obj.create(other_bom_data_read[0])
                other_brand_id.write({'categ_ids': [(6, 0, categ_ids_list)]})
                body = (_('Data Copy successfully from %s to %s database!') % (current_db_name, self.db_name))
                current_brand_id.message_post(body=body)
                _logger.info("Process Completed....")
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
