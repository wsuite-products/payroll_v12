# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class MRPProduction(models.Model):
    _inherit = 'mrp.production'

    sale_order_id = fields.Many2one('sale.order', 'Sale Order', track_visibility='onchange')
    sale_order_line_id = fields.Many2one('sale.order.line', 'Sale Order Line', track_visibility='onchange')
    purchase_order_id = fields.Many2one('purchase.order', 'Purchase Order', track_visibility='onchange')
    purchase_order_line_id = fields.Many2one(
        'purchase.order.line', 'Purchase Order Line', track_visibility='onchange')
    task_assignee_config = fields.Text(string='Task Assignee Config', track_visibility='onchange')
    quotation_number = fields.Char('#Quotation Number', track_visibility='onchange')
    lead_id = fields.Many2one('crm.lead', 'Lead', track_visibility='onchange')
    lead_line_id = fields.Many2one('crm.lead.lines', 'Lead Line', track_visibility='onchange')
    brand_id = fields.Many2one('multi.brand', 'Brand', track_visibility='onchange')
    step_id = fields.Many2one('step.step', track_visibility='onchange')
    comment_ids = fields.One2many('workorder.comment', 'production_id', string='Comments', track_visibility='onchange')

    @api.multi
    def _generate_workorders(self, exploded_boms):
        workorders = super(MRPProduction, self)._generate_workorders(exploded_boms)
        for operation in self.bom_id.routing_id.operation_ids:
            workorder_id = workorders.filtered(lambda workorder: workorder.operation_id == operation)
            if self.lead_line_id.description:
                description = self.lead_line_id.description + '\n' + operation.note
            else:
                description = operation.note
            workorder_id.write({
                'task_form_json': operation.task_form_json,
                'is_operational': operation.is_operational,
                'description': description,
                'brand_id': self.brand_id.id,
                'user_ids': [(6, 0, self.lead_id.all_user_ids.ids)],
                'page_id': operation.page_id.id,
            })
        return workorders

    @api.multi
    def action_cancel(self):
        self._cr.execute("UPDATE mrp_workorder SET state='cancel' where production_id in %s", (tuple(self.ids),))
        res = super(MRPProduction, self).action_cancel()
        if self.purchase_order_line_id:
            self.purchase_order_line_id.product_qty -= 1
            if self.purchase_order_line_id.product_qty <= 0:
                lines_qty = sum(self.purchase_order_id.order_line.mapped('product_qty'))
                if lines_qty <= 0:
                    self.purchase_order_id.button_cancel()
        return res

class WorkorderRejectHistory(models.Model):
    _name = 'workorder.reject.history'
    _description = 'WorkOrder Reject History'

    user_id = fields.Many2one(comodel_name="res.users", string="User")
    comment = fields.Text('Comment')
    workorder_id = fields.Many2one('mrp.workorder', string='WorkOrder')


class MRPWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    json_data = fields.Text('Json Data')
    task_form_json = fields.Text('Task Form Json')
    task_id = fields.Integer('W-Project Task Id', track_visibility='onchange')
    is_operational = fields.Boolean('Is Operational?', track_visibility='onchange')
    user_ids = fields.Many2many('res.users', string='Users', track_visibility='onchange')
    description = fields.Text('Description', track_visibility='onchange')
    responsible_id = fields.Many2one(
        comodel_name="res.users", string="Responsible", required=False, track_visibility='onchange'
    )
    assign_id = fields.Many2one(
        comodel_name="res.users", string="Assign", required=False, track_visibility='onchange'
    )
    # comment_ids = fields.One2many('workorder.comment', 'order_id', string='Comments', track_visibility='onchange')
    brand_id = fields.Many2one('multi.brand', 'Brand', track_visibility='onchange')
    spent_time = fields.Float('Spent Time')
    watcher_ids = fields.Many2many(
        'res.users',
        'mrp_work_order_watcher_user_details',
        'work_order_id',
        'user_id',
        string='Watchers', track_visibility='onchange')
    date_planned_start = fields.Datetime(track_visibility='onchange')
    date_planned_finished = fields.Datetime(track_visibility='onchange')
    # date_start = fields.Datetime(track_visibility='onchange')
    # date_finished = fields.Datetime(track_visibility='onchange')
    # state = fields.Selection(track_visibility='onchange')
    page_id = fields.Many2one('step.page', 'Pages', track_visibility='onchange')
    re_open = fields.Boolean('Re-Open?', track_visibility='onchange')
    state = fields.Selection(selection_add=[('re_open', 'Re-Open')], track_visibility='onchange')
    production_id = fields.Many2one(
        'mrp.production', 'Manufacturing Order',
        index=True, ondelete='cascade', required=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})

    reject_ids = fields.One2many('workorder.reject.history', 'workorder_id', string='Reject History')

    def action_reopen(self):
        self._cr.execute("UPDATE mrp_workorder SET state = %s, re_open = %s WHERE id = %s", ['progress', True, self.id])
        return True

    def action_reject_history(self, user_id, workorder_id, comment):
        workorder_id = self.env['mrp.workorder'].browse(workorder_id)
        if not workorder_id:
            return "Record Not Found!"
        workorder_id.state = 'cancel'
        self.env['workorder.reject.history'].create({
            'user_id': user_id,
            'comment': comment,
            'workorder_id': workorder_id.id,
        })
        if workorder_id.next_work_order_id and workorder_id.next_work_order_id.state == 'pending':
            workorder_id.next_work_order_id.state = 'ready'
        return True


class WorkorderComment(models.Model):
    _name = 'workorder.comment'
    _inherit = ["mail.thread"]
    _description = 'WorkOrder Comment'

    sequence = fields.Integer('Sequence', default=10)
    comment = fields.Text('Comments', track_visibility='onchange')
    user_id = fields.Many2one('res.users')
    attachment = fields.Binary('Attachment', track_visibility='onchange')
    file_name = fields.Char("File Name", track_visibility='onchange')
    attachment_url = fields.Char('Attachment URL')
    order_id = fields.Many2one('mrp.workorder', string='WorkOrder')
    filesize = fields.Char('File Size')
    type = fields.Selection([('comment', 'Comments'), ('attachment', 'Attachment')], string="Type")
    final_asset = fields.Boolean('Final Asset?')
    production_id = fields.Many2one('mrp.production', 'Manufacturing Order')


class MRPRoutingWorkCenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    page_id = fields.Many2one('step.page', 'Pages')


class MrpWorkcenterProductivity(models.Model):
    _name = "mrp.workcenter.productivity"
    _inherit = ["mail.thread", "mrp.workcenter.productivity"]

    description = fields.Text(track_visibility='onchange')
    duration = fields.Float(track_visibility='onchange')
