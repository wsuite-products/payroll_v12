# Copyright 2017 - 2018 Modoolar <info@modoolar.com>
# License LGPLv3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import models, fields, api, _
from odoo.osv import expression


class ProjectProject(models.Model):
    _inherit = "project.project"

    task_key_sequence_id = fields.Many2one(
        comodel_name="ir.sequence", string="Key Sequence", ondelete="restrict",
    )

    key = fields.Char(string="Key", size=10, required=True, index=True,)

    _sql_constraints = [
        ("project_key_unique", "UNIQUE(key)", "Project key must be unique!")
    ]

    @api.multi
    @api.onchange("name")
    def _onchange_project_name(self):
        for rec in self:
            if rec.name:
                rec.key = self.generate_project_key(rec.name)
            else:
                rec.key = ""

    @api.multi
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        # clear the key before copying the project
        default["key"] = self.generate_project_key(default["name"])
        project = super(ProjectProject, self).copy(default)
        return project

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "key" not in vals:
                if vals["name"]:
                    vals["key"] = self.generate_project_key(vals["name"])
                else:
                    vals["key"] = ""

        new_project = super(ProjectProject, self).create(vals_list)
        new_project.create_sequence()

        return new_project

    @api.multi
    def write(self, values):

        reindex = False

        if "key" in values:
            key = values["key"]
            reindex = self.key != key

        res = super(ProjectProject, self).write(values)

        if reindex:
            # Here we don't expect to have more than one record
            # because we can not have multiple projects with same KEY.
            self.update_sequence()
            self._reindex_task_keys()

        return res

    @api.multi
    def unlink(self):
        sequences_to_delete = []
        for project in self:
            sequences_to_delete.append(project.task_key_sequence_id.id)

        ret = super(ProjectProject, self).unlink()

        self.env["ir.sequence"].sudo().browse(sequences_to_delete).unlink()
        return ret

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        if name:
            domain = [
                "|",
                ("key", "ilike", name + "%"),
                ("name", operator, name),
            ]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ["&"] + domain
        projects = self.search(domain + args, limit=limit)
        return projects.name_get()

    def create_sequence(self):
        """
        This method creates ir.sequence fot the current project
        :return: Returns create sequence
        """
        self.ensure_one()
        sequence_data = self._prepare_sequence_data()
        sequence = self.env["ir.sequence"].sudo().create(sequence_data)
        self.write({"task_key_sequence_id": sequence.id})
        return sequence

    def update_sequence(self):
        """
        This method updates existing task sequence
        :return:
        """
        sequence_data = self._prepare_sequence_data(init=False)
        self.task_key_sequence_id.sudo().write(sequence_data)

    def _prepare_sequence_data(self, init=True):
        """
        This method prepares data for create/update_sequence methods
        :param init: Set to False in case you don't want to set initial values
        for number_increment and number_next_actual
        """
        values = {
            "name": "%s %s"
            % (_("Project task sequence for project "), self.name),
            "implementation": "standard",
            "code": "project.task.key.%s" % (self.id,),
            "prefix": "%s-" % (self.key,),
            "use_date_range": False,
            "active": False,
        }

        if init:
            values.update(dict(number_increment=1, number_next_actual=1))

        return values

    def get_next_task_key(self):
        key = self.sudo().task_key_sequence_id.next_by_id()
        tasks = self.env["project.task"].search([("key", "=", key)])
        if not tasks:
            return key
        return self.get_next_task_key()

    def generate_project_key(self, text):
        if not text:
            return ""
        data = text.strip().split(" ")
        if len(data) == 1:
            key = data[0][:3].upper()
        else:
            key = []
            for item in data:
                if item and item[0].isalnum():
                    key.append(item[0].upper())
            key = "".join(key)
        i = 2
        base_key = key
        while self._check_key_exists(key):
            key = "%s%s" % (base_key, i)
            i += 1
        return key

    def _check_key_exists(self, key):
        projects = self.with_context(active_test=False).search(
            [("key", "=", key)]
        )
        return bool(projects)

    @api.multi
    def _reindex_task_keys(self):
        """
        This method will reindex task keys of the current project.
        """
        self.ensure_one()

        reindex_query = """
        UPDATE project_task
        SET key = x.key
        FROM (
          SELECT t.id, p.key || '-' || split_part(t.key, '-', 2) AS key
          FROM project_task t
          INNER JOIN project_project p ON t.project_id = p.id
          WHERE t.project_id = %s
        ) AS x
        WHERE project_task.id = x.id;
        """

        self.env.cr.execute(reindex_query, (self.id,))
        self.env["project.task"].invalidate_cache(["key"], self.task_ids.ids)

    @api.model
    def _set_default_project_key(self):
        """
        This method will be called from the post_init hook in order to set
        default values on project.project and
        project.task, so we leave those tables nice and clean after module
        installation.
        :return:
        """
        for project in self.with_context(active_test=False).search(
            [("key", "=", False)]
        ):
            project.key = self.generate_project_key(project.name)
            project.create_sequence()

            for task in project.task_ids:
                task.key = project.get_next_task_key()
