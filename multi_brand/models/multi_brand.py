# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _, registry, SUPERUSER_ID
from odoo.addons import decimal_precision as dp
import threading
import logging
_logger = logging.getLogger(__name__)


class MultiBrand(models.Model):
    _name = "multi.brand"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Multi Brand'

    name = fields.Char('Name', required=True)
    description = fields.Text('Description')
    file_name = fields.Char("File Name")
    image = fields.Binary('image')
    product_suite_ids = fields.Many2many(
        'product.product', string='Product Wsuite')
    categ_ids = fields.Many2many(
        'product.category',
        string='Product Categories', copy=False)
    image_url = fields.Char('Image URL')
    brand_reference = fields.Char('Brand Reference')
    is_default = fields.Boolean('Is Default')
    provision_complete = fields.Boolean('Provision Complete')
    provision_fail = fields.Boolean('Provision Fail')
    folder_config = fields.Text('Folder Config')
    advertising_services_percentage = fields.Float('Advertising Services Percentage')
    quotation_config = fields.Text('Quotation Config')
    active = fields.Boolean('Active', default=True)
    use_default_brand_asset = fields.Boolean('Use Default Brand Asset?')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        domain = []
        args = args or []
        if self.env.context.get('partner_id', False):
            partner_id = self.env['res.partner'].browse(
                self.env.context['partner_id'])
            if partner_id.multi_brand_ids:
                domain = [('id', '=',
                           partner_id.multi_brand_ids.ids)]
        multi_brand = self.search(domain + args, limit=limit)
        return multi_brand.name_get()

    @api.model
    def create(self, vals):
        """Add binary field in the attachment."""
        res = super(MultiBrand, self).create(vals)
        if vals.get('image', '') and vals.get('file_name', ''):
            self.env['ir.attachment'].create(dict(
                name=vals.get('file_name', ''),
                datas_fname=vals.get('file_name', ''),
                datas=vals.get('image', ''),
                res_model='multi.brand',
                type='binary',
                res_id=res.id
            ))
        return res

    @api.multi
    def write(self, vals):
        """Add binary field in the attachment."""
        if vals.get('image', ''):
            if self.file_name == vals.get('file_name', ''):
                self.env['ir.attachment'].search([
                    ('res_model', '=', 'multi.brand'),
                    ('res_id', '=', self.id),
                    ('name', '=', self.file_name)], limit=1).write(
                    {'datas': vals.get('image', '')})
            if self.file_name != vals.get('file_name', ''):
                self.env['ir.attachment'].search([
                    ('res_model', '=', 'multi.brand'),
                    ('res_id', '=', self.id),
                    ('name', '=', self.file_name)], limit=1).unlink()
                self.env['ir.attachment'].create(dict(
                    name=vals.get('file_name') or self.file_name,
                    datas_fname=vals.get('file_name') or self.file_name,
                    datas=vals.get('image', ''),
                    res_model='multi.brand',
                    type='binary',
                    res_id=self.id
                ))
        return super(MultiBrand, self).write(vals)

    @api.multi
    def delete_data_related_to_brand(self):
        thread = threading.Thread(target=self.action_delete_assets_data, args=())
        thread.start()

    @api.multi
    def action_delete_assets_data(self):
        try:
            with api.Environment.manage():
                new_cr = self.pool.cursor()
                self = self.with_env(self.env(cr=new_cr))
                self.action_delete_assets_plan_data()
                new_cr.commit()
                new_cr.close()
            return {'type': 'ir.actions.act_window_close'}
        except Exception as error:
            _logger.info(error)

    @api.multi
    def action_delete_assets_plan_data(self):
        self.action_multi_brand_delete()
        self.action_multi_brand_delete_plan()

    @api.multi
    def action_multi_brand_delete(self):
        product_template_obj = self.env['product.template']
        bom_obj = self.env['mrp.bom']
        mrp_routing_obj = self.env['mrp.routing']
        product_obj = self.env['product.product']
        categ_obj = self.env['product.category']
        crm_lead_lines_obj = self.env['crm.lead.lines']
        sale_order_line_obj = self.env['sale.order.line']
        purchase_order_line_obj = self.env['purchase.order.line']
        categ_ids = categ_obj.search(['|', ('id', 'in', self.categ_ids.ids), ('brand_id', '=', self.id)])
        for categ_id in categ_ids:
            template_ids = product_template_obj.search(['|', ('categ_id', 'child_of', categ_id.ids), ('brand_id', '=', self.id)])
            for template_id in template_ids:
                product_ids = product_obj.search(['|', ('product_tmpl_id', '=', template_id.id), ('brand_id', '=', self.id)])
                bom_ids = bom_obj.search(['|', '|', ('product_id', 'in', product_ids.ids), ('product_tmpl_id', '=', template_id.id), ('brand_id', '=', self.id)])
                routing_ids = mrp_routing_obj.search([('brand_id', '=', self.id)])
                routing_ids.unlink()
                if bom_ids:
                    self._cr.execute('DELETE FROM mrp_production WHERE bom_id in %s', (tuple(bom_ids.ids),))
                    bom_ids.unlink()
                if product_ids:
                    lead_line_ids = crm_lead_lines_obj.search([('product_id', 'in', product_ids.ids)])
                    lead_ids = lead_line_ids.mapped('crm_lead_id')
                    if lead_ids:
                        _logger.info("lead_ids==> %s", lead_ids)
                        self._cr.execute('DELETE FROM crm_lead WHERE id in %s', (tuple(lead_ids.ids),))

                    sale_order_line_ids = sale_order_line_obj.search([('product_id', 'in', product_ids.ids)])
                    order_ids = sale_order_line_ids.mapped('order_id')
                    if order_ids:
                        _logger.info("order_ids==> %s", order_ids)
                        self._cr.execute('DELETE FROM sale_order WHERE id in %s', (tuple(order_ids.ids),))

                    purchase_order_line_ids = purchase_order_line_obj.search([('product_id', 'in', product_ids.ids)])
                    purchase_order_ids = purchase_order_line_ids.mapped('order_id')
                    if purchase_order_ids:
                        _logger.info("purchase_order_ids==> %s", purchase_order_ids)
                        self._cr.execute('DELETE FROM purchase_order WHERE id in %s', (tuple(purchase_order_ids.ids),))

                    self._cr.execute('DELETE FROM stock_move WHERE product_id in %s', (tuple(product_ids.ids),))
                    self._cr.execute('DELETE FROM mrp_production WHERE product_id in %s', (tuple(product_ids.ids),))
            template_ids.unlink()
        categ_ids.unlink()
        body = (_('Data Deleted successfully related to Assets!'))
        self.message_post(body=body, subject=self.id)
        _logger.info("Data Deleted successfully related to Assets!")
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.multi
    def action_multi_brand_delete_plan(self):
        crm_lead_type_obj = self.env['crm.lead.type']
        crm_lead_type_ids = crm_lead_type_obj.search([('brand_id', '=', self.id)])
        for crm_lead_type_id in crm_lead_type_ids:
            for flow_id in crm_lead_type_id.flows_ids:
                self._cr.execute('DELETE FROM step_user_input WHERE step_id in %s', (tuple(flow_id.step_id.ids),))
                self._cr.execute('DELETE FROM crm_lead WHERE stage_id in %s', (tuple(flow_id.ids),))
                flow_id.step_id.unlink()
                flow_id.unlink()
        crm_lead_type_ids.unlink()
        body = (_('Data Deleted successfully related to Plan!'))
        self.message_post(body=body, subject=self.id)
        _logger.info("Data Deleted successfully related to Plan!")
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.multi
    def copy_brand_data_on_other_database(self, current_database_name=None, target_database_name=None, source_brand_id=None, target_brand_id=None):
        thread = threading.Thread(target=self.assign_process_wplan_other_database_API, args=(current_database_name,target_database_name, source_brand_id, target_brand_id))
        thread.start()

    @api.multi
    def assign_process_wplan_other_database_API(self, current_database_name, target_database_name, source_brand_id, target_brand_id):
        try:
            with api.Environment.manage():
                new_cr = self.pool.cursor()
                self = self.with_env(self.env(cr=new_cr))
                self.action_multi_brand_copy_process_other_database_API(current_database_name, target_database_name, source_brand_id, target_brand_id)
                new_cr.commit()
                new_cr.close()
                _logger.info("Copy Process done successfuly")
            return {'type': 'ir.actions.act_window_close'}
        except Exception as error:
            _logger.info(error)

    @api.multi
    def action_multi_brand_copy_process_other_database_API(self, current_database_name, target_database_name, source_brand_id, target_brand_id):
        db_registry = registry(target_database_name)
        current_db_name = current_database_name
        product_template_obj = self.env['product.template']
        crm_lead_type_obj = self.env['crm.lead.type']
        bom_obj = self.env['mrp.bom']
        search_brand_ids = self.env['multi.brand'].browse([source_brand_id])
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

            for current_brand_id in search_brand_ids:
                # Multi Brand
                # other_brand_id = other_multi_brand_obj.search([('name', '=', current_brand_id.name)], limit=1)
                other_brand_id = other_multi_brand_obj.browse([target_brand_id])
                if not other_brand_id:
                    brand_vals = current_brand_id.read(['brand_reference', 'description', 'file_name',
                        'folder_config', 'image_url', 'is_default', 'name', 'provision_complete', 'provision_fail',
                        'service_agreement','advertising_services_percentage','quotation_config','active'])
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
                        other_product_category_id = other_product_category_obj.search([('name', '=', categ_id.name), ('brand_id', '=', other_brand_id.id)], limit=1)
                        if not other_product_category_id:
                           category_read_data = categ_id.read(['name', 'media', 'fringe', 'channel', 'no_show', 'quotation_template_category', 'description', 'icon'])
                           category_read_data[0].update({'brand_id': other_brand_id.id})
                           other_product_category_id = other_product_category_obj.create(category_read_data[0])

                        parent_categ_id = categ_id.parent_id
                        old_parent_id = other_product_category_id
                        while parent_categ_id:
                            new_parent_categ_id = other_product_category_obj.search([('name', '=', parent_categ_id.name), ('brand_id', '=', other_brand_id.id)], limit=1)
                            if not new_parent_categ_id:
                               category_read_data = parent_categ_id.read(['name', 'media', 'fringe', 'channel', 'no_show', 'quotation_template_category', 'description', 'icon'])
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
                        new_parent_id = other_crm_lead_type_obj.search([('name', '=', crm_lead_type_id.parent_crm_lead_type.name), ('brand_id', '=', other_brand_id.id)], limit=1)
                        if not new_parent_id:
                            new_parent_read = crm_lead_type_id.parent_crm_lead_type.read(['name', 'description', 'image_url', 'color'])
                            new_parent_read[0].update({'brand_id': other_brand_id.id})
                            new_parent_id = other_crm_lead_type_obj.create(new_parent_read[0])
                    first_parent_id = new_parent_id

                    flow_ids = []
                    for flow_id in crm_lead_type_id.flows_ids:
                        _logger.info("flow_id==> %s", flow_id)

                        # Flow (CRM Stage)
                        # other_flow_id = other_crm_stage_obj.search([('name', '=', flow_id.name), ('brand_id', '=', other_brand_id.id)], limit=1)
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
                    if not other_crm_lead_type_obj.search([('name', '=', crm_lead_type_id.name), ('brand_id', '=', other_brand_id.id)], limit=1):
                        crm_lead_type_created_id= other_crm_lead_type_obj.create(vals)

                categ_ids_list = []
                for categ_id in current_brand_id.categ_ids:

                    # Product Category
                    other_product_category_id = other_product_category_obj.search([('name', '=', categ_id.name), ('brand_id', '=', other_brand_id.id)], limit=1)
                    if not other_product_category_id:
                       category_read_data = categ_id.read(['name', 'media', 'fringe', 'channel', 'no_show', 'quotation_template_category', 'description'])
                       category_read_data[0].update({'brand_id': other_brand_id.id})
                       other_product_category_id = other_product_category_obj.create(category_read_data[0])

                    parent_categ_id = categ_id.parent_id
                    old_parent_id = other_product_category_id
                    while parent_categ_id:
                        new_parent_categ_id = other_product_category_obj.search([('name', '=', parent_categ_id.name), ('brand_id', '=', other_brand_id.id)], limit=1)
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
                    print("==categ_id===", categ_id)
                    # Product Template
                    for template_id in product_template_obj.search([('categ_id', 'child_of', categ_id.ids)]):
                        _logger.info("template_id==> %s", template_id)
                        other_product_template_id = other_product_template_obj.search([('name', '=', template_id.name), ('brand_id', '=', other_brand_id.id), ('copy_brand_reference', '=', template_id.id)], limit=1)
                        categ_id = False
                        client_id = False
                        if not other_product_template_id:

                            # Product Category
                            categ_id = other_product_category_obj.search([('name', '=', template_id.categ_id.name), ('brand_id', '=', other_brand_id.id)], limit=1)
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
                            other_product_variant_id = other_product_product_obj.search([('brand_id', '=', other_brand_id.id), ('copy_brand_reference', '=', product_id.id)], limit=1)
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
                body = (_('Data Copy successfully from %s to %s database!') % (current_db_name, target_database_name))
                current_brand_id.message_post(body=body, subject=other_brand_id.id)
                _logger.info("Process Completed....")
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.multi
    def copy_brand_data_on_same_database(self, source_brand=None, target_brand=None, copy_type='both'):
        if copy_type == 'wplan':
            thread = threading.Thread(target=self.assign_process_wplan_API, args=(source_brand, target_brand))
            thread.start()
        elif copy_type == 'assets':
            thread = threading.Thread(target=self.assign_process_assets_API, args=(source_brand, target_brand))
            thread.start()
        else:
            thread = threading.Thread(target=self.assign_process_wplan_assets_API, args=(source_brand, target_brand))
            thread.start()
        current_brand_id = self.browse(source_brand)
        target_brand_id = self.browse(target_brand)
        _logger.info("Copy Multi Brand process runnning from %s to %s branch!", current_brand_id.name, target_brand_id.name)

    @api.multi
    def assign_process_wplan_assets_API(self, source_brand, target_brand):
        self.assign_process_wplan_API(source_brand, target_brand)
        self.assign_process_assets_API(source_brand, target_brand)

    @api.multi
    def assign_process_wplan_API(self, source_brand, target_brand):
        try:
            with api.Environment.manage():
                new_cr = self.pool.cursor()
                self = self.with_env(self.env(cr=new_cr))
                self.action_multi_brand_assign_process_wplan(source_brand, target_brand)
                new_cr.commit()
                new_cr.close()
                _logger.info("Asigned Process done successfuly")
            return {'type': 'ir.actions.act_window_close'}
        except Exception as error:
            _logger.info(error)

    @api.multi
    def action_multi_brand_assign_process_wplan(self, current_brand_id, target_brand_id):
        current_brand_id = self.browse(current_brand_id)
        target_brand_id = self.browse(target_brand_id)
        _logger.info("current_brand_id===>>>%s", current_brand_id)
        _logger.info("target_brand_id===>>>%s", target_brand_id)
        crm_lead_type_obj = self.env['crm.lead.type']
        crm_lead_type_ids = crm_lead_type_obj.search([('brand_id', '=', current_brand_id.id)])
        _logger.info("crm_lead_type_ids===>>>%s", crm_lead_type_ids)
        for crm_lead_type_id in crm_lead_type_ids:
            _logger.info("crm_lead_type_id===>>>%s", crm_lead_type_id)
            new_crm_lead_type = crm_lead_type_id.copy()
            new_parent_id = False
            if new_crm_lead_type.parent_crm_lead_type:
                new_parent_id = crm_lead_type_obj.search([('name', '=', new_crm_lead_type.parent_crm_lead_type.name), ('brand_id', '=', target_brand_id.id)], limit=1)
                if not new_parent_id:
                    new_parent_id = new_crm_lead_type.parent_crm_lead_type.copy()
                    new_parent_id.write({'brand_id': target_brand_id.id, 'name': new_parent_id.name})
            first_parent_id = new_parent_id
            while new_parent_id:
                old_parent_id = new_parent_id
                if new_parent_id.parent_crm_lead_type:
                    new_parent_id = crm_lead_type_obj.search([('name', '=', new_parent_id.parent_crm_lead_type.name), ('brand_id', '=', target_brand_id.id)], limit=1)
                    if not new_parent_id:
                        new_parent_id = new_parent_id.parent_crm_lead_type.copy()
                        old_parent_id.write({
                            'parent_crm_lead_type': new_parent_id.id,
                            'brand_id': target_brand_id.id,
                            'name': new_parent_id.name,
                            })
                else:
                    new_parent_id = False
            flow_ids = []
            for flow_id in new_crm_lead_type.flows_ids:
                new_flow_id = flow_id.copy()
                flow_ids.append(new_flow_id.id)
                if not flow_id.step_id:
                    continue
                new_step_id = flow_id.step_id.copy()
                step_title = new_step_id.title.replace(' (copy)', '')
                new_step_id.write({'title': step_title, 'brand_reference': target_brand_id.id})
                new_flow_id.write({'name': new_flow_id.name, 'step_id': new_step_id.id, 'brand_id': target_brand_id.id})
            new_crm_lead_type.write({
                'flows_ids': [(6, 0, flow_ids)],
                'brand_id': target_brand_id.id,
                'parent_crm_lead_type': first_parent_id and first_parent_id.id,
                'name': new_crm_lead_type.name,
                })
        body = (_('Plan related data assigned successfully from %s to %s branch!') % (current_brand_id.name, target_brand_id.name))
        current_brand_id.message_post(body=body, subject=target_brand_id.id)

    @api.multi
    def assign_process_assets_API(self, source_brand, target_brand):
        try:
            with api.Environment.manage():
                new_cr = self.pool.cursor()
                self = self.with_env(self.env(cr=new_cr))
                self.action_multi_brand_assign_process_assets(source_brand, target_brand)
                new_cr.commit()
                new_cr.close()
                _logger.info("Asigned Process done successfuly")
            return {'type': 'ir.actions.act_window_close'}
        except Exception as error:
            _logger.info(error)

    @api.multi
    def action_multi_brand_assign_process_assets(self, current_brand_id, target_brand_id):
        current_brand_id = self.browse(current_brand_id)
        target_brand_id = self.browse(target_brand_id)
        product_template_obj = self.env['product.template']
        _logger.info("===>>target_brand_id==%s>", target_brand_id)
        _logger.info("===>>current_brand_id=%s=>", current_brand_id)
        bom_obj = self.env['mrp.bom']
        category_ids = self.env['product.category'].search([('brand_id', '=', current_brand_id.id)])
        cated_ids = []
        for categ_id in category_ids:
            _logger.info("categ_id===>>>%s", categ_id)
            new_categ_id = categ_id.copy()
            new_categ_id.write({'name': new_categ_id.name, 'brand_id': target_brand_id.id})
            template_ids = product_template_obj.search([('categ_id', 'child_of', categ_id.ids)])
            for template_id in template_ids:
                _logger.info("template_id===>>>%s", template_id)
                check_bom_ids = []
                product_ids = self.env['product.product'].search([('product_tmpl_id', '=', template_id.id)])
                new_template_id = False
                if product_ids:
                    new_template_id = template_id.copy()
                    new_template_id.write({'categ_id': new_categ_id.id, 'name': new_template_id.name, 'brand_id': target_brand_id.id})
                default_template_unlink = []
                for product_id in product_ids:
                    new_product_id = product_id.copy()
                    default_template_unlink.append(new_product_id.product_tmpl_id.id)
                    new_product_id.write({
                        'name': product_id.name,
                        'product_name': product_id.product_name or '',
                        'brand_id': target_brand_id.id,
                        'product_tmpl_id': new_template_id.id,
                        'categ_id': new_categ_id and new_categ_id.id})
                    bom_ids = bom_obj.search([('product_id', '=', product_id.id)])
                    for bom_id in bom_ids:
                        _logger.info("bom_id==>%s", bom_id)
                        if bom_id and product_id not in check_bom_ids:
                            check_bom_ids.append(product_id)
                            new_bom_id = bom_id.copy()
                            new_routing_id = False
                            if bom_id.routing_id:
                                new_routing_id = bom_id.routing_id.copy()
                                new_routing_id.operation_ids = [(6,0,[])]
                                for operation_id in bom_id.routing_id.operation_ids:
                                    new_operation_id = operation_id.copy()
                                    new_operation_id.write({'routing_id': new_routing_id.id})
                                new_routing_id.write({'name': new_routing_id.name, 'brand_id': target_brand_id.id})
                            new_bom_id.write({
                                'product_tmpl_id': new_template_id.id,
                                'product_id': new_product_id.id,
                                'routing_id': new_routing_id and new_routing_id.id,
                            })
                if default_template_unlink:
                    self.env.cr.execute("""delete from product_template WHERE id IN %s""", [tuple(default_template_unlink)])
                if new_template_id:
                    unlink_default_product_ids = self.env['product.product'].search([('product_tmpl_id', '=', new_template_id.id), ('brand_id', '=', False)])
                    if unlink_default_product_ids:
                        self.env.cr.execute("""delete from product_product WHERE id IN %s""", [tuple(unlink_default_product_ids.ids)])
            cated_ids.append(new_categ_id.id)
        target_brand_id.categ_ids = [(6, 0, cated_ids)]
        body = (_('Assets related data assigned successfully from %s to %s branch!') % (current_brand_id.name, target_brand_id.name))
        current_brand_id.message_post(body=body, subject=target_brand_id.id)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    brand_id = fields.Many2one('multi.brand', 'Brand')
    copy_brand_reference = fields.Integer('Copy Reference')


class ProductProduct(models.Model):
    _inherit = "product.product"

    brand_id = fields.Many2one('multi.brand', 'Brand')
    public_price = fields.Float('Public Price')
    taxes_id = fields.Many2many('account.tax', 'products_taxes_rel', 'product_id', 'tax_id', help="Default taxes used when selling the product.", string='Customer Taxes',
        domain=[('type_tax_use', '=', 'sale')], default=lambda self: self.env.user.company_id.account_sale_tax_id)
    copy_brand_reference = fields.Integer('Copy Reference')


class ProductCategory(models.Model):
    _inherit = "product.category"

    brand_id = fields.Many2one('multi.brand', 'Brand')


class MRPBOM(models.Model):
    _inherit = "mrp.bom"

    brand_id = fields.Many2one(related='product_id.brand_id', string='Brand')


class MRPRouting(models.Model):
    _inherit = "mrp.routing"

    brand_id = fields.Many2one('multi.brand', 'Brand')


class ShareBrand(models.Model):
    _name = "share.brand"
    _description = 'Share Brand'
    _rec_name = 'brand_id'

    brand_id = fields.Many2one('multi.brand', 'Brand')
    category = fields.Selection([
        ('production', 'Production'),
        ('creative', 'Creative'),
        ('client', 'Client'),
        ('media', 'Media')], 'Category')
    wsuite_company_id = fields.Integer('Wsuite Company')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('rejected', 'Rejected'),
        ('approved', 'Approved'),
        ])
