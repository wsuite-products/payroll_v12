# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from datetime import datetime, timedelta, date
import time
import logging
_logger = logging.getLogger(__name__)
from operator import itemgetter


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    @api.multi
    def create_crm_lead_stage_second(self, stage_id, step_id, prev_stage):
        response_id = self.env['step.user_input'].create({
            'step_id': step_id,
            'type': 'manually',
        })
        self.env['crm.lead.stage'].create({
            'crm_lead_id': self.id,
            'stage_id': stage_id,
            'pre_stage_id': prev_stage,
            'date': fields.Datetime.now(),
            'state': 'in_progress',
            'response_id': response_id.id,
        })

    @api.model
    def create(self, vals):
        res = super(CRMLead, self).create(vals)
        res.create_crm_lead_stage_second(res.stage_id.id, res.stage_id.step_id.id, False)
        return res

    @api.multi
    def get_all_lead_data(self, lead_id):
        _logger.info("===>>get_all_lead_data==")
        if not lead_id:
            return "Please provide the Lead Id"
        lead_id = self.browse(lead_id)
        _logger.info(" lead_id : %s", lead_id)
        lead_data = lead_id.read([])
        lead_data[0].update({
            "request_check": lead_id.crm_lead_type_id.parent_crm_lead_type.request_chk or False,
        })
        stage_data = False
        _logger.info("===>>stage_id : %s", lead_id.stage_id)
        _logger.info("===>>step_id : %s", lead_id.step_id)
        if lead_id.stage_id:
            stage_data = lead_id.stage_id.read(
                ["id", "name", "sequence", "probability", "on_change", "requirements", "team_id", "legend_priority",
                 "fold", "create_uid", "write_uid", "step_id", "feedback", "feedback_category",
                 "feedback_type", "category_css", "step_flag", "color", "image", "image_url", "file_name", "is_loghour",
                 "mandatory", "approved_by", "active", "brand_id", "team_count",
                 "display_name", "task_id"])

            stage_data[0].update({
                "create_date": str(lead_id.stage_id.create_date),
                "write_date": str(lead_id.stage_id.write_date),
            })

        cls_id = self.env['crm.lead.stage'].search(
            [('stage_id', '=', lead_id.stage_id.id),
             ('crm_lead_id', '=', lead_id.id),
             ('step_id', '=', lead_id.step_id.id),
             ('response_id', '!=', False)])
        _logger.info("===>>History id: %s", cls_id)
        history_data = False
        answer_data = False
        if cls_id:
            history_data = cls_id.read(
                ["id", "crm_lead_id", "stage_id", "pre_stage_id", "create_uid", "write_uid",
                 "response_id", "state", "user_ids", "done_user_ids", "display_name", "step_id"])

            history_data[0].update({
                "date": str(cls_id.date),
                "create_date": str(cls_id.create_date),
                "write_date": str(cls_id.write_date),
            })

            _logger.info("===>>Answer id: %s", cls_id.response_id)
            answer_data = cls_id.response_id.read([
                "id", "step_id", "deadline", "type", "state", "test_entry", "token", "partner_id", "email",
                "last_displayed_page_id", "user_input_line_ids", "create_uid", "write_uid",
                "result_url", "print_url", "quizz_score", "display_name"])

            answer_data[0].update({
                "date_create": str(cls_id.response_id.date_create),
                "create_date": str(cls_id.response_id.create_date),
                "write_date": str(cls_id.response_id.write_date),
            })

        step_page_data = []
        for page_id in lead_id.step_id.page_ids:
            page_read_data = page_id.read([
                "id", "title", "step_id", "question_ids", "comment_ids", "sequence", "description", "form_config",
                "task_id", "is_loghour", "active", "sla", "create_uid", "write_uid", "display_name"])
            page_read_data[0].update({
                "create_date": str(page_id.create_date),
                "write_date": str(page_id.write_date),
            })
            step_page_data.append((page_read_data[0]))

        lead_type_stage_data = []
        for flow_id in lead_id.crm_lead_type_id.flows_ids:
            flow_read_data = flow_id.read([])
            flow_read_data[0].update({
                "create_date": str(flow_id.create_date),
                "write_date": str(flow_id.write_date),
            })
            lead_type_stage_data.append((flow_read_data[0]))

        all_history_data = []
        all_answer_data = []
        for history_id in lead_id.crm_lead_stage_ids:
            history_all_data = history_id.read(
                ["id", "crm_lead_id", "stage_id", "pre_stage_id", "create_uid", "write_uid",
                 "response_id", "state", "user_ids", "done_user_ids", "display_name", "step_id"])
            history_all_data[0].update({
                "date": str(history_id.date),
                "create_date": str(history_id.create_date),
                "write_date": str(history_id.write_date),
            })
            all_history_data.append(history_all_data[0])
            if history_id.response_id:
                answer_all_data = history_id.response_id.read([
                    "id", "step_id", "deadline", "type", "state", "test_entry", "token", "partner_id", "email",
                    "last_displayed_page_id", "user_input_line_ids", "create_uid", "write_uid",
                    "result_url", "print_url", "quizz_score", "display_name"])

                answer_all_data[0].update({
                    "date_create": str(history_id.response_id.date_create),
                    "create_date": str(history_id.response_id.create_date),
                    "write_date": str(history_id.response_id.write_date),
                })
                all_answer_data.append(answer_all_data[0])

        quotation_numbers = list(set(lead_id.product_quote_ids.mapped('quotation_number')))
        cll_obj = self.env['crm.lead.lines']
        All_Quotations = []
        for quotation_number in quotation_numbers:
            product_quote_ids = cll_obj.search([
                ('quotation_number', '=', quotation_number),
                ('crm_lead_id', '=', lead_id.id),
                ('order_line_id', '=', False)])
            if product_quote_ids:
                All_Quotations.append({"quotation_number": quotation_number, "status": "In-Progress"})
            else:
                All_Quotations.append({"quotation_number": quotation_number, "status": "Done"})
        response_data = {
            "Campaign": lead_data and lead_data[0] or '',
            "Stage": stage_data and stage_data[0] or '',
            "Formhistory": history_data and history_data[0] or '',
            "Answer": answer_data and answer_data[0] or '',
            "Steppages": step_page_data,
            'Leadtypeflows': lead_type_stage_data,
            "AllFormhistory": all_history_data,
            "AllAnswer": all_answer_data,
            "All_Quotations": All_Quotations,
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    @api.multi
    def get_questions_answer(self, lead_id=False, step_id=False, page_id=False, user_input_id=False):
        _logger.info("===>>get_questions_answer==")
        _logger.info("===>>step_id id: %s", step_id)
        _logger.info("===>>page_id id: %s", page_id)
        if not step_id and page_id:
            return "Please give the step_id and page_id"
        question_ids = self.env['step.question'].search([('step_id', '=', step_id), ('page_id', '=', page_id)])
        question_ids_list = []

        for question_id in question_ids:
            question_data = question_id.read([
                "id", "page_id", "sequence", "question", "description", "type", "matrix_subtype", "labels_ids",
                "labels_ids_2", "column_nb", "display_mode", "comments_allowed", "comments_message",
                "comment_count_as_answer", "validation_required", "validation_email", "validation_length_min",
                "validation_length_max", "validation_min_float_value", "validation_max_float_value",
                "validation_error_msg", "constr_mandatory", "constr_error_msg", "user_input_line_ids", "field_config",
                "create_uid", "write_uid", "step_id", "display_name"
            ])
            question_data[0].update({
                "validation_min_date": str(question_id.validation_min_date),
                "validation_max_date": str(question_id.validation_max_date),
                "create_date": str(question_id.create_date),
                "write_date": str(question_id.write_date),
            })
            question_ids_list.append(question_data[0])

        domain = [('step_id', '=', step_id), ('page_id', '=', page_id)]
        if not user_input_id:
            lead_id = self.browse(lead_id)
            cls_id = self.env['crm.lead.stage'].search(
                [('stage_id', '=', lead_id.stage_id.id),
                 ('crm_lead_id', '=', lead_id.id),
                 ('step_id', '=', lead_id.step_id.id),
                 ('response_id', '!=', False)])
            if cls_id.response_id:
                domain += [('user_input_id', '=', cls_id.response_id.id)]
        else:
            domain += [('user_input_id', '=', user_input_id)]

        answer_ids = self.env['step.user_input_line'].search(domain)
        answer_ids_list = []
        for answer_id in answer_ids:
            answer_data = answer_id.read([
                "id", "user_input_id", "question_id", "step_id", "value_json_data", "answer_type", "page_id"])
            answer_ids_list.append(answer_data[0])

        response_data = {
            "Question": question_ids_list or [],
            "Answer": answer_ids_list or [],
        }

        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    @api.multi
    def get_product_template_data(self, product_tmpl_id):
        start = time.time()
        _logger.info("==Old=>>get_product_template_data==")
        _logger.info("===>>product_tmpl_id id: %s", product_tmpl_id)
        if not product_tmpl_id:
            return "Please provide the Product Template"
        product_ids = self.env['product.product'].search([('product_tmpl_id', '=', product_tmpl_id)])
        template_data = []
        for product_id in product_ids:
            product_data = self.get_product_data(product_id)
            template_data.append(product_data[0])
        response_data = {
            "Templates": template_data,
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        done = time.time()
        elapsed = done - start
        _logger.info("===>> Seconds : %s", elapsed)
        return response_data

    @api.multi
    def get_product_work_centers_data(self, product_id):
        WorkCenters = []
        for bom_id in product_id.variant_bom_ids:
            for op_id in bom_id.routing_id.operation_ids:
                op_data = op_id.read([
                    "id", "name", "workcenter_id", "sequence", "routing_id", "note", "company_id", "worksheet",
                    "time_mode", "time_mode_batch", "time_cycle_manual", "batch", "batch_size", "workorder_ids",
                    "resource_id", "task_form_json", "is_operational", "create_uid", "create_date", "write_uid",
                    "write_date", "x_task_form_json", "time_cycle", "workorder_count", "display_name"])
                WorkCenters.append(op_data[0])
        return WorkCenters

    @api.multi
    def get_product_data(self, product_id):
        _logger.info("===>>product_id id: %s", product_id)
        product_data = product_id.read([
            "id", "product_tmpl_id", "public_price", "taxes_id", "direct_cost", "indirect_cost", "income",
            "product_name", "name", "description", "categ_id", "bom_ids", "route_ids", "list_price", "company_id",
            "qty_available", "bom_count", "display_name"])
        WorkCenters = self.get_product_work_centers_data(product_id)
        product_data[0].update({
            'WorkCenters': WorkCenters
        })
        return product_data

    @api.multi
    def get_product_template_data_query(self, product_tmpl_id):
        start = time.time()
        _logger.info("===>>get_product_template_data_query==")
        _logger.info("===>>product_tmpl_id id: %s", product_tmpl_id)
        if not product_tmpl_id:
            return "Please provide the Product Template"
        self.env.cr.execute(
            '''SELECT id FROM product_product
                            WHERE product_tmpl_id = '%s'
                        ''' % (product_tmpl_id))
        product_ids = self.env['product.product'].browse([row['id'] for row in self.env.cr.dictfetchall()])
        template_data = []
        for product_id in product_ids:
            product_data = self.get_product_data_query(product_id)
            template_data.append(product_data[0])
        response_data = {
            "Templates": template_data,
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        done = time.time()
        elapsed = done - start
        return response_data

    @api.multi
    def get_product_work_centers_data_query(self, product_id):
        WorkCenters = []
        self.env.cr.execute(
            '''SELECT routing_id FROM mrp_bom
                            WHERE product_id = '%s'
                        ''' % (product_id.id))
        for routing_id in self.env.cr.dictfetchall():
            if routing_id.get('routing_id', ''):
                self.env.cr.execute(
                    '''SELECT id FROM mrp_routing_workcenter
                                    WHERE routing_id = '%s'
                                ''' % (routing_id.get('routing_id', '')))
                for op_id in self.env['mrp.routing.workcenter'].browse([row['id'] for row in self.env.cr.dictfetchall()]):
                    op_data = op_id.read([
                        "id", "name", "workcenter_id", "sequence", "routing_id", "note", "company_id", "worksheet",
                        "time_mode", "time_mode_batch", "time_cycle_manual", "batch", "batch_size", "workorder_ids",
                        "resource_id", "task_form_json", "is_operational", "create_uid", "create_date", "write_uid",
                        "write_date", "x_task_form_json", "time_cycle", "workorder_count", "display_name"])
                    WorkCenters.append(op_data[0])
        return WorkCenters

    @api.multi
    def get_product_data_query(self, product_id):
        _logger.info("===>>product_id id: %s", product_id)
        product_data = product_id.read([
            "id", "product_tmpl_id", "public_price", "taxes_id", "direct_cost", "indirect_cost", "income",
            "product_name", "name", "description", "categ_id", "bom_ids", "route_ids", "list_price", "company_id",
            "qty_available", "bom_count", "display_name"])
        WorkCenters = self.get_product_work_centers_data_query(product_id)
        product_data[0].update({
            'WorkCenters': WorkCenters
        })
        return product_data

    @api.multi
    def get_lead_line_data(self, lead_id, quotation_number):
        _logger.info("===>>get_lead_line_data==")
        _logger.info("===>>lead_id id: %s", lead_id)
        _logger.info("===>>quotation_number id: %s", quotation_number)
        if not lead_id and quotation_number:
            return "Please give the lead_id and quotation_number"
        clpq_obj = self.env['crm.lead.product.quotes']
        lead_line_ids = self.env['crm.lead.lines'].search([
            ('crm_lead_id', '=', lead_id),
            ('quotation_number', '=', str(quotation_number))])

        lead_line_list = []
        for lead_line_id in lead_line_ids:
            lead_line_data = lead_line_id.read([])
            WorkCenters = self.get_product_work_centers_data(lead_line_id.product_id)
            lead_line_data[0].update({
                "WorkCenters": WorkCenters,
                "category": [lead_line_id.product_id.categ_id.id, lead_line_id.product_id.categ_id.name],
            })
            lead_line_list.append(lead_line_data[0])

        clpq_ids = clpq_obj.search([
            ('crm_lead_id', '=', lead_id),
            ('quotation_number', '=', str(quotation_number))])
        clpq_list = [clpq_id.read([])[0] for clpq_id in clpq_ids]

        all_quotation_ids = clpq_obj.search([('crm_lead_id', '=', lead_id)])

        response_data = {
            "LeadLines": lead_line_list or [],
            "PreQuoteLines": clpq_list or [],
            "All_Quotations": list(set(all_quotation_ids.mapped('quotation_number'))),
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    def get_all_activity(self, mail_message_ids, lead_id, work_order_id):
        res_users_obj = self.env['res.users']
        mail_message_activity_list = []
        for mail_message_id in mail_message_ids:
            _logger.info("===>> mail_message_id : %s", mail_message_id)
            user_id = res_users_obj.search([
                '|', ('login', '=', mail_message_id.author_id.email),
                ('partner_id', '=', mail_message_id.author_id.id)])

            _logger.info("===>> author_id : %s", mail_message_id.author_id)
            _logger.info("===>> user_id : %s", user_id)

            comment_id = False
            if mail_message_id.model == 'workorder.comment':
                comment_id = mail_message_id.res_id

            for tracking_value_id in mail_message_id.sudo().tracking_value_ids:
                tracking_values = {}
                if tracking_value_id.field_type == 'boolean':
                    tracking_values = {
                        'subject': tracking_value_id.field_desc or "",
                        'old_value': False if tracking_value_id.old_value_integer == 0 else True,
                        'new_value': False if tracking_value_id.new_value_integer == 0 else True,
                    }
                elif tracking_value_id.field_type == 'integer':
                    tracking_values = {
                        'subject': tracking_value_id.field_desc or "",
                        'old_value': tracking_value_id.old_value_integer,
                        'new_value': tracking_value_id.new_value_integer,
                    }
                elif tracking_value_id.field_type in ['many2one', 'selection']:
                    tracking_values = {
                        'subject': tracking_value_id.field_desc or "",
                        'old_value': tracking_value_id.old_value_char or "",
                        'new_value': tracking_value_id.new_value_char or "",
                    }
                elif tracking_value_id.field_type in ['datetime', 'date']:
                    tracking_values = {
                        'subject': tracking_value_id.field_desc or "",
                        'old_value': tracking_value_id.old_value_datetime or "",
                        'new_value': tracking_value_id.new_value_datetime or "",
                    }

                elif tracking_value_id.field_type == 'float':
                    tracking_values = {
                        'subject': tracking_value_id.field_desc or "",
                        'old_value': tracking_value_id.old_value_float or "",
                        'new_value': tracking_value_id.new_value_float or "",
                    }

                elif tracking_value_id.field_type == 'monetary':
                    tracking_values = {
                        'subject': tracking_value_id.field_desc or "",
                        'old_value': tracking_value_id.old_value_monetary or "",
                        'new_value': tracking_value_id.new_value_monetary or "",
                    }

                elif tracking_value_id.field_type in ['text', 'html']:
                    tracking_values = {
                        'subject': tracking_value_id.field_desc or "",
                        'old_value': tracking_value_id.old_value_text or "",
                        'new_value': tracking_value_id.new_value_text or "",
                    }
                if tracking_values:
                    tracking_values.update({
                        'message_id': mail_message_id.id,
                        'comment_id': comment_id,
                        'work_order_id': work_order_id.id,
                        'work_order_name': work_order_id.name,
                        'lead_id': lead_id,
                        'write_date': mail_message_id.write_date,
                        'create_date': mail_message_id.create_date,
                        "user_details": {
                            'id': user_id.id or "",
                            'name': user_id.name or "",
                            'profile_image': user_id and user_id.employee_id.profile_image_url or "",
                        }
                    })
                mail_message_activity_list.append(tracking_values)
        return mail_message_activity_list

    @api.multi
    def get_w_project_dashboard_data(self, user_id, brand_id):
        _logger.info("===>>get_w_project_dashboard_data==")
        _logger.info("===>>user_id id: %s", user_id)
        _logger.info("===>>brand_id id: %s", brand_id)
        if not user_id and brand_id:
            return "Please give the user_id and brand_id"

        work_order_ids = self.env['mrp.workorder'].search(
            [('production_id.lead_id.all_user_ids', 'in', [user_id]), ('brand_id', '=', brand_id)], order='id desc')
        _logger.info("===>>work_order_ids id: %s", work_order_ids)

        new_task_count = len(work_order_ids.filtered(lambda r: r.state in ["pending", "ready"]))
        in_progress_task_count = len(work_order_ids.filtered(lambda r: r.state in ["progress"]))
        done_task_count = len(work_order_ids.filtered(lambda r: r.state in ["done"]))
        mm_obj = self.env['mail.message']
        recent_activity_list = []
        for work_order_id in work_order_ids[:5]:
            lead_id = work_order_id.production_id.lead_id.id
            mail_message_ids = mm_obj.search(
                [('model', '=', 'mrp.workorder'), ('res_id', '=', work_order_id.id)], order='id desc')
            if mail_message_ids:
                if len(recent_activity_list) > 5:
                    break
                recent_activity_list.extend(self.get_all_activity(mail_message_ids, lead_id, work_order_id))

            # comments_mail_message_ids = mm_obj.search([
            #     ('model', '=', 'workorder.comment'),
            #     ('res_id', 'in', work_order_id.comment_ids.ids)], order='id desc')
            # if comments_mail_message_ids:
            #     recent_activity_list.extend(self.get_all_activity(comments_mail_message_ids, lead_id, work_order_id.id))
        recent_tasks_list = []
        for work_order_id in work_order_ids[:9]:
            work_ordere_data = work_order_id.read([
                "assign_id", "comment_ids", "date_planned_finished", "date_start", "description", "id", "name",
                "production_id", "responsible_id"])
            user_image_list = []
            for w_user_id in work_order_id.production_id.lead_id.all_user_ids:
                user_image_list.append(w_user_id.employee_id.profile_image_url)
            work_ordere_data[0].update({
                "pro_date_planned_finished": work_order_id.production_id.date_planned_finished,
                "pro_date_planned_start": work_order_id.production_id.date_planned_start,
                "user_image": user_image_list,
                "lead_id": work_order_id.production_id.lead_id.id,
            })
            recent_tasks_list.append(work_ordere_data[0])

        crm_lead_ids = self.env['crm.lead'].search([
            ('brand_id', '=', brand_id),
            ('all_user_ids', 'in', [user_id])], limit=9, order='id desc')

        recent_project_list = []
        for crm_lead_id in crm_lead_ids:
            vals = {
                "description": crm_lead_id.description or "",
                "id": crm_lead_id.id,
                "name": crm_lead_id.name or "",
                "create_date": crm_lead_id.create_date,
                "create_uid": {
                    "id": crm_lead_id.create_uid.id,
                    "name": crm_lead_id.create_uid.name or "",
                    "profileImage": crm_lead_id.create_uid.employee_id.profile_image_url or "",
                }
            }
            recent_project_list.append(vals)

        response_data = {
            "new_task_count": new_task_count,
            "done_task_count": done_task_count,
            'in_progress_task_count': in_progress_task_count,
            "recent_tasks": recent_tasks_list,
            "recent_activity": recent_activity_list[:5],
            "recent_project": recent_project_list,
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    @api.multi
    def get_workpackages(self, user_id, brand_id, task_type, offset=0, limit=3, search_keyword=False, lead_id=False):
        _logger.info("===>>get_workpackages==")
        _logger.info("===>>user_id id: %s", user_id)
        _logger.info("===>>brand_id id: %s", brand_id)
        _logger.info("===>>task_type id: %s", task_type)
        _logger.info("===>>offset id: %s", offset)
        _logger.info("===>>limit id: %s", limit)
        _logger.info("===>>search_keyword id: %s", search_keyword)
        _logger.info("===>>lead_id id: %s", lead_id)
        mrp_workorder_obj = self.env['mrp.workorder']
        mrp_production_obj = self.env['mrp.production']
        if not offset:
            offset = 0
        if not limit:
            limit = 3

        domain = [('production_id.lead_id.all_user_ids', 'in', [user_id]), ('brand_id', '=', brand_id)]
        if task_type != 'recent':
            domain += [('state', 'in', [task_type])]
        else:
            domain += [('state', '!=', 'done')]
        if search_keyword:
            domain += [('name', 'ilike', search_keyword)]
        if lead_id:
            domain += [('production_id.lead_id', '=', lead_id)]

        _logger.info("\n===>>domain id: %s", domain)
        work_order_ids = mrp_workorder_obj.search(domain)
        production_ids_list_length = 0
        if work_order_ids:
            production_ids_list = work_order_ids.mapped('production_id')
            production_ids_list_length = len(production_ids_list)
            production_ids = mrp_production_obj.search([('id', 'in', production_ids_list.ids)], order='id desc', limit=limit, offset=offset)
            domain += [('production_id', 'in', production_ids.ids)]
            work_order_ids = mrp_workorder_obj.search(domain)

        _logger.info("===>>work_order_ids id: %s", work_order_ids)

        recent_tasks_list = []
        for work_order_id in work_order_ids:
            work_ordere_data = work_order_id.read([
                "assign_id", "date_planned_finished", "date_start", "description", "id", "name",
                "responsible_id", "create_date", "write_date", "state"])

            active_work_order_id = work_order_id.production_id.workorder_ids.filtered(
                lambda r: r.state in ["progress", "ready"] and not r.re_open)
            if len(active_work_order_id) > 1:
                active_work_order_id = active_work_order_id[-1]
            if not active_work_order_id:
                check_all_work_order = all(work_order_id.production_id.workorder_ids.filtered(lambda r: r.state == "done"))
                _logger.info("===>>check_all_work_order: %s", check_all_work_order)
                if check_all_work_order:
                    active_work_order_id = work_order_id.production_id.workorder_ids[-1]

            if work_order_id.production_id.step_id:
                product_name = work_order_id.production_id.step_id.title
            else:
                product_name = work_order_id.production_id.product_id.product_name

            work_ordere_data[0].update({
                "Lead_data": [work_order_id.production_id.lead_id.id, work_order_id.production_id.lead_id.name],
                "MO_data": {
                    "id": work_order_id.production_id.id,
                    "name": work_order_id.production_id.name,
                    "work_order_state": active_work_order_id and active_work_order_id.name or "",
                    "product_name": product_name,
                    "pro_date_planned_finished": work_order_id.production_id.date_planned_finished,
                    "pro_date_planned_start": work_order_id.production_id.date_planned_start,
                    "create_date": work_order_id.production_id.create_date,
                    "write_date": work_order_id.production_id.write_date,
                }
            })
            recent_tasks_list.append(work_ordere_data[0])

        response_data = {
            "recordLength": len(mrp_workorder_obj.search(domain)),
            "MOrecordLength": production_ids_list_length,
            "records": recent_tasks_list,
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    def get_activity_list(self, user_id, brand_id, offset=0, limit=10):
        _logger.info("===>>get_activity_list==")
        _logger.info("===>>user_id id: %s", user_id)
        _logger.info("===>>brand_id id: %s", brand_id)
        _logger.info("===>>offset id: %s", offset)
        _logger.info("===>>limit id: %s", limit)
        mail_message_obj = self.env['mail.message']
        domain = [
            ('model', 'in', ['mrp.workorder', 'sale.order', 'crm.lead', 'crm.lead.stage']),
            ('subject', '!=', False)]
        mail_message_ids = mail_message_obj.search(domain, order='id desc', limit=limit, offset=offset)
        recent_activity_list = []
        for mail_message_id in mail_message_ids:
            mail_message_data = mail_message_id.read(["date", "id", "model", "subject"])
            mail_message_data[0].update({'author_url': mail_message_id.author_id.image_url})
            recent_activity_list.append(mail_message_data[0])

        response_data = {
            "recordLength": len(mail_message_obj.search(domain)),
            "recent_activity": recent_activity_list,
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    def get_kanban_list(self, user_id, brand_id, lead_id):
        _logger.info("===>>get_kanban_list==")
        _logger.info("===>>user_id id: %s", user_id)
        _logger.info("===>>brand_id id: %s", brand_id)
        _logger.info("===>>lead_id id: %s", lead_id)
        sale_order_obj = self.env['sale.order']
        sale_order_ids = sale_order_obj.search([
            ('opportunity_id', '=', lead_id),
            ('opportunity_id.brand_id', '=', brand_id),
            ('opportunity_id.all_user_ids', 'in', [user_id]),
        ])
        mo_list = []
        count = 0
        check_product_list = []
        for sale_order_id in sale_order_ids:
            for sale_order_line_id in sale_order_id.order_line:
                if sale_order_line_id.product_id.id not in check_product_list:
                    count += 1
                    vals = {
                        'product_id': sale_order_line_id.product_id.id,
                        'product_name': sale_order_line_id.product_id.product_name
                    }
                    mo_list.append(vals)
                    check_product_list.append(sale_order_line_id.product_id.id)

        response_data = {
            "recordLength": count,
            "records": mo_list,
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    def get_kanban_tasks(self, lead_id, product_id):
        _logger.info("===>>get_kanban_tasks==")
        _logger.info("===>>lead_id id: %s", lead_id)
        _logger.info("===>>product_id id: %s", product_id)
        mrp_pro_obj = self.env['mrp.production']
        mo_list = []
        count = 0
        domain = [('lead_id', '=', lead_id), ('step_id', '=', False)]
        if product_id:
            domain += [('product_id', '=', product_id)]
        mo_ids = mrp_pro_obj.search(domain)
        work_order_list = []
        for mo_id in mo_ids:
            for work_order_id in mo_id.workorder_ids:
                if not any(d['name'] == work_order_id.name for d in work_order_list):
                    work_order_list.append({'id': work_order_id.id, 'name': work_order_id.name})
            work_order_id = mo_id.workorder_ids.filtered(lambda r: r.state in ["progress", "ready"] and not r.re_open)
            if len(work_order_id) > 1:
                work_order_id = work_order_id[-1]
            if not work_order_id:
                check_all_work_order = all(mo_id.workorder_ids.filtered(lambda r: r.state == "done"))
                _logger.info("===>>check_all_work_order: %s", check_all_work_order)
                if check_all_work_order:
                    work_order_id = mo_id.workorder_ids[-1]
            if work_order_id:
                work_order_values = {
                    'id': work_order_id.id,
                    'name': work_order_id.name,
                    'assign_id': work_order_id.assign_id.id or "",
                    'assign_name': work_order_id.assign_id.name or "",
                    'profile_image': work_order_id.assign_id.employee_id.profile_image_url or "",
                    'state': work_order_id.state,
                    'date_start': work_order_id.date_start or "",
                    'date_finished': work_order_id.date_finished or "",
                    'date_planned_finished': work_order_id.date_planned_finished or "",
                    'date_planned_start': work_order_id.date_planned_start or "",
                }
            else:
                work_order_values = {
                    'id': False,
                    'name': "",
                    'assign_id': "",
                    'assign_name': "",
                    'profile_image': "",
                    'state': "",
                    'date_start': "",
                    'date_finished': "",
                    'date_planned_finished': "",
                    'date_planned_start': "",
                }
            vals = {
                'id': mo_id.id,
                'product_name': mo_id.product_id.name,
                'name': mo_id.name,
                'date_start': mo_id.date_start or "",
                'date_finished': mo_id.date_finished or "",
                'date_planned_finished': mo_id.date_planned_finished or "",
                'date_planned_start': mo_id.date_planned_start or "",
                'workOrderDetail': work_order_values or "",
            }
            mo_list.append(vals)

        response_data = {
            "recordLength": len(mo_ids),
            "recordLengthWorkOrder": count,
            "workorder_list": work_order_list,
            "manufacturing_list": mo_list,
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    def get_manufacturing_order_status_change(self, manufacturing_order_id, new_work_order_name):
        _logger.info("===>>get_manufacturing_order_status_change==")
        _logger.info("===>>manufacturing_order_id id: %s", manufacturing_order_id)
        _logger.info("===>>new_work_order_name id: %s", str(new_work_order_name))
        mrp_pro_obj = self.env['mrp.production']
        mo_id = mrp_pro_obj.browse(manufacturing_order_id)
        last_work_order_id = mo_id.workorder_ids and mo_id.workorder_ids[-1]
        new_work_order_id = self.env['mrp.workorder'].search(
            [('production_id', '=', manufacturing_order_id),
             ('name', '=', str(new_work_order_name))])
        _logger.info("===>>new_work_order_id: %s", new_work_order_id)
        if not new_work_order_id:
            return {
                "result": False,
                'message': "Record not found related " + str(new_work_order_name)
            }

        domain = [
            ('production_id', '=', manufacturing_order_id),
            ('state', 'not in', ['done', 'cancel'])]

        if last_work_order_id == new_work_order_id:
            domain += [('id', '<=', new_work_order_id.id)]
        else:
            domain += [('id', '<', new_work_order_id.id)]

        work_order_ids = self.env['mrp.workorder'].search(domain)
        _logger.info("===>>work_order_ids id: %s", work_order_ids)
        try:
            for work_order_id in work_order_ids:
                work_order_id.button_start()
                work_order_id.record_production()
            return {
                "result": True,
                "message": "Success"
            }
        except Exception as ex:
            _logger.info("Errors===: %s", str(ex))
            return {
                "result": False,
                'message': str(ex)
            }

    def get_workpackage_comment_list(self, model_type, order_id):
        if model_type not in ['WO', 'MO']:
            return "Please provide the type WO or MO!"
        if not model_type:
            model_type = 'WO'
        _logger.info("===>>get_workpackage_comment_list==")
        _logger.info("===>>order_id id: %s", order_id)
        _logger.info("===>>model_type : %s", model_type)
        order_id_list = []
        if model_type == 'WO':
            order_id_list = [order_id]
        elif model_type == 'MO':
            work_order_ids = self.env['mrp.workorder'].search([('production_id', '=', order_id)])
            order_id_list = work_order_ids.ids
        work_order_comment_ids = self.env['workorder.comment'].search([
            ('order_id', 'in', order_id_list),
            ('type', '=', 'comment'),
        ], order='id desc')
        comment_list = []
        for work_order_comment_id in work_order_comment_ids:
            values = {
                "id": work_order_comment_id.id,
                "comment_text": work_order_comment_id.comment,
                "write_date": work_order_comment_id.write_date,
                "attachment_url": work_order_comment_id.attachment_url,
                "user_details": {
                    'id': work_order_comment_id.user_id.id or "",
                    'name': work_order_comment_id.user_id.name or "",
                    'profile_image': work_order_comment_id.user_id.employee_id.profile_image_url or "",
                }

            }
            comment_list.append(values)
        response_data = {
            "recordLength": len(work_order_comment_ids),
            "comment_list": comment_list,
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    def get_workpackage_activity_list(self, model_type, order_id, selected_date, date_count):
        if model_type not in ['WO', 'MO']:
            return "Please provide the type WO or MO!"
        if not model_type:
            model_type = 'WO'
        _logger.info("===>>get_workpackage_activity_list==")
        _logger.info("===>>Type id: %s", model_type)
        _logger.info("===>>order_id id: %s", order_id)
        _logger.info("===>>selected_date id: %s", selected_date)
        _logger.info("===>>date_count id: %s", date_count)
        last_date = datetime.strptime(selected_date, '%Y-%m-%d')
        first_date = last_date - timedelta(days=date_count)
        _logger.info("===>>Starting Date: %s", first_date.date())
        _logger.info("===>>End Date: %s", last_date.date())
        comments_obj = self.env['workorder.comment']
        mail_message_obj = self.env['mail.message']
        order_id_list = []
        if model_type == 'WO':
            order_id_list = [order_id]
        elif model_type == 'MO':
            work_order_ids = self.env['mrp.workorder'].search([('production_id', '=', order_id)])
            order_id_list = work_order_ids.ids
        mail_message_attachment_ids = mail_message_obj.search(
            [('model', '=', 'workorder.comment'),
             ('date', '>=', first_date.date()),
             ('date', '<=', last_date.date())], order='id desc')
        comment_ids = comments_obj.search([
            ('id', 'in', mail_message_attachment_ids.mapped('res_id')),
            ('order_id', 'in', order_id_list),
            ('type', '=', 'attachment')])
        mail_message_attachment_ids = mail_message_obj.search(
            [('model', '=', 'workorder.comment'),
             ('res_id', 'in', comment_ids.ids)], order='id desc')
        mail_message_ids = mail_message_obj.search(
            [('model', '=', 'mrp.workorder'),
             ('res_id', 'in', order_id_list),
             ('date', '>=', first_date.date()),
             ('date', '<=', last_date.date())], order='id desc')

        final_list = mail_message_attachment_ids + mail_message_ids
        _logger.info("===>> mail_message_ids : %s", mail_message_ids)
        message_activity_list = []
        count = 0
        res_users_obj = self.env['res.users']

        for mail_message_id in final_list.sorted(key='id', reverse=True):
            _logger.info("===>> mail_message_id : %s", mail_message_id)
            user_id = res_users_obj.search([
                '|', ('login', '=', mail_message_id.author_id.email),
                ('partner_id', '=', mail_message_id.author_id.id)])
            _logger.info("===>> author_id : %s", mail_message_id.author_id)
            _logger.info("===>> user_id : %s", user_id)

            for tracking_value_id in mail_message_id.sudo().tracking_value_ids:
                tracking_values = {}
                if tracking_value_id.field_type == 'boolean':
                    count += 1
                    tracking_values = {
                        'subject': tracking_value_id.field_desc or "",
                        'old_value': False if tracking_value_id.old_value_integer == 0 else True,
                        'new_value': False if tracking_value_id.new_value_integer == 0 else True,
                    }
                elif tracking_value_id.field_type == 'integer':
                    count += 1
                    tracking_values = {
                        'subject': tracking_value_id.field_desc or "",
                        'old_value': tracking_value_id.old_value_integer,
                        'new_value': tracking_value_id.new_value_integer,
                    }

                elif tracking_value_id.field_type in ['many2one', 'selection', 'char']:
                    count += 1
                    tracking_values = {
                        'subject': tracking_value_id.field_desc or "",
                        'old_value': tracking_value_id.old_value_char or "",
                        'new_value': tracking_value_id.new_value_char or "",
                    }
                elif tracking_value_id.field_type in ['datetime', 'date']:
                    count += 1
                    tracking_values = {
                        'subject': tracking_value_id.field_desc or "",
                        'old_value': tracking_value_id.old_value_datetime or "",
                        'new_value': tracking_value_id.new_value_datetime or "",
                    }

                elif tracking_value_id.field_type == 'float':
                    count += 1
                    tracking_values = {
                        'subject': tracking_value_id.field_desc or "",
                        'old_value': tracking_value_id.old_value_float or "",
                        'new_value': tracking_value_id.new_value_float or "",
                    }

                elif tracking_value_id.field_type == 'monetary':
                    count += 1
                    tracking_values = {
                        'subject': tracking_value_id.field_desc or "",
                        'old_value': tracking_value_id.old_value_monetary or "",
                        'new_value': tracking_value_id.new_value_monetary or "",
                    }

                elif tracking_value_id.field_type in ['text', 'html']:
                    count += 1
                    tracking_values = {
                        'subject': tracking_value_id.field_desc or "",
                        'old_value': tracking_value_id.old_value_text or "",
                        'new_value': tracking_value_id.new_value_text or "",
                    }
                if tracking_values:
                    tracking_values.update({
                        'message_id': mail_message_id.id,
                        'write_date': mail_message_id.write_date,
                        'create_date': mail_message_id.create_date,
                        "user_details": {
                            'id': user_id.id or "",
                            'name': user_id.name or "",
                            'profile_image': user_id and user_id.employee_id.profile_image_url or "",
                        }
                    })
                    message_activity_list.append(tracking_values)
        response_data = {
            "recordLength": count,
            "activity_list": message_activity_list,
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    def create_product(self, values):
        _logger.info("===>>create_product==")
        _logger.info("===>>values id: %s", values)
        product_id = self.env['product.product'].create(values)
        for attribute_value_id in values.get('attribute_value_ids'):
            self.env.cr.execute(
                "INSERT INTO product_attribute_value_product_product_rel("
                "product_product_id, product_attribute_value_id) VALUES (%s, %s)" % (
                    product_id.id, attribute_value_id))
        _logger.info("===>>product_id id: %s", product_id)
        return {'product_id': product_id.id}

    def update_product(self, product_id, values):
        _logger.info("===>>create_product==")
        _logger.info("===>>product_id id: %s", product_id)
        _logger.info("===>>values id: %s", values)
        try:
            product_id = self.env['product.product'].browse(product_id)
            _logger.info("===>>product_id id: %s", product_id)
            product_id.write(values)
            for attribute_value_id in values.get('attribute_value_ids'):
                self.env.cr.execute(
                    "INSERT INTO product_attribute_value_product_product_rel("
                    "product_product_id, product_attribute_value_id) VALUES (%s, %s)" % (
                        product_id.id, attribute_value_id))
            return {
                "result": True
            }
        except Exception as ex:
            _logger.info("Errors===: %s", str(ex))
            return {
                "result": False,
            }

    @api.multi
    def get_w_project_lead_data(self, user_id, brand_id, lead_id, search_keyword):
        _logger.info("===>>get_w_project_lead_data==")
        _logger.info("===>>user_id id: %s", user_id)
        _logger.info("===>>brand_id id: %s", brand_id)
        _logger.info("===>>lead_id id: %s", lead_id)
        _logger.info("===>>search_keyword id: %s", search_keyword)

        domain = [('production_id.lead_id.all_user_ids', 'in', [user_id]), ('brand_id', '=', brand_id), ('production_id.lead_id', '=', lead_id)]
        if search_keyword:
            domain += [('name', 'ilike', search_keyword)]

        work_order_ids = self.env['mrp.workorder'].search(domain, order='id desc')
        _logger.info("===>>work_order_ids id: %s", work_order_ids)

        new_task_count = len(work_order_ids.filtered(lambda r: r.state in ["pending", "ready"]))
        in_progress_task_count = len(work_order_ids.filtered(lambda r: r.state in ["progress"]))
        done_task_count = len(work_order_ids.filtered(lambda r: r.state in ["done"]))

        response_data = {
            "new_task_count": new_task_count,
            "done_task_count": done_task_count,
            'in_progress_task_count': in_progress_task_count,
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    @api.multi
    def create_lead_line_and_pre_quote_line(self, product_quote, product_leadline):
        _logger.info("===>>get_w_project_lead_data==")
        cll_obj = self.env['crm.lead.lines']
        clpq_obj = self.env['crm.lead.product.quotes']
        _logger.info("===>>Product_quote id: %s", product_quote)
        _logger.info("===>>Product_leadline id: %s", product_leadline)
        product_quote_id = clpq_obj.search([
            ('product_tmp_id', '=', product_quote.get('product_tmp_id')),
            ('quotation_number', '=', product_quote.get('quotation_number'))], limit=1, order='id desc')
        if not product_quote_id:
            product_quote_id = clpq_obj.create({
                "product_tmp_id": product_quote.get('product_tmp_id'),
                "quotation_number": product_quote.get('quotation_number'),
                "crm_lead_id": product_quote.get('crm_lead_id'),
                "currency_id": product_quote.get('currency_id'),
                "is_approval": product_quote.get('is_approval'),
                "is_fee": product_quote.get('is_fee'),
                "quote_type": product_quote.get('quote_type'),
                "is_billable": product_quote.get('is_billable'),
            })
        lead_line_ids = []
        for leadline in product_leadline:
            product_id = self.env['product.product'].search([('id', '=', leadline.get('product_id'))])
            _logger.info("===>>product_id.mapped('bom_ids') id: %s", product_id.mapped('bom_ids'))
            minutes = sum([mrw.time_cycle_manual for mrw in product_id.mapped('bom_ids.routing_id.operation_ids')])
            hours = 0.0
            if minutes:
                hours = minutes / 60
            lead_line_id = cll_obj.create({
                "product_id": leadline.get('product_id'),
                "product_uom_qty": leadline.get('product_uom_qty'),
                "crm_lead_id": leadline.get('crm_lead_id'),
                "order_date": leadline.get('order_date'),
                "name": leadline.get('name'),
                "product_uom": leadline.get('product_uom'),
                "price_unit": leadline.get('price_unit'),
                "price_update_reason": leadline.get('price_update_reason'),
                "tax_id": [(6, False, leadline.get('tax_id'))],
                "quotation_number": leadline.get('quotation_number'),
                "quote_type": leadline.get('quote_type'),
                "hours": hours,
            })
            lead_line_ids.append(lead_line_id.id)
        response_data = {
            "lead_line_ids": lead_line_ids,
            "product_quote_id": product_quote_id.ids,
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    def create_special_mo_and_tasks(self, lead_id, step_id):
        _logger.info("===>>create_special_mo_and_tasks==")
        _logger.info("===>>lead_id id: %s", lead_id)
        _logger.info("===>>step_id id: %s", step_id)
        mrp_prod_obj = self.env['mrp.production']
        mrp_bom_obj = self.env['mrp.bom']
        mrp_workcenter_obj = self.env['mrp.workcenter']
        mrp_routing_obj = self.env['mrp.routing']
        step_obj = self.env['step.step']
        mrp_rw_obj = self.env['mrp.routing.workcenter']
        mo_id = mrp_prod_obj.search([('lead_id', '=', lead_id), ('step_id', '=', step_id)], limit=1)
        step_id = step_obj.browse(step_id)
        lead_id = self.env['crm.lead'].browse(lead_id)
        if not step_id:
            return "Record Not Found related to step"
        _logger.info("===>>mo_id id: %s", mo_id)
        if not mo_id:
            product_id = self.env['product.product'].search([('product_name', '=', 'Special Product')], limit=1)
            if not product_id:
                product_id = self.env['product.product'].create({
                    'name': 'Special Product',
                    'product_name': 'Special Product',
                    'type': 'service',
                })
            code = 'Lead Id :' + str(lead_id.id) + ' - Step ID :' + str(step_id.id)
            # routing_id = mrp_routing_obj.search([('name', '=', 'Special Routing'), ('code', '=', code)])
            # if not routing_id:
            routing_id = mrp_routing_obj.create({
                'name': 'Special Routing',
                'code': code,
            })
            # bom_id = mrp_bom_obj.search([('product_id.product_name', '=', 'Special Product')], limit=1)
            # if not bom_id:
            bom_id = mrp_bom_obj.create({
                'product_id': product_id.id,
                'product_tmpl_id': product_id.product_tmpl_id.id,
                'product_uom_id': product_id.uom_id.id,
                'product_qty': 1.0,
                'type': 'normal',
                'routing_id': routing_id.id,
                # 'bom_line_ids': [
                #     (0, 0, {'product_id': product_id.id, 'product_qty': 1}),
                # ]
            })
            mo_id = mrp_prod_obj.create({
                'origin': code,
                'step_id': step_id.id,
                'lead_id': lead_id.id,
                'product_id': product_id.id,
                'product_uom_id': product_id.uom_id.id,
                'product_qty': 1,
                'bom_id': bom_id.id,
                'routing_id': routing_id.id,
                'brand_id': lead_id.brand_id.id,
            })

            work_center_id = mrp_workcenter_obj.search([('name', '=', 'Special Work Center')])
            if not work_center_id:
                work_center_id = mrp_workcenter_obj.create({
                    'costs_hour': 1,
                    'name': 'Special Work Center'
                })
            for page_id in step_id.page_ids:
                if not page_id.is_loghour:
                    continue
                mrp_rw_obj.create({
                    'name': page_id.title,
                    'workcenter_id': work_center_id.id,
                    'routing_id': routing_id.id,
                    'time_cycle': 1,
                    'page_id': page_id.id,
                    'sequence': 1,
                })
            mo_id.button_plan()
        response_data = {
            "production_id": mo_id.id,
            "work_order_ids": mo_id.workorder_ids.ids,
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    def getOZStatistics(self):
        _logger.info("===>>getOZStatistics==")
        production_ids = self.env['mrp.production'].search([('lead_id', '!=', False)])
        total_projects = list(set(production_ids.mapped('lead_id')))
        # employee_ids = self.env['hr.employee'].search([
        #     ('work_group_id', '!=', False),
        #     ('user_id', '!=', False),
        #     ('job_id', '!=', False)])
        users_ids = self.env['res.users'].search([
            ('employee_id.work_group_id', '!=', False),
            ('employee_id.job_id', '!=', False)])

        client_ids = self.env['res.partner'].search([('customer', '=', True), ('customer_admin', '=', True)])
        vendors_ids = self.env['res.partner'].search([('supplier', '=', True)])
        total_hours = 0
        total_pending_tasks = 0
        for workorder_id in production_ids.mapped('workorder_ids'):
            if workorder_id.state != 'done':
                total_pending_tasks += 1
            total_hours += workorder_id.duration_expected

        project_types_data = {}
        for total_project in total_projects:
            if not project_types_data.get(total_project.crm_lead_type_id.id):
                project_types_data[total_project.crm_lead_type_id.id] = {
                    'total_projects': 1,
                    'project_type_id': total_project.crm_lead_type_id.id,
                    'project_type_name': total_project.crm_lead_type_id.name,
                }
            else:
                project_types_data[total_project.crm_lead_type_id.id]['total_projects'] += 1

        final_project_datas = []
        for ptd in project_types_data:
            final_project_datas.append(project_types_data.get(ptd))
        response_data = {
            "total_projects": len(total_projects),
            "total_hours": total_hours / 60,
            "total_pending_tasks": total_pending_tasks,
            "total_users": len(users_ids),
            "total_clients": len(client_ids),
            "total_vendors": len(vendors_ids),
            "project_types": final_project_datas,
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    def daterange(self, date1, date2):
        for n in range(int((date2 - date1).days) + 1):
            yield date1 + timedelta(n)

    def getOZList(self, search_keyword, limit=8, offset=0, start_date=False, end_date=False):
        _logger.info("===>>getOZList==")
        _logger.info("===>>search_keyword id: %s", search_keyword)
        _logger.info("===>>limit id: %s", limit)
        _logger.info("===>>offset id: %s", offset)
        _logger.info("===>>start_date id: %s", start_date)
        _logger.info("===>>end_date id: %s", end_date)
        domain = []
        if search_keyword:
            domain = [('name', 'ilike', search_keyword)]

        weekdays = [5, 6]
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        total_working_days = 0

        for dt in self.daterange(start_date, end_date):
            if dt.weekday() not in weekdays:
                total_working_days += 1

        work_group_ids_length = self.env['work.group'].search(domain)
        work_group_ids = self.env['work.group'].search(domain, limit=limit, offset=offset, order='name')
        work_group_details = []
        mw_object = self.env['mrp.workorder']

        for work_group_id in work_group_ids:
            users_ids = self.env['res.users'].search([
                 ('employee_id.work_group_id', '=', work_group_id.id),
                 ('employee_id.job_id', '!=', False)])
            production_ids = self.env['mrp.production'].search([
                ('lead_id', '!=', False),
                ('lead_id.all_user_ids', 'in', users_ids.ids)])
            total_tasks = sum(production_ids.mapped('workorder_count'))

            workorder_ids = production_ids.mapped('workorder_ids').mapped('id')
            mw_ids = mw_object.search([
                ('date_start', '>=', start_date),
                ('date_finished', '<=', end_date),
                ('id', 'in', workorder_ids)
            ])
            planned_hours = 0.0
            worklog_hours = 0.0
            for workorder_id in mw_ids:
                planned_hours += workorder_id.duration_expected
                worklog_hours += workorder_id.spent_time
            total_projects = list(set(production_ids.mapped('lead_id')))
            work_group_details.append({
                 "name": work_group_id.name,
                 "id": work_group_id.id,
                 "total_users": len(users_ids),
                 "total_project": len(total_projects),
                 "total_tasks": total_tasks,
                 "total_hours": total_working_days * 8 * len(users_ids),
                 "planned_hours": planned_hours / 60,
                 "worklog_hours": worklog_hours / 60,
            })
        response_data = {
            "work_group_details": work_group_details,
            "recordLength": len(work_group_ids_length),
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    def getOZProfiles(self, operationzoneid, start_date=False, end_date=False):
        _logger.info("===>>getOZProfiles==")
        _logger.info("===>>operationzoneid id: %s", operationzoneid)
        _logger.info("===>>start_date id: %s", start_date)
        _logger.info("===>>end_date id: %s", end_date)

        weekdays = [5, 6]
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        total_working_days = 0

        for dt in self.daterange(start_date, end_date):
            if dt.weekday() not in weekdays:
                total_working_days += 1

        _logger.info("===>>total_working_days : %s", total_working_days)
        work_group_id = self.env['work.group'].browse(operationzoneid)
        if not work_group_id:
            return {}

        total_users = self.env['res.users'].search([
            ('employee_id.work_group_id', '=', work_group_id.id),
            ('employee_id.job_id', '!=', False)])

        _logger.info("===>>total_users : %s", len(total_users))
        production_ids = self.env['mrp.production'].search([
            ('lead_id', '!=', False),
            ('lead_id.all_user_ids', 'in', total_users.ids)])

        total_projects = list(set(production_ids.mapped('lead_id')))
        profile_list = []

        mw_object = self.env['mrp.workorder']
        mwp_object = self.env['mrp.workcenter.productivity']

        total_total_hours = total_working_days * 8 * len(total_users)
        total_planned_hours = 0
        total_worklog_hours = 0

        workorder_ids = production_ids.mapped('workorder_ids').mapped('id')
        profile_type_data = {}
        for user_id in total_users:
            job_id = user_id.employee_id.job_id
            mwp_ids = mwp_object.search([
                ('date_start', '>=', start_date),
                ('date_end', '<=', end_date),
                ('user_id', '=', user_id.id),
                ('workorder_id', 'in', workorder_ids)
            ])
            worklog_hours = sum(mwp_ids.mapped('duration')) / 60
            mw_ids = mw_object.search([
                ('date_start', '>=', start_date),
                ('date_finished', '<=', end_date),
                ('assign_id', '=', user_id.id),
                ('id', 'in', workorder_ids)
            ])
            planned_hours = sum(mw_ids.mapped('duration_expected')) / 60
            total_planned_hours += planned_hours
            total_worklog_hours += worklog_hours
            twd = total_working_days * 8 * 1
            if not profile_type_data.get(job_id.id):
                profile_type_data[job_id.id] = {
                    "name": job_id.name,
                    "id": job_id.id,
                    "total_employees": 1,
                    "color_code": job_id.color_code,
                    "total_hours": twd,
                    "planned_hours": planned_hours,
                    "worklog_hours": worklog_hours,
                }
            else:
                profile_type_data[job_id.id]['total_employees'] += 1
                profile_type_data[job_id.id]['total_hours'] += twd
                profile_type_data[job_id.id]['planned_hours'] += planned_hours
                profile_type_data[job_id.id]['worklog_hours'] += worklog_hours
        for i in profile_type_data:
            profile_list.append(profile_type_data.get(i))
        profile_list_sorted = sorted(profile_list, key=itemgetter('total_employees'),reverse = True)

        data = {
            "name": work_group_id.name,
            "id": work_group_id.id,
            "total_users": len(total_users),
            "total_project": len(total_projects),
            "total_hours":  total_total_hours, #total_working_days * 8 * len(total_users),
            "planned_hours": total_planned_hours,
            "worklog_hours": total_worklog_hours,
            "profile_list": profile_list_sorted,
        }
        response_data = {
            "data": data,
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    def get_custom_asset_data(self, brand_id, type=False, lead_id=False, date_range=False, limit=10, offset=1):
        if not limit:
            limit = 10
        if not offset:
            offset = 0
        _logger.info("===>>get_custom_asset_data==")
        _logger.info("===>>brand_id id: %s", brand_id)
        _logger.info("===>>type id: %s", type)
        _logger.info("===>>lead_id id: %s", lead_id)
        _logger.info("===>>date_range id: %s", date_range)
        _logger.info("===>>limit id: %s", limit)
        _logger.info("===>>offset id: %s", offset)
        domain = [('brand_id', '=', brand_id), ('lead_line_id.quote_type', 'in', ['PR', 'DC', 'EP'])]
        production_ids = self.env['mrp.production'].search(domain)
        total_pr = 0
        total_dc = 0
        total_ep = 0
        for production_id in production_ids:
            if production_id.lead_line_id.quote_type == 'PR':
                total_pr += 1
            elif production_id.lead_line_id.quote_type == 'DC':
                total_dc += 1
            elif production_id.lead_line_id.quote_type == 'EP':
                total_ep += 1

        domain = [('brand_id', '=', brand_id)]
        if type:
            domain += [('lead_line_id.quote_type', '=', type)]
        else:
            domain += [('lead_line_id.quote_type', 'in', ['PR', 'DC', 'EP'])]

        if lead_id:
            domain += [('lead_id', '=', lead_id)]

        if date_range:
            range_date = datetime.now() - timedelta(days=date_range)
            domain += [('create_date', '>=', range_date.date())]
        _logger.info("===>>domain id: %s", domain)

        asset_list = []
        production_ids = self.env['mrp.production'].search(domain, limit=limit, offset=offset, order='id desc')
        for production_id in production_ids:
            asset_list.append({
                "mo_id": production_id.id,
                "product_name": [production_id.product_id.id, production_id.product_id.product_name],
                "vendor": [production_id.lead_line_id.res_supplier_id.id, production_id.lead_line_id.res_supplier_id.name],
                "date": production_id.lead_line_id.order_date,
                "quote_type": production_id.lead_line_id.quote_type,
                "lead_id": [production_id.lead_id.id, production_id.lead_id.name],
                "product_template": [production_id.product_tmpl_id.id, production_id.product_tmpl_id.name],
                "create_date": production_id.create_date,
            })
        response_data = {
            "total_counts": {
                "total_dc": total_dc,
                "total_pr": total_pr,
                "total_ep": total_ep
            },
            "asset_list": asset_list
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    def getOZTaskOverview(self, operationzoneid, client_ids, brand_ids, project_ids, profile_ids, resource_ids, start_date, end_date):
        _logger.info("===>>getOZTaskOverview==")
        _logger.info("===>>operationzoneid id: %s", operationzoneid)
        _logger.info("===>>client_ids: %s", client_ids)
        _logger.info("===>>brand_ids: %s", brand_ids)
        _logger.info("===>>project_ids: %s", project_ids)
        _logger.info("===>>profile_ids: %s", profile_ids)
        _logger.info("===>>resource_ids: %s", resource_ids)
        _logger.info("===>>start_date: %s", start_date)
        _logger.info("===>>end_date: %s", end_date)

        work_group_id = self.env['work.group'].browse(operationzoneid)
        if not work_group_id:
            return {}

        total_users = self.env['res.users'].search([
            ('employee_id.work_group_id', '=', work_group_id.id),
            ('employee_id.job_id', '!=', False)])

        _logger.info("===>>total_users : %s", len(total_users))
        domain = [('lead_id', '!=', False)]
        if client_ids:
            domain += [('lead_id.partner_id', 'in', client_ids)]

        if brand_ids:
            domain += [('brand_id', 'in', client_ids)]

        if project_ids:
            domain += [('lead_id', 'in', project_ids)]

        if profile_ids:
            profile_users = self.env['res.users'].search([
                ('employee_id.work_group_id', '=', work_group_id.id),
                ('employee_id.job_id', 'in', profile_ids)])
            domain += [('lead_id.all_user_ids', 'in', profile_users.ids)]
        else:
            domain += [('lead_id.all_user_ids', 'in', total_users.ids)]

        if resource_ids:
            resource_users = self.env['res.users'].search([
                ('employee_id.work_group_id', '=', work_group_id.id),
                ('id', 'in', resource_ids)])
            domain += [('lead_id.all_user_ids', 'in', resource_users.ids)]

        production_ids = self.env['mrp.production'].search(domain)

        _logger.info("===>>production_ids: %s", production_ids)
        mw_object = self.env['mrp.workorder']

        workorderids = production_ids.mapped('workorder_ids').mapped('id')
        _logger.info("===>>workorderids: %s", workorderids)

        workorder_ids = mw_object.search([
            ('date_start', '>=', start_date),
            ('date_finished', '<=', end_date),
            ('id', 'in', workorderids)
        ])
        _logger.info("===>>workorder_ids: %s", workorder_ids)

        assigned_task_list = []
        unassigned_task_list = []
        for workorder_id in workorder_ids:
            vals = {
                    'id': workorder_id.id,
                    'task_name': workorder_id.name,
                    'state': workorder_id.state,
                    'estimated_duration': workorder_id.duration_expected and workorder_id.duration_expected / 60 or 0.0,
                    'start_date': workorder_id.date_start,
                    'end_date': workorder_id.date_finished,
                    'campaign_id': workorder_id.production_id.lead_id.id,
                    'campaign_name': workorder_id.production_id.lead_id.name,
                    'brand_id': workorder_id.brand_id.id or workorder_id.production_id.brand_id.id,
                    'brand_name': workorder_id.brand_id.name or workorder_id.production_id.brand_id.name,
                    'brand_reference': workorder_id.brand_id.brand_reference or workorder_id.production_id.brand_id.brand_reference,
                    'client_id': workorder_id.production_id.lead_id.partner_id.id,
                    'client_name': workorder_id.production_id.lead_id.partner_id.name,
                    'product_id': workorder_id.product_id.id,
                    'product_name': workorder_id.product_id.product_name,
                    'created_date': workorder_id.create_date,
                }
            if workorder_id.assign_id:
                user_id = workorder_id.assign_id
                vals.update({
                    'username': user_id.name or "",
                    'user_profile_image': user_id and user_id.employee_id.profile_image_url or "",
                    'user_profile_name': user_id.employee_id.job_id.name or user_id.job_profile_id.name or '',
                })
                assigned_task_list.append(vals)
            else:
                unassigned_task_list.append(vals)

        response_data = {
            "id": operationzoneid,
            "name": work_group_id.name,
            "total_users": len(total_users),
            "assigned_task_list": assigned_task_list,
            "unassigned_task_list": unassigned_task_list,
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    def getOZProjects(self, operationzoneid):
        users_ids = self.env['res.users'].search([
            ('employee_id.work_group_id', '=', operationzoneid),
            ('employee_id.job_id', '!=', False)])
        production_ids = self.env['mrp.production'].search([
            ('lead_id', '!=', False),
            ('lead_id.all_user_ids', 'in', users_ids.ids)])
        total_projects = list(set(production_ids.mapped('lead_id')))
        project_list = []
        for project_id in total_projects:
            project_list.append({
                'id': project_id.id,
                'name': project_id.name,
            })
        response_data = {
            "recordLength": len(total_projects),
            "project_list": project_list
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    def getOZResourceList(self, operationzoneid, client_ids, brand_ids, project_ids, profile_ids, resource_ids, limit, offset):
        _logger.info("===>>getOZResourceList==")
        _logger.info("===>>operationzoneid id: %s", operationzoneid)
        _logger.info("===>>client_ids: %s", client_ids)
        _logger.info("===>>brand_ids: %s", brand_ids)
        _logger.info("===>>project_ids: %s", project_ids)
        _logger.info("===>>profile_ids: %s", profile_ids)
        _logger.info("===>>resource_ids: %s", resource_ids)
        _logger.info("===>>limit: %s", limit)
        _logger.info("===>>offset: %s", offset)

        work_group_id = self.env['work.group'].browse(operationzoneid)
        if not work_group_id:
            return {}

        total_users = self.env['res.users'].search([
            ('employee_id.work_group_id', '=', work_group_id.id),
            ('employee_id.job_id', '!=', False)])

        _logger.info("===>>total_users : %s", len(total_users))
        if client_ids or brand_ids or project_ids or profile_ids or resource_ids:
            domain = [('lead_id', '!=', False)]
            if client_ids:
                domain += [('lead_id.partner_id', 'in', client_ids)]

            if brand_ids:
                domain += [('brand_id', 'in', client_ids)]

            if project_ids:
                domain += [('lead_id', 'in', project_ids)]

            if profile_ids:
                profile_users = self.env['res.users'].search([
                    ('employee_id.work_group_id', '=', work_group_id.id),
                    ('employee_id.job_id', 'in', profile_ids)])
                domain += [('lead_id.all_user_ids', 'in', profile_users.ids)]
            else:
                domain += [('lead_id.all_user_ids', 'in', total_users.ids)]

            if resource_ids:
                resource_users = self.env['res.users'].search([
                    ('employee_id.work_group_id', '=', work_group_id.id),
                    ('id', 'in', resource_ids)])
                domain += [('lead_id.all_user_ids', 'in', resource_users.ids)]

            production_ids = self.env['mrp.production'].search(domain)
            mw_object = self.env['mrp.workorder']
            workorderids = production_ids.mapped('workorder_ids').mapped('id')
            workorder_ids = mw_object.search([
                ('id', 'in', workorderids),
                ('assign_id', '!=', False),
            ])
            total_users = workorder_ids.mapped('assign_id')

        user_list = []
        user_ids = self.env['res.users'].search([('id', 'in', total_users.ids)], limit=limit, offset=offset, order='name')
        for user_id in user_ids:
            vals = {
                'id': user_id.id,
                'name': user_id.name or "",
                'profile_image_url': user_id and user_id.employee_id.profile_image_url or "",
                'job_position': user_id.employee_id.job_id.name or user_id.job_profile_id.name or '',
            }
            user_list.append(vals)

        response_data = {
            "id": operationzoneid,
            "name": work_group_id.name,
            "total_users": len(total_users),
            "user_list": user_list,
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    def getOZResourceTaskList(self, operationzoneid, user_id, start_date, end_date):
        _logger.info("===>>getOZResourceTaskList==")
        _logger.info("===>>operationzoneid id: %s", operationzoneid)
        _logger.info("===>>user_id: %s", user_id)
        _logger.info("===>>start_date: %s", start_date)
        _logger.info("===>>end_date: %s", end_date)

        user_id = self.env['res.users'].browse(user_id)

        job_id = user_id.employee_id.job_id or user_id.job_profile_id
        currency_id = user_id.company_id.currency_id

        total_users = self.env['res.users'].search([
            ('employee_id.work_group_id', '=', operationzoneid),
            ('employee_id.job_id', '!=', False)])

        _logger.info("===>>total_users : %s", len(total_users))

        domain = [('lead_id', '!=', False), ('lead_id.all_user_ids', 'in', total_users.ids)]
        production_ids = self.env['mrp.production'].search(domain)

        mw_object = self.env['mrp.workorder']

        workorderids = production_ids.mapped('workorder_ids').mapped('id')
        workorder_ids = mw_object.search([
            ('date_start', '>=', start_date),
            ('date_finished', '<=', end_date),
            ('id', 'in', workorderids),
            ('assign_id', '=', user_id.id),
        ], order='date_start')
        task_list = []
        total_spent_time = 0.0
        total_estimate_hour = 0.0
        for workorder_id in workorder_ids:
            total_spent_time += workorder_id.spent_time
            total_estimate_hour += workorder_id.duration_expected
            vals = {
                'id': workorder_id.id,
                'task_name': workorder_id.name,
                'state': workorder_id.state,
                'estimated_duration': workorder_id.duration_expected and workorder_id.duration_expected / 60 or 0.0,
                'start_date': workorder_id.date_start,
                'end_date': workorder_id.date_finished,
                'campaign_id': workorder_id.production_id.lead_id.id,
                'campaign_name': workorder_id.production_id.lead_id.name,
                'brand_id': workorder_id.brand_id.id or workorder_id.production_id.brand_id.id,
                'brand_name': workorder_id.brand_id.name or workorder_id.production_id.brand_id.name,
                'brand_reference': workorder_id.brand_id.brand_reference or workorder_id.production_id.brand_id.brand_reference,
                'client_id': workorder_id.production_id.lead_id.partner_id.id,
                'client_name': workorder_id.production_id.lead_id.partner_id.name,
                'product_id': workorder_id.product_id.id,
                'product_name': workorder_id.product_id.product_name,
            }
            task_list.append(vals)

        response_data = {
            "id": user_id.id,
            "name": user_id.name,
            'profile_image_url': user_id and user_id.employee_id.profile_image_url or "",
            'job_position_id': job_id.id or '',
            'job_position_name': job_id.name or '',
            'profile_cost': job_id.group_id.cost_per_hour,
            'company_curreny': {
                'id': currency_id.id,
                'code': currency_id.name,
                'symbol': currency_id.symbol,
            },
            'total_spent_hour': total_spent_time / 60,
            'total_estimate_hour': total_estimate_hour / 60,
            'task_list': task_list,
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    def getOZResourceTaskDetail(self, task_id):
        _logger.info("===>>getOZResourceTaskDetail==")
        _logger.info("===>>task_id id: %s", task_id)
        workorder_id = self.env['mrp.workorder'].browse(task_id)
        response_data = {
            'id': workorder_id.id,
            'task_name': workorder_id.name,
            'state': workorder_id.state,
            'description': workorder_id.description,
            'estimated_duration': workorder_id.duration_expected and workorder_id.duration_expected / 60 or 0.0,
            'spent_time': workorder_id.spent_time and workorder_id.spent_time / 60,
            'start_date': workorder_id.date_start,
            'end_date': workorder_id.date_finished,
            'campaign_id': workorder_id.production_id.lead_id.id,
            'campaign_name': workorder_id.production_id.lead_id.name,
            'brand_id': workorder_id.brand_id.id or workorder_id.production_id.brand_id.id,
            'brand_name': workorder_id.brand_id.name or workorder_id.production_id.brand_id.name,
            'brand_reference': workorder_id.brand_id.brand_reference or workorder_id.production_id.brand_id.brand_reference,
            'client_id': workorder_id.production_id.lead_id.partner_id.id,
            'client_name': workorder_id.production_id.lead_id.partner_id.name,
            'product_id': workorder_id.product_id.id,
            'product_name': workorder_id.product_id.product_name,
            'production_id': workorder_id.production_id.id,
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    def getOZProjectList(self, operationzoneid, client_ids, brand_ids, project_ids, profile_ids, resource_ids, limit, offset):
        _logger.info("===>>getOZProjectList==")
        _logger.info("===>>operationzoneid id: %s", operationzoneid)
        _logger.info("===>>client_ids: %s", client_ids)
        _logger.info("===>>brand_ids: %s", brand_ids)
        _logger.info("===>>project_ids: %s", project_ids)
        _logger.info("===>>profile_ids: %s", profile_ids)
        _logger.info("===>>resource_ids: %s", resource_ids)
        _logger.info("===>>limit: %s", limit)
        _logger.info("===>>offset: %s", offset)

        work_group_id = self.env['work.group'].browse(operationzoneid)
        if not work_group_id:
            return {}

        total_users = self.env['res.users'].search([
            ('employee_id.work_group_id', '=', work_group_id.id),
            ('employee_id.job_id', '!=', False)])

        _logger.info("===>>total_users : %s", len(total_users))
        if client_ids or brand_ids or project_ids or profile_ids or resource_ids:
            domain = [('lead_id', '!=', False)]
            if client_ids:
                domain += [('lead_id.partner_id', 'in', client_ids)]

            if brand_ids:
                domain += [('brand_id', 'in', client_ids)]

            if project_ids:
                domain += [('lead_id', 'in', project_ids)]

            if profile_ids:
                profile_users = self.env['res.users'].search([
                    ('employee_id.work_group_id', '=', work_group_id.id),
                    ('employee_id.job_id', 'in', profile_ids)])
                domain += [('lead_id.all_user_ids', 'in', profile_users.ids)]
            else:
                domain += [('lead_id.all_user_ids', 'in', total_users.ids)]

            if resource_ids:
                resource_users = self.env['res.users'].search([
                    ('employee_id.work_group_id', '=', work_group_id.id),
                    ('id', 'in', resource_ids)])
                domain += [('lead_id.all_user_ids', 'in', resource_users.ids)]

            production_ids = self.env['mrp.production'].search(domain)
            mw_object = self.env['mrp.workorder']
            workorderids = production_ids.mapped('workorder_ids').mapped('id')
            workorder_ids = mw_object.search([
                ('id', 'in', workorderids),
                ('assign_id', '!=', False),
            ])
            total_users = workorder_ids.mapped('assign_id')

        lead_list = []
        total_lead_ids = self.env['crm.lead'].search([('all_user_ids', 'in', total_users.ids)], order='name')
        for lead_id in total_lead_ids[offset:limit+offset]:
            vals = {
                'id': lead_id.id,
                'name': lead_id.name or "",
            }
            lead_list.append(vals)

        response_data = {
            "id": operationzoneid,
            "name": work_group_id.name,
            "total_projects": len(total_lead_ids),
            "project_list": lead_list,
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    def getOZProjectResourceList(self, operationzoneid, project_id, start_date, end_date):
        _logger.info("===>>getOZProjectReportTaskList==")
        _logger.info("===>>operationzoneid id: %s", operationzoneid)
        _logger.info("===>>project_id: %s", project_id)
        _logger.info("===>>start_date: %s", start_date)
        _logger.info("===>>end_date: %s", end_date)

        work_group_id = self.env['work.group'].browse(operationzoneid)
        if not work_group_id:
            return {}

        domain = [('lead_id', '=', project_id)]
        production_ids = self.env['mrp.production'].search(domain)

        mw_object = self.env['mrp.workorder']

        workorder_ids = mw_object.search([
            ('date_start', '>=', start_date),
            ('date_finished', '<=', end_date),
            ('production_id', 'in', production_ids.ids),
            '|',
            ('assign_id.operation_zone', '=', work_group_id.name),
            ('assign_id.employee_id.work_group_id', '=', work_group_id.id)
        ], order='date_start')

        _logger.info("===>>workorder_ids: %s", workorder_ids)
        task_list = []
        final_list = {}
        for workorder_id in workorder_ids:
            user_id = workorder_id.assign_id
            job_id = user_id.employee_id.job_id or user_id.job_profile_id
            if workorder_id.assign_id.id not in final_list:
                final_list[workorder_id.assign_id.id] = {
                    "id": user_id.id,
                    "name": user_id.name,
                    'profile_image_url': user_id and user_id.employee_id.profile_image_url or "",
                    'job_position_id': job_id.id or '',
                    'job_position_name': job_id.name or '',
                    'profile_cost': job_id.group_id.cost_per_hour,
                    'task_list': [
                        {
                            'id': workorder_id.id,
                            'task_name': workorder_id.name,
                            'state': workorder_id.state,
                            'estimated_duration': workorder_id.duration_expected and workorder_id.duration_expected / 60 or 0.0,
                            'spent_time': workorder_id.spent_time and workorder_id.spent_time / 60,
                            'start_date': workorder_id.date_start,
                            'end_date': workorder_id.date_finished,
                        }
                    ]
                }
            else:
                final_list[workorder_id.assign_id.id]['task_list'].append({
                    'id': workorder_id.id,
                    'task_name': workorder_id.name,
                    'state': workorder_id.state,
                    'estimated_duration': workorder_id.duration_expected and workorder_id.duration_expected / 60 or 0.0,
                    'spent_time': workorder_id.spent_time and workorder_id.spent_time / 60,
                    'start_date': workorder_id.date_start,
                    'end_date': workorder_id.date_finished,
                })

        for i in final_list:
            task_list.append(final_list.get(i))
        final_task_list = sorted(task_list, key=itemgetter('name'))

        response_data = {
            "id": operationzoneid,
            "name": work_group_id.name,
            "task_list": final_task_list,
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    def getOZProjectReportTaskList(self, operationzoneid, project_id, start_date):
        _logger.info("===>>getOZProjectReportTaskList==")
        _logger.info("===>>operationzoneid id: %s", operationzoneid)
        _logger.info("===>>project_id: %s", project_id)
        _logger.info("===>>start_date: %s", start_date)

        work_group_id = self.env['work.group'].browse(operationzoneid)
        if not work_group_id:
            return {}

        domain = [('lead_id', '=', project_id)]
        production_ids = self.env['mrp.production'].search(domain)
        mw_object = self.env['mrp.workorder']

        workorder_ids = mw_object.search([
            ('date_start', '>=', start_date),
            ('date_start', '<=', start_date),
            ('production_id', 'in', production_ids.ids),
            '|',
            ('assign_id.operation_zone', '=', work_group_id.name),
            ('assign_id.employee_id.work_group_id', '=', work_group_id.id)
        ], order='date_start')

        _logger.info("===>>workorder_ids: %s", workorder_ids)

        task_list = []
        total_spent_time = 0.0
        total_estimate_hour = 0.0
        currency_id = False
        for workorder_id in workorder_ids:
            total_spent_time += workorder_id.spent_time
            total_estimate_hour += workorder_id.duration_expected
            user_id = workorder_id.assign_id
            if not currency_id:
                currency_id = user_id.company_id.currency_id
            job_id = user_id.employee_id.job_id or user_id.job_profile_id
            vals = {
                'id': workorder_id.id,
                'task_name': workorder_id.name,
                'state': workorder_id.state,
                'estimated_duration': workorder_id.duration_expected and workorder_id.duration_expected / 60 or 0.0,
                'spent_time': workorder_id.spent_time and workorder_id.spent_time / 60,
                'start_date': workorder_id.date_start,
                'end_date': workorder_id.date_finished,
                'campaign_id': workorder_id.production_id.lead_id.id,
                'campaign_name': workorder_id.production_id.lead_id.name,
                'brand_id': workorder_id.brand_id.id or workorder_id.production_id.brand_id.id,
                'brand_name': workorder_id.brand_id.name or workorder_id.production_id.brand_id.name,
                'brand_reference': workorder_id.brand_id.brand_reference or workorder_id.production_id.brand_id.brand_reference,
                'client_id': workorder_id.production_id.lead_id.partner_id.id,
                'client_name': workorder_id.production_id.lead_id.partner_id.name,
                'product_id': workorder_id.product_id.id,
                'product_name': workorder_id.product_id.product_name,
                'assignee_data': {
                    "id": user_id.id,
                    "name": user_id.name,
                    'profile_image_url': user_id and user_id.employee_id.profile_image_url or "",
                    'job_position_id': job_id.id or '',
                    'job_position_name': job_id.name or '',
                    'profile_cost': job_id.group_id.cost_per_hour,
                }
            }
            task_list.append(vals)

        response_data = {
            'company_curreny': {
                'id': currency_id and currency_id.id or False,
                'code': currency_id and currency_id.name or False,
                'symbol': currency_id and currency_id.symbol or False,
            },
            'task_list': task_list,
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data

    def create_new_product(self, vals, task_list):
        _logger.info("===>>create_new_product==")
        _logger.info("===>>vals: %s", vals)
        _logger.info("===>>task_list: %s", task_list)
        _logger.info("===>>create_special_mo_and_tasks==")
        mrp_bom_obj = self.env['mrp.bom']
        mrp_routing_obj = self.env['mrp.routing']
        mrp_rw_obj = self.env['mrp.routing.workcenter']
        product_id = self.env['product.product'].create(vals)
        code = 'R' + str(product_id.id)
        routing_id = mrp_routing_obj.create({
            'name': code,
            'code': code,
        })
        mrp_bom_obj.create({
            'product_id': product_id.id,
            'product_tmpl_id': product_id.product_tmpl_id.id,
            'product_uom_id': product_id.uom_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'routing_id': routing_id.id,
        })
        for t_vals in task_list:
            t_vals.update({'routing_id': routing_id.id})
            mrp_rw_obj.create(t_vals)
        response_data = {
            "product_id": [product_id.id, product_id.product_name],
        }
        _logger.info("===>> Response Json Data : %s", response_data)
        return response_data