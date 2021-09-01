# -*- coding: utf-8 -*-
# Copyright 2019-TODAY WSuite Products <wsuite-products@destiny.ws>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
import threading
import logging
_logger = logging.getLogger(__name__)


class AssigndataWizard(models.TransientModel):
    _name = 'assign.data.wizard'
    _description = 'Assign Data Wizard'

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
    _name = 'assign.brand.wizard'
    _description = 'Assign Brand Wizard'
    
    current_brand_id = fields.Many2one('multi.brand', 'Current Brand')
    brand_id = fields.Many2one('multi.brand', 'Assign Brand')
    
    @api.multi
    def action_multi_brand_assign_process_wplan_1(self):
        crm_lead_type_obj = self.env['crm.lead.type']
        crm_lead_type_ids = crm_lead_type_obj.search([('brand_id', '=', self.current_brand_id.id)])
        brand_name = ' ' + self.brand_id.name
        for crm_lead_type_id in crm_lead_type_ids:
            new_crm_lead_type = crm_lead_type_id.copy()
            new_parent_id = False
            if new_crm_lead_type.parent_crm_lead_type:
                new_parent_id = crm_lead_type_obj.search([('name', '=', new_crm_lead_type.parent_crm_lead_type.name), ('brand_id', '=', self.brand_id.id)], limit=1)
                if not new_parent_id:
                    new_parent_id = new_crm_lead_type.parent_crm_lead_type.copy()
                    new_parent_id.write({'brand_id': self.brand_id.id, 'name': new_parent_id.name})
            first_parent_id = new_parent_id
            while new_parent_id:
                old_parent_id = new_parent_id
                if new_parent_id.parent_crm_lead_type:
                    new_parent_id = crm_lead_type_obj.search([('name', '=', new_parent_id.parent_crm_lead_type.name), ('brand_id', '=', self.brand_id.id)], limit=1)
                    if not new_parent_id:
                        new_parent_id = new_parent_id.parent_crm_lead_type.copy()
                        old_parent_id.write({
                            'parent_crm_lead_type': new_parent_id.id,
                            'brand_id': self.brand_id.id,
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
                new_step_id.write({'title': step_title, 'brand_reference': self.brand_id.id})
                new_flow_id.write({'name': new_flow_id.name, 'step_id': new_step_id.id, 'brand_id': self.brand_id.id})
            new_crm_lead_type.write({
                'flows_ids': [(6, 0, flow_ids)],
                'brand_id': self.brand_id.id,
                'parent_crm_lead_type': first_parent_id and first_parent_id.id,
                'name': new_crm_lead_type.name,
                })
        body = (_('Plan related data assigned successfully from %s to %s branch!') % (self.current_brand_id.name, self.brand_id.name))
        self.current_brand_id.message_post(body=body)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.multi
    def action_multi_brand_assign_process_assets(self):
        message = 'Once this process finish it will give message in log of this %s branch!' % (self.current_brand_id.name)
        view_id = self.env.ref('multi_brand.assign_data_wizard').id
        thread = threading.Thread(target=self.assign_process_assets, args=())
        thread.start()
        res = {
            'name': _('Information'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'assign.data.wizard',
            'view_id': view_id,
            'target': 'new',
            'context': {'message': message},
        }
        return res

    @api.multi
    def action_multi_brand_assign_process_wplan(self):
        message = 'Once this process finish it will give message in log of this %s branch!' % (self.current_brand_id.name)
        view_id = self.env.ref('multi_brand.assign_data_wizard').id
        thread = threading.Thread(target=self.assign_process_wplan, args=())
        thread.start()
        res = {
            'name': _('Information'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'assign.data.wizard',
            'view_id': view_id,
            'target': 'new',
            'context': {'message': message},
        }
        return res

    @api.multi
    def assign_process_wplan(self):
        try:
            with api.Environment.manage():
                new_cr = self.pool.cursor()
                self = self.with_env(self.env(cr=new_cr))
                self.action_multi_brand_assign_process_wplan_1()
                new_cr.commit()
                new_cr.close()
                _logger.info("Asigned Process done successfuly")
            return {'type': 'ir.actions.act_window_close'}
        except Exception as error:
            _logger.info(error)

    @api.multi
    def assign_process_assets(self):
        try:
            with api.Environment.manage():
                new_cr = self.pool.cursor()
                self = self.with_env(self.env(cr=new_cr))
                self.action_multi_brand_assign_process_assets_1()
                new_cr.commit()
                new_cr.close()
                _logger.info("Asigned Process done successfuly")
            return {'type': 'ir.actions.act_window_close'}
        except Exception as error:
            _logger.info(error)

    @api.multi
    def action_multi_brand_assign_process_assets_1(self):
        # brand_name = ' ' + self.brand_id.name
        product_template_obj = self.env['product.template']
        bom_obj = self.env['mrp.bom']
        cated_ids = []
        for categ_id in self.current_brand_id.categ_ids:
            new_categ_id = categ_id.copy()
            new_categ_id.write({'name': new_categ_id.name, 'brand_id': self.brand_id.id})
            template_ids = product_template_obj.search([('categ_id', 'child_of', categ_id.ids)])
            for template_id in template_ids:
                check_bom_ids = []
                product_ids = self.env['product.product'].search([('product_tmpl_id', '=', template_id.id)])
                new_template_id = False
                if product_ids:
                    new_template_id = template_id.copy()
                    new_template_id.write({'categ_id': new_categ_id.id, 'name': new_template_id.name, 'brand_id': self.brand_id.id})
                default_template_unlink = []
                for product_id in product_ids:
                    new_product_id = product_id.copy()
                    default_template_unlink.append(new_product_id.product_tmpl_id.id)
                    new_product_id.write({
                        'name': product_id.name,
                        'product_name': product_id.product_name or '',
                        'brand_id': self.brand_id.id,
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
                                new_routing_id.write({'name': new_routing_id.name, 'brand_id': self.brand_id.id})
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
        self.brand_id.categ_ids = [(6, 0, cated_ids)]
        body = (_('Assets related data assigned successfully from %s to %s branch!') % (self.current_brand_id.name, self.brand_id.name))
        self.current_brand_id.message_post(body=body)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.multi
    def action_multi_brand_assign_process_both(self):
        self.action_multi_brand_assign_process_wplan()
        self.action_multi_brand_assign_process_assets()
