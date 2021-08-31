# Copyright 2020 MathBenTech <info@mathben.tech>
# License AGPLv3.0 or later (https://www.gnu.org/licenses/agpl-3.0.en.html).

from odoo import models, fields, api


class ConvertTaskType2Wizard(models.TransientModel):
    _name = "project.task.convert_type2_wizard"
    _description = "Project Task Convert Type2 Wizard"

    @api.model
    def default_get(self, lst_fields):
        result = super(ConvertTaskType2Wizard, self).default_get(lst_fields)
        if self._context.get('active_model') == 'project.task' and 'task_ids' in lst_fields:
            result['task_ids'] = self._context.get('active_ids', [])
        return result

    task_ids = fields.Many2many(comodel_name='project.task', string='Tasks to converted', required=True,
                                help="Select tasks to convert.")

    type_id = fields.Many2one(
        comodel_name="project.task.type2", string="Task Type", required=True, help="Select task type to convert."
    )

    @api.multi
    def convert_project_task_type2(self):
        # TODO need to check the task type2 available with the project
        for task_id in self.task_ids:
            task_id.type_id = self.type_id

        return {
            "type": "ir.actions.act_multi",
            "actions": [
                {"type": "ir.actions.act_window_close"},
                {"type": "ir.actions.act_view_reload"},
            ],
        }
