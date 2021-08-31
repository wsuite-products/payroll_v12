# Copyright 2020 MathBenTech <info@mathben.tech>
# License AGPLv3.0 or later (https://www.gnu.org/licenses/agpl-3.0.en.html).

from odoo import models, fields, api


class ConvertProjectTaskTypeWizard(models.TransientModel):
    _name = "project.task.type.convert_wizard"
    _description = "Project task type convert Wizard"

    @api.model
    def default_get(self, lst_fields):
        result = super(ConvertProjectTaskTypeWizard, self).default_get(lst_fields)
        if self._context.get('active_model') == 'project.task.type' and 'type_ids' in lst_fields:
            result['type_ids'] = self._context.get('active_ids', [])
        return result

    type_ids = fields.Many2many(comodel_name='project.task.type', string='Stages converted from', required=True,
                                help="Select stages to convert from.")

    type_id = fields.Many2one(
        comodel_name="project.task.type",
        string="Stage converted to",
        required=True,
        help="Select the stage to convert to."
    )

    convert_undefined_stage = fields.Boolean(string="Convert undefined stage", default=False,
                                             help="Includes undefined stage tasks to be transferred.")

    @api.multi
    @api.model_cr
    def convert_project_task_type(self):
        """
        Move all project task with type_ids to type_id
        """
        lst_type_ids = [obj.id for obj in self.type_ids if obj.id != self.type_id.id]

        search_condition = []
        if self.convert_undefined_stage:
            search_condition.append('|')
            search_condition.append(('stage_id', '=', False))
        search_condition.append(('stage_id', 'in', lst_type_ids))
        # Include archived task
        search_condition += ['|', ('active', '=', False), ('active', '=', True)]
        project_task_ids = self.env["project.task"].search(search_condition)

        # Bypass all project.task model to ignore workflow
        # reproduce this command : project_task_ids.write({"stage_id": self.type_id.id})
        # Add wkf_state_id if exist in the project, this will show the task in Scrummer
        for task_id in project_task_ids:
            stage_has_workflow = bool(self.env["project.workflow.state"].search([("stage_id", "=", self.type_id.id)]))
            wkf_state_id = False
            if task_id.project_id.allow_workflow and task_id.workflow_id and stage_has_workflow:
                wkf_state_id = self.env["project.workflow.state"].search(
                    [("workflow_id", "=", project_task_ids[0].workflow_id.id), ("stage_id", "=", self.type_id.id)]).id

            if wkf_state_id:
                self._cr.execute('UPDATE project_task '
                                 'SET stage_id = %s, '
                                 'wkf_state_id = %s '
                                 'WHERE id = %s;',
                                 (self.type_id.id, wkf_state_id, task_id.id)
                                 )
            else:
                self._cr.execute('UPDATE project_task '
                                 'SET stage_id = %s '
                                 'WHERE id = %s;',
                                 (self.type_id.id, task_id.id)
                                 )

        # No need to commit. This will rollback if unlink crash
        # if project_task_ids:
        #     self._cr.commit()

        # Delete unused project.task.type after convert
        self.env["project.task.type"].browse(lst_type_ids).unlink()
        return {
            "type": "ir.actions.act_multi",
            "actions": [
                {"type": "ir.actions.act_window_close"},
                {"type": "ir.actions.act_view_reload"},
            ],
        }
