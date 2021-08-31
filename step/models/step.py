# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
import logging
import re
import uuid
from collections import Counter, OrderedDict
from itertools import product
from werkzeug import urls
import base64

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.addons.http_routing.models.ir_http import slug
from odoo.exceptions import UserError, ValidationError
email_validator = re.compile(r"[^@]+@[^@]+\.[^@]+")
_logger = logging.getLogger(__name__)


def dict_keys_startswith(dictionary, string):
    """Returns a dictionary containing the elements of <dict>
    whose keys start with <string>.
        .. note::
            This function uses dictionary comprehensions (Python >= 2.7)
    """
    return {k: v for k, v in dictionary.items() if k.startswith(string)}


class StepStage(models.Model):
    """Stages for Kanban view of steps"""

    _name = 'step.stage'
    _description = 'Step Stage'
    _order = 'sequence,id'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=1)
    closed = fields.Boolean(
        help="If closed, people won't be able "
             "to answer to steps in this column.")
    fold = fields.Boolean(string="Folded in kanban view")

    _sql_constraints = [
        ('positive_sequence',
         'CHECK(sequence >= 0)',
         'Sequence number MUST be a natural')
    ]


class Step(models.Model):
    """ Settings for a multi-page/multi-question step.
        Each step can have one or more attached pages,
        and each page can display one or more questions.
    """

    _name = 'step.step'
    _description = 'Step'
    _rec_name = 'title'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_stage(self):
        return self.env['step.stage'].search([], limit=1).id

    title = fields.Char('Title', required=True, translate=True)
    page_ids = fields.One2many('step.page', 'step_id',
                               string='Pages', copy=True)
    stage_id = fields.Many2one(
        'step.stage', string="Stage",
        default=_default_stage, ondelete="restrict",
        copy=False, group_expand='_read_group_stage_ids')
    auth_required = fields.Boolean(
        'Login required',
        help="Users with a public link will be requested "
             "to login before taking part to the step",
        oldname="authenticate")
    users_can_go_back = fields.Boolean(
        'Users can go back',
        help="If checked, users can go back to previous pages.")
    tot_sent_step = fields.Integer(
        "Number of sent steps", compute="_compute_step_statistic")
    tot_start_step = fields.Integer(
        "Number of started steps", compute="_compute_step_statistic")
    tot_comp_step = fields.Integer(
        "Number of completed steps",
        compute="_compute_step_statistic")
    description = fields.Html(
        "Description", translate=True,
        help="A long description of the purpose of the step")
    color = fields.Integer('Color Index', default=0)
    user_input_ids = fields.One2many(
        'step.user_input', 'step_id', string='User responses', readonly=True)
    designed = fields.Boolean("Is designed?", compute="_is_designed")
    public_url = fields.Char("Public link", compute="_compute_step_url")
    public_url_html = fields.Char(
        "Public link (html version)", compute="_compute_step_url")
    print_url = fields.Char("Print link", compute="_compute_step_url")
    result_url = fields.Char("Results link", compute="_compute_step_url")
    email_template_id = fields.Many2one(
        'mail.template', string='Email Template', ondelete='set null')
    thank_you_message = fields.Html(
        "Thanks Message", translate=True,
        help="This message will be displayed when step is completed")
    quizz_mode = fields.Boolean("Quizz Mode")
    active = fields.Boolean("Active", default=True)
    is_closed = fields.Boolean(
        "Is closed", related='stage_id.closed', readonly=False)
    sequence = fields.Integer(default=1)
    brand_reference = fields.Integer('Brand Reference')

    def _is_designed(self):
        for step in self:
            if not step.page_ids or not \
                    [page.question_ids for page in step.page_ids
                     if page.question_ids]:
                step.designed = False
            else:
                step.designed = True

    @api.multi
    def _compute_step_statistic(self):
        UserInput = self.env['step.user_input']

        sent_step = UserInput.search([
            ('step_id', 'in', self.ids),
            ('type', '=', 'link')])
        start_step = UserInput.search(
            ['&', ('step_id', 'in', self.ids),
             '|', ('state', '=', 'skip'),
             ('state', '=', 'done')])
        complete_step = UserInput.search(
            [('step_id', 'in', self.ids),
             ('state', '=', 'done')])

        for step in self:
            step.tot_sent_step = len(sent_step.filtered(
                lambda user_input: user_input.step_id == step))
            step.tot_start_step = len(start_step.filtered(
                lambda user_input: user_input.step_id == step))
            step.tot_comp_step = len(complete_step.filtered(
                lambda user_input: user_input.step_id == step))

    def _compute_step_url(self):
        """ Computes a public URL for the step """
        base_url = '/' if self.env.context.get('relative_url') else \
                   self.env['ir.config_parameter'].sudo().get_param(
                       'web.base.url')
        for step in self:
            step.public_url = \
                urls.url_join(base_url, "step/start/%s" % (slug(step)))
            step.print_url = \
                urls.url_join(base_url, "step/print/%s" % (slug(step)))
            step.result_url = \
                urls.url_join(base_url, "step/results/%s" % (slug(step)))
            step.public_url_html = \
                '<a href="%s">%s</a>' % (step.public_url, _(
                    "Click here to start step"))

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """ Read group customization in order to display all the stages in the
            kanban view, even if they are empty
        """
        stage_ids = stages._search(
            [], order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    # Public methods #
    def copy_data(self, default=None):
        title = _("%s (copy)") % (self.title)
        default = dict(default or {}, title=title)
        return super(Step, self).copy_data(default)

    @api.model
    def next_page(self, user_input, page_id, go_back=False):
        """ The next page to display to the user,
         knowing that page_id is the id of the last displayed page.

            If page_id == 0, it will always return the first page of the step.

            If all the pages have been displayed and go_back == False, it will
            return None

            If go_back == True, it will return the
            *previous* page instead of the next page.

            .. note::
                It is assumed here that a careful user will not
                try to set go_back to True if she knows that the
                page to display is the first one! (doing this will
                 probably cause a giant worm to eat her house)
        """
        step = user_input.step_id
        pages = list(enumerate(step.page_ids))

        # First page
        if page_id == 0:
            return (pages[0][1], 0, len(pages) == 1)

        current_page_index = pages.index(
            next(p for p in pages if p[1].id == page_id))

        # All the pages have been displayed
        if current_page_index == len(pages) - 1 and not go_back:
            return (None, -1, False)
        # Let's get back, baby!
        elif go_back and step.users_can_go_back:
            return (pages[current_page_index - 1][1],
                    current_page_index - 1, False)
        else:
            # This will show the last page
            if current_page_index == len(pages) - 2:
                return (pages[current_page_index + 1][1],
                        current_page_index + 1, True)
            # This will show a regular page
            else:
                return (pages[current_page_index + 1][1],
                        current_page_index + 1, False)

    @api.multi
    def filter_input_ids(self, filters, finished=False):
        """If user applies any filters, then this function returns list of
           filtered user_input_id and label's strings for display data in web.
           :param filters: list of dictionary (having: row_id, ansewr_id)
           :param finished: True for completely filled step,Falser otherwise.
           :returns list of filtered user_input_ids.
        """
        self.ensure_one()
        if filters:
            domain_filter, choice = [], []
            for current_filter in filters:
                row_id, answer_id = \
                    current_filter['row_id'], current_filter['answer_id']
                if row_id == 0:
                    choice.append(answer_id)
                else:
                    domain_filter.extend([
                        '|', ('value_suggested_row.id', '=', row_id),
                        ('value_suggested.id', '=', answer_id)])
            if choice:
                domain_filter.insert(0, ('value_suggested.id', 'in', choice))
            else:
                domain_filter = domain_filter[1:]
            input_lines = \
                self.env['step.user_input_line'].search(domain_filter)
            filtered_input_ids = [
                input_line.user_input_id.id for input_line in input_lines]
        else:
            filtered_input_ids = []
        if finished:
            UserInput = self.env['step.user_input']
            if not filtered_input_ids:
                user_inputs = UserInput.search([('step_id', '=', self.id)])
            else:
                user_inputs = UserInput.browse(filtered_input_ids)
            return user_inputs.filtered(
                lambda input_item: input_item.state == 'done').ids
        return filtered_input_ids

    @api.model
    def get_filter_display_data(self, filters):
        """Returns data to display current filters
            :param filters: list of dictionary (having: row_id, answer_id)
            :returns list of dict having data to display filters.
        """
        filter_display_data = []
        if filters:
            Label = self.env['step.label']
            for current_filter in filters:
                row_id, answer_id = \
                    current_filter['row_id'], current_filter['answer_id']
                label = Label.browse(answer_id)
                question = label.question_id
                if row_id == 0:
                    labels = label
                else:
                    labels = Label.browse([row_id, answer_id])
                filter_display_data.append({'question_text': question.question,
                                            'labels': labels.mapped('value')})
        return filter_display_data

    @api.model
    def prepare_result(self, question, current_filters=None):
        """ Compute statistical data for questions by counting
        number of vote per choice on basis of filter """
        current_filters = current_filters if current_filters else []
        result_summary = {}

        # Calculate and return statistics for choice
        if question.type in ['simple_choice', 'multiple_choice']:
            comments = []
            answers = OrderedDict(
                (label.id, {
                    'text': label.value,
                    'count': 0, 'answer_id': label.id
                }) for label in question.labels_ids)
            for input_line in question.user_input_line_ids:
                if input_line.answer_type == 'suggestion' and \
                        answers.get(input_line.value_suggested.id) and \
                        (not current_filters or
                         input_line.user_input_id.id in current_filters):
                    answers[input_line.value_suggested.id]['count'] += 1
                if input_line.answer_type == 'text' and \
                        (not current_filters or
                         input_line.user_input_id.id in current_filters):
                    comments.append(input_line)
            result_summary = {
                'answers': list(answers.values()),
                'comments': comments}

        # Calculate and return statistics for matrix
        if question.type == 'matrix':
            rows = OrderedDict()
            answers = OrderedDict()
            res = dict()
            comments = []
            [rows.update({label.id: label.value}
                         ) for label in question.labels_ids_2]
            [answers.update({label.id: label.value}
                            ) for label in question.labels_ids]
            for cell in product(rows, answers):
                res[cell] = 0
            for input_line in question.user_input_line_ids:
                if input_line.answer_type == 'suggestion' and \
                        (not current_filters or input_line.user_input_id.id in
                         current_filters) and input_line.value_suggested_row:
                    res[(input_line.value_suggested_row.id,
                         input_line.value_suggested.id)] += 1
                if input_line.answer_type == 'text' and \
                        (not current_filters or
                         input_line.user_input_id.id in current_filters):
                    comments.append(input_line)
            result_summary = {
                'answers': answers, 'rows': rows,
                'result': res, 'comments': comments}

        # Calculate and return statistics for free_text, textbox, date
        if question.type in ['free_text', 'textbox', 'date']:
            result_summary = []
            for input_line in question.user_input_line_ids:
                if not current_filters or \
                        input_line.user_input_id.id in current_filters:
                    result_summary.append(input_line)

        # Calculate and return statistics for numerical_box
        if question.type == 'numerical_box':
            result_summary = {'input_lines': []}
            all_inputs = []
            for input_line in question.user_input_line_ids:
                if not current_filters or \
                        input_line.user_input_id.id in current_filters:
                    all_inputs.append(input_line.value_number)
                    result_summary['input_lines'].append(input_line)
            if all_inputs:
                result_summary.update({
                    'average': round(sum(all_inputs) / len(all_inputs), 2),
                    'max': round(max(all_inputs), 2),
                    'min': round(min(all_inputs), 2),
                    'sum': sum(all_inputs),
                    'most_common': Counter(all_inputs).most_common(5)})
        return result_summary

    @api.model
    def get_input_summary(self, question, current_filters=None):
        """ Returns overall summary of question
        e.g. answered, skipped, total_inputs on basis of filter """
        current_filters = current_filters if current_filters else []
        result = {}
        if question.step_id.user_input_ids:
            total_input_ids = \
                current_filters or [input_id.id for input_id
                                    in question.step_id.user_input_ids
                                    if input_id.state != 'new']
            result['total_inputs'] = len(total_input_ids)
            question_input_ids = []
            for user_input in question.user_input_line_ids:
                if not user_input.skipped:
                    question_input_ids.append(user_input.user_input_id.id)
            result['answered'] = \
                len(set(question_input_ids) & set(total_input_ids))
            result['skipped'] = result['total_inputs'] - result['answered']
        return result

    # Actions

    @api.multi
    def action_start_step(self):
        """ Open the website page with the step form """
        self.ensure_one()
        token = self.env.context.get('step_token')
        trail = "/%s" % token if token else ""
        lead_id_url = ""
        if self.env.context.get('lead_id', False):
            lead_id_url = "?lead_id=" + str(
                self.env.context.get('lead_id', False))
        return {
            'type': 'ir.actions.act_url',
            'name': "Start Step",
            'target': 'self',
            'url': self.with_context(
                relative_url=True).public_url + trail + lead_id_url
        }

    @api.multi
    def action_send_step(self):
        """ Open a window to compose an email,
        pre-filled with the step message """
        # Ensure that this step has at least
        # one page with at least one question.
        if not self.page_ids or not [page.question_ids for page in
                                     self.page_ids if page.question_ids]:
            raise UserError(_('You cannot send an invitation '
                              'for a step that has no questions.'))

        if self.stage_id.closed:
            raise UserError(_("You cannot send invitations for closed steps."))

        template = self.env.ref(
            'step.email_template_step', raise_if_not_found=False)

        local_context = dict(
            self.env.context,
            default_model='step.step',
            default_res_id=self.id,
            default_step_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            notif_layout='mail.mail_notification_light',
        )
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'step.mail.compose.message',
            'target': 'new',
            'context': local_context,
        }

    @api.multi
    def action_print_step(self):
        """ Open the website page with the step printable view """
        self.ensure_one()
        token = self.env.context.get('step_token')
        trail = "/" + token if token else ""
        lead_id_url = ""
        if self.env.context.get('lead_id', False):
            lead_id_url = "?lead_id=" + str(
                self.env.context.get('lead_id', False))
        return {
            'type': 'ir.actions.act_url',
            'name': "Print Step",
            'target': 'self',
            'url': self.with_context(
                relative_url=True).public_url + trail + lead_id_url
        }

    @api.multi
    def action_result_step(self):
        """ Open the website page with the step results view """
        self.ensure_one()
        lead_id_url = ""
        if self.env.context.get('lead_id', False):
            lead_id_url = "?lead_id=" + str(
                self.env.context.get('lead_id', False))
        return {
            'type': 'ir.actions.act_url',
            'name': "Results of the Step",
            'target': 'self',
            'url': self.with_context(
                relative_url=True).result_url + lead_id_url
        }

    @api.multi
    def action_test_step(self):
        ''' Open the website page with the step form into test mode'''
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'name': "Results of the Step",
            'target': 'self',
            'url': self.with_context(relative_url=True).public_url + "/phantom"
        }

    @api.multi
    def action_step_user_input(self):
        action_rec = self.env.ref('step.action_step_user_input')
        action = action_rec.read()[0]
        ctx = dict(self.env.context)
        ctx.update({'search_default_step_id': self.ids[0],
                    'search_default_completed': 1})
        action['context'] = ctx
        return action


class StepPage(models.Model):
    """ A page for a step.
        Pages are essentially containers, allowing to group questions
        by ordered screens.
        .. note::
            A page should be deleted if the step it belongs to is deleted.
    """
    _name = 'step.page'
    _description = 'Step Page'
    _rec_name = 'title'
    _order = 'sequence,id'

    # Model Fields #

    title = fields.Char('Page Title', required=True, translate=True)
    step_id = fields.Many2one(
        'step.step',
        string='Step',
        ondelete='cascade', required=True)
    question_ids = fields.One2many(
        'step.question',
        'page_id',
        string='Questions', copy=True)
    comment_ids = fields.One2many(
        'step.page.comment',
        'page_id',
        string='Comments', copy=True)
    sequence = fields.Integer('Page number', default=10)
    description = fields.Html(
        'Description',
        translate=True,
        oldname="note",
        help="An introductory text to your page")
    form_config = fields.Text('Form Configuration')
    task_id = fields.Integer('W-Project Task Id')
    is_loghour = fields.Boolean('Is Log hour')
    active = fields.Boolean('Active', default=True)
    sla = fields.Char('SLA')


class StepPageComment(models.Model):
    _name = 'step.page.comment'
    _description = 'Step Page Comment'

    sequence = fields.Integer('Sequence', default=10)
    page_id = fields.Many2one(
        'step.page', string='Step page',
        ondelete='cascade', required=True,
        default=lambda self: self.env.context.get('page_id'))
    step_id = fields.Many2one(
        'step.step',
        related='page_id.step_id',
        string='Step',
        readonly=False)
    comment = fields.Text('Comments')
    user_id = fields.Many2one('res.users')
    attachment = fields.Binary('Attachment')
    file_name = fields.Char("File Name")
    attachment_url = fields.Char('Attachment URL')
    form_history_id = fields.Many2one('crm.lead.stage', 'Form History')


class StepQuestion(models.Model):
    """ Questions that will be asked in a step.

        Each question can have one of more suggested answers (eg. in case of
        dropdown choices, multi-answer checkboxes, radio buttons...).
    """

    _name = 'step.question'
    _description = 'Step Question'
    _rec_name = 'question'
    _order = 'sequence,id'

    # Model fields #

    # Question metadata
    page_id = fields.Many2one(
        'step.page', string='Step page',
        ondelete='cascade', required=True,
        default=lambda self: self.env.context.get('page_id'))
    step_id = fields.Many2one(
        'step.step',
        related='page_id.step_id',
        string='Step',
        readonly=False)
    sequence = fields.Integer('Sequence', default=10)

    # Question
    question = fields.Char('Question Name', required=True, translate=True)
    description = fields.Html(
        'Description',
        help="Use this field to add additional explanations "
             "about your question",
        translate=True, oldname='descriptive_text')

    # Answer
    type = fields.Selection([
        ('free_text', 'Multiple Lines Text Box'),
        ('textbox', 'Single Line Text Box'),
        ('email', 'Email'),
        ('url', 'URL'),
        ('numerical_box', 'Numerical Value'),
        ('date', 'Date'),
        ('simple_choice', 'Multiple choice: only one answer'),
        ('multiple_choice', 'Multiple choice: multiple answers allowed'),
        ('matrix', 'Matrix'),
        ('upload_file', 'Upload File'),
        ('main_business_objective', 'Main business objective'),
        ('why_communication', 'Why Communication?'),
        ('main_objective_of_communication', 'Main objective of communication'),
        ('budget', 'Budget'),
        ('target_audience', 'Target Audience'),
        ('multiple_text_area', 'Multiple Text Area'),
        ('multiple_file_upload', 'Multiple File Upload'),
        ('summary_popup', 'Summary Popup'),
        ('audience_brief', 'Audience Brief'),
        ('textarea_collapsible', 'Textarea Collapsible'),
        ('divider', 'Divider'),
        ('component_group', 'Component Group'),
        ('paragraph', 'Paragraph'),
        ('header', 'Header'),
        ('prequote', 'Prequote'),
        ('iframeViewer', 'iframe Viewer'),
        ('country_state_city', 'Country-State-City'),
        ('content_cluster', 'Content-Cluster'),
        ('audience_custom', 'Audience-Custom'),
        ('frequency_custom', 'Frequency-Custom'),
        ('feedback', 'Feedback'),
    ],
        string='Type of Question',
        default='free_text', required=True)
    matrix_subtype = fields.Selection([
        ('simple', 'One choice per row'),
        ('multiple', 'Multiple choices per row')],
        string='Matrix Type', default='simple')
    labels_ids = fields.One2many(
        'step.label',
        'question_id',
        string='Types of answers',
        oldname='answer_choice_ids', copy=True)
    labels_ids_2 = fields.One2many(
        'step.label',
        'question_id_2',
        string='Rows of the Matrix', copy=True)
    # labels are used for proposed choices
    # if question.type == simple choice | multiple choice
    #                    -> only labels_ids is used
    # if question.type == matrix
    #                    -> labels_ids are the columns of the matrix
    #                    -> labels_ids_2 are the rows of the matrix

    # Display options
    column_nb = fields.Selection([
        ('12', '1'),
        ('6', '2'),
        ('4', '3'),
        ('3', '4'),
        ('2', '6')],
        'Number of columns', default='12')
    # These options refer to col-xx-[12|6|4|3|2] classes in Bootstrap
    display_mode = fields.Selection([
        ('columns', 'Radio Buttons'),
        ('dropdown', 'Selection Box')],
        default='columns')

    # Comments
    comments_allowed = fields.Boolean(
        'Show Comments Field', oldname="allow_comment")
    comments_message = fields.Char(
        'Comment Message',
        translate=True,
        default=lambda self: _("If other, please specify:"))
    comment_count_as_answer = fields.Boolean(
        'Comment Field is an Answer Choice',
        oldname='make_comment_field')

    # Validation
    validation_required = fields.Boolean(
        'Validate entry',
        oldname='is_validation_require')
    validation_email = fields.Boolean('Input must be an email')
    validation_length_min = fields.Integer('Minimum Text Length')
    validation_length_max = fields.Integer('Maximum Text Length')
    validation_min_float_value = fields.Float('Minimum value')
    validation_max_float_value = fields.Float('Maximum value')
    validation_min_date = fields.Date('Minimum Date')
    validation_max_date = fields.Date('Maximum Date')
    validation_error_msg = fields.Char(
        'Validation Error message',
        oldname='validation_valid_err_msg',
        translate=True,
        default=lambda self: _(
            "The answer you entered has an invalid format."))

    # Constraints on number of answers (matrices)
    constr_mandatory = fields.Boolean(
        'Mandatory Answer', oldname="is_require_answer")
    constr_error_msg = fields.Char(
        'Error message',
        oldname='req_error_msg',
        translate=True,
        default=lambda self: _("This question requires an answer."))
    user_input_line_ids = fields.One2many(
        'step.user_input_line',
        'question_id',
        string='Answers', domain=[('skipped', '=', False)])
    field_config = fields.Text('Json Field Config')

    _sql_constraints = [
        ('positive_len_min',
         'CHECK (validation_length_min >= 0)',
         'A length must be positive!'),
        ('positive_len_max',
         'CHECK (validation_length_max >= 0)',
         'A length must be positive!'),
        ('validation_length',
         'CHECK (validation_length_min <= validation_length_max)',
         'Max length cannot be smaller than min length!'),
        ('validation_float',
         'CHECK (validation_min_float_value <= validation_max_float_value)',
         'Max value cannot be smaller than min value!'),
        ('validation_date',
         'CHECK (validation_min_date <= validation_max_date)',
         'Max date cannot be smaller than min date!')
    ]

    @api.onchange('type')
    def onchange_type(self):
        self.validation_email = False
        if self.type == 'email':
            self.validation_email = True

    @api.onchange('validation_email')
    def onchange_validation_email(self):
        if self.validation_email:
            self.validation_required = False

    # Validation methods
    @api.multi
    def validate_question(self, post, answer_tag):
        """ Validate question, depending on question type and parameters """
        self.ensure_one()
        try:
            checker = getattr(self, 'validate_' + self.type)
        except AttributeError:
            _logger.warning(
                self.type + ": This type of question has no validation method")
            return {}
        else:
            return checker(post, answer_tag)

    @api.multi
    def validate_free_text(self, post, answer_tag):
        self.ensure_one()
        errors = {}
        answer = post[answer_tag].strip()
        # Empty answer to mandatory question
        if self.constr_mandatory and not answer:
            errors.update({answer_tag: self.constr_error_msg})
        return errors

    def check_url(self, url):
        """ Reference: https://github.com/django/django/blob/master/
        django/core/validators.py """
        url_regex = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.'
            r')+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
            r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return True if url_regex.match(url) else False

    @api.multi
    def validate_url(self, post, answer_tag):
        self.ensure_one()
        errors = {}
        answer = post[answer_tag].strip()
        # Empty answer to mandatory question
        if self.constr_mandatory and not answer:
            errors.update({answer_tag: self.constr_error_msg})
        if answer:
            if not self.check_url(answer):
                errors.update({answer_tag: _(
                    'This answer must be proper url address')})
        return errors

    @api.multi
    def validate_textbox(self, post, answer_tag):
        self.ensure_one()
        errors = {}
        answer = post[answer_tag].strip()
        # Empty answer to mandatory question
        if self.constr_mandatory and not answer:
            errors.update({answer_tag: self.constr_error_msg})
        # Email format validation
        # Note: this validation is very basic:
        #     all the strings of the form
        #     <something>@<anything>.<extension>
        #     will be accepted
        if answer and self.validation_email:
            if not email_validator.match(answer):
                errors.update({answer_tag: _(
                    'This answer must be an email address')})
        # Answer validation (if properly defined)
        # Length of the answer must be in a range
        if answer and self.validation_required:
            if not (self.validation_length_min <= len(answer) <=
                    self.validation_length_max):
                errors.update({answer_tag: self.validation_error_msg})
        return errors

    @api.multi
    def validate_email(self, post, answer_tag):
        self.ensure_one()
        errors = {}
        answer = post[answer_tag].strip()
        # Empty answer to mandatory question
        if self.constr_mandatory and not answer:
            errors.update({answer_tag: self.constr_error_msg})
        # Email format validation
        # Note: this validation is very basic:
        #     all the strings of the form
        #     <something>@<anything>.<extension>
        #     will be accepted
        if answer and self.validation_email:
            if not email_validator.match(answer):
                errors.update({answer_tag: _(
                    'This answer must be an email address')})
        # Answer validation (if properly defined)
        # Length of the answer must be in a range
        if answer and self.validation_required:
            if not (self.validation_length_min <= len(answer) <=
                    self.validation_length_max):
                errors.update({answer_tag: self.validation_error_msg})
        return errors

    @api.multi
    def validate_numerical_box(self, post, answer_tag):
        self.ensure_one()
        errors = {}
        answer = post[answer_tag].strip()
        # Empty answer to mandatory question
        if self.constr_mandatory and not answer:
            errors.update({answer_tag: self.constr_error_msg})
        # Checks if user input is a number
        if answer:
            try:
                floatanswer = float(answer)
            except ValueError:
                errors.update({answer_tag: _('This is not a number')})
        # Answer validation (if properly defined)
        if answer and self.validation_required:
            # Answer is not in the right range
            with tools.ignore(Exception):
                # check that it is a float has been done hereunder
                floatanswer = float(answer)
                if not (self.validation_min_float_value <= floatanswer <=
                        self.validation_max_float_value):
                    errors.update({answer_tag: self.validation_error_msg})
        return errors

    @api.multi
    def validate_date(self, post, answer_tag):
        self.ensure_one()
        errors = {}
        answer = post[answer_tag].strip()
        # Empty answer to mandatory question
        if self.constr_mandatory and not answer:
            errors.update({answer_tag: self.constr_error_msg})
        # Checks if user input is a date
        if answer:
            try:
                dateanswer = fields.Date.from_string(answer)
            except ValueError:
                errors.update({answer_tag: _('This is not a date')})
                return errors
        # Answer validation (if properly defined)
        if answer and self.validation_required:
            # Answer is not in the right range
            try:
                date_from_string = fields.Date.from_string
                dateanswer = date_from_string(answer)
                min_date = date_from_string(self.validation_min_date)
                max_date = date_from_string(self.validation_max_date)

                if min_date and max_date and not (
                        min_date <= dateanswer <= max_date):
                    # If Minimum and Maximum Date are entered
                    errors.update({answer_tag: self.validation_error_msg})
                elif min_date and not min_date <= dateanswer:
                    # If only Minimum Date is entered
                    # and not Define Maximum Date
                    errors.update({answer_tag: self.validation_error_msg})
                elif max_date and not dateanswer <= max_date:
                    # If only Maximum Date is entered
                    # and not Define Minimum Date
                    errors.update({answer_tag: self.validation_error_msg})
            except ValueError:
                # check that it is a date has been done hereunder
                pass
        return errors

    @api.multi
    def validate_simple_choice(self, post, answer_tag):
        self.ensure_one()
        errors = {}
        if self.comments_allowed:
            comment_tag = "%s_%s" % (answer_tag, 'comment')
        # Empty answer to mandatory self
        if self.constr_mandatory and answer_tag not in post:
            errors.update({answer_tag: self.constr_error_msg})
        if self.constr_mandatory and \
                answer_tag in post and not post[answer_tag].strip():
            errors.update({answer_tag: self.constr_error_msg})
        # Answer is a comment and is empty
        if self.constr_mandatory and answer_tag in post and \
                post[answer_tag] == "-1" and \
                self.comment_count_as_answer and \
                comment_tag in post and not post[comment_tag].strip():
            errors.update({answer_tag: self.constr_error_msg})
        return errors

    @api.multi
    def validate_multiple_choice(self, post, answer_tag):
        self.ensure_one()
        errors = {}
        if self.constr_mandatory:
            answer_candidates = dict_keys_startswith(post, answer_tag)
            comment_flag = answer_candidates.pop((
                    "%s_%s" % (answer_tag, -1)), None)
            if self.comments_allowed:
                comment_answer = answer_candidates.pop((
                        "%s_%s" % (answer_tag, 'comment')), '').strip()
            # Preventing answers with blank value
            if all(not answer.strip() for answer in answer_candidates.values()
                   ) and answer_candidates:
                errors.update({answer_tag: self.constr_error_msg})
            # There is no answer neither comments (if comments count as answer)
            if not answer_candidates and self.comment_count_as_answer and (
                    not comment_flag or not comment_answer):
                errors.update({answer_tag: self.constr_error_msg})
            # There is no answer at all
            if not answer_candidates and not self.comment_count_as_answer:
                errors.update({answer_tag: self.constr_error_msg})
        return errors

    @api.multi
    def validate_generic(self, post, answer_tag):
        self.ensure_one()
        errors = {}
        answer = post[answer_tag].strip()
        # Empty answer to mandatory question
        if self.constr_mandatory and not answer:
            errors.update({answer_tag: self.constr_error_msg})
        return errors

    @api.multi
    def validate_main_business_objective(self, post, answer_tag):
        return self.validate_generic(post, answer_tag)

    @api.multi
    def validate_main_objective_of_communication(self, post, answer_tag):
        return self.validate_generic(post, answer_tag)

    @api.multi
    def validate_why_communication(self, post, answer_tag):
        return self.validate_generic(post, answer_tag)

    @api.multi
    def validate_feedback(self, post, answer_tag):
        return self.validate_generic(post, answer_tag)

    @api.multi
    def validate_frequency_custom(self, post, answer_tag):
        return self.validate_generic(post, answer_tag)

    @api.multi
    def validate_audience_custom(self, post, answer_tag):
        return self.validate_generic(post, answer_tag)

    @api.multi
    def validate_content_cluster(self, post, answer_tag):
        return self.validate_generic(post, answer_tag)

    @api.multi
    def validate_country_state_city(self, post, answer_tag):
        return self.validate_generic(post, answer_tag)

    @api.multi
    def validate_prequote(self, post, answer_tag):
        return self.validate_generic(post, answer_tag)

    @api.multi
    def validate_iframeViewer(self, post, answer_tag):
        return self.validate_generic(post, answer_tag)
    @api.multi
    def validate_budget(self, post, answer_tag):
        return self.validate_generic(post, answer_tag)

    @api.multi
    def validate_target_audience(self, post, answer_tag):
        return self.validate_generic(post, answer_tag)

    @api.multi
    def validate_multiple_text_area(self, post, answer_tag):
        return self.validate_generic(post, answer_tag)

    @api.multi
    def validate_multiple_file_upload(self, post, answer_tag):
        return self.validate_generic(post, answer_tag)

    @api.multi
    def validate_summary_popup(self, post, answer_tag):
        return self.validate_generic(post, answer_tag)

    @api.multi
    def validate_audience_brief(self, post, answer_tag):
        return self.validate_generic(post, answer_tag)

    @api.multi
    def validate_textarea_collapsible(self, post, answer_tag):
        return self.validate_generic(post, answer_tag)

    @api.multi
    def validate_divider(self, post, answer_tag):
        return self.validate_generic(post, answer_tag)

    @api.multi
    def validate_component_group(self, post, answer_tag):
        return self.validate_generic(post, answer_tag)

    @api.multi
    def validate_paragraph(self, post, answer_tag):
        return self.validate_generic(post, answer_tag)

    @api.multi
    def validate_header(self, post, answer_tag):
        return self.validate_generic(post, answer_tag)

    @api.multi
    def validate_matrix(self, post, answer_tag):
        self.ensure_one()
        errors = {}
        if self.constr_mandatory:
            lines_number = len(self.labels_ids_2)
            answer_candidates = dict_keys_startswith(post, answer_tag)
            answer_candidates.pop((
                    "%s_%s" % (answer_tag, 'comment')), '').strip()
            # Number of lines that have been answered
            if self.matrix_subtype == 'simple':
                answer_number = len(answer_candidates)
            elif self.matrix_subtype == 'multiple':
                answer_number = \
                    len({sk.rsplit('_', 1)[0] for sk in answer_candidates})
            else:
                raise RuntimeError("Invalid matrix subtype")
            # Validate that each line has been answered
            if answer_number != lines_number:
                errors.update({answer_tag: self.constr_error_msg})
        return errors


class StepLabel(models.Model):
    """ A suggested answer for a question """

    _name = 'step.label'
    _rec_name = 'value'
    _order = 'sequence,id'
    _description = 'Step Label'

    question_id = fields.Many2one(
        'step.question',
        string='Question', ondelete='cascade')
    question_id_2 = fields.Many2one(
        'step.question',
        string='Question 2',
        ondelete='cascade')
    sequence = fields.Integer('Label Sequence order', default=10)
    value = fields.Char('Suggested value', translate=True, required=True)
    quizz_mark = fields.Float(
        'Score for this choice',
        help="A positive score indicates a correct choice;"
             " a negative or null score indicates a wrong answer")

    @api.one
    @api.constrains('question_id', 'question_id_2')
    def _check_question_not_empty(self):
        """Ensure that field question_id XOR field question_id_2 is not null"""
        if not bool(self.question_id) != bool(self.question_id_2):
            raise ValidationError(_(
                "A label must be attached to only one question."))


class StepUserInput(models.Model):
    """ Metadata for a set of one user's answers to a particular step """

    _name = "step.user_input"
    _rec_name = 'date_create'
    _description = 'Step User Input'

    step_id = fields.Many2one(
        'step.step', string='Step',
        required=True, readonly=True, ondelete='restrict')
    date_create = fields.Datetime(
        'Creation Date', default=fields.Datetime.now,
        required=True, readonly=True, copy=False)
    deadline = fields.Datetime(
        'Deadline', help="Date by which the person can open the "
                         "step and submit answers", oldname="date_deadline")
    type = fields.Selection([
        ('manually', 'Manually'), ('link', 'Link')],
        string='Answer Type', default='manually',
        required=True, readonly=True, oldname="response_type")
    state = fields.Selection([
        ('new', 'Not started yet'),
        ('skip', 'Partially completed'),
        ('done', 'Completed')], string='Status', default='new', readonly=True)
    test_entry = fields.Boolean(readonly=True)
    token = fields.Char(
        'Identification token',
        default=lambda self: str(uuid.uuid4()),
        readonly=True, required=True, copy=False)

    # Optional Identification data
    partner_id = fields.Many2one(
        'res.partner', string='Partner', readonly=True)
    email = fields.Char('E-mail', readonly=True)

    # Displaying data
    last_displayed_page_id = fields.Many2one(
        'step.page', string='Last displayed page')
    # The answers !
    user_input_line_ids = fields.One2many(
        'step.user_input_line',
        'user_input_id',
        string='Answers', copy=True)

    # URLs used to display the answers
    result_url = fields.Char(
        "Public link to the step results",
        related='step_id.result_url', readonly=False)
    print_url = fields.Char(
        "Public link to the empty step",
        related='step_id.print_url', readonly=False)
    quizz_score = fields.Float(
        "Score for the quiz",
        compute="_compute_quizz_score", default=0.0)

    @api.depends('user_input_line_ids.quizz_mark')
    def _compute_quizz_score(self):
        for user_input in self:
            user_input.quizz_score = sum(
                user_input.user_input_line_ids.mapped('quizz_mark'))

    _sql_constraints = [
        ('unique_token', 'UNIQUE (token)', 'A token must be unique!'),
    ]

    @api.model
    def do_clean_emptys(self):
        """ Remove empty user inputs that have been created manually
            (used as a cronjob declared in data/step_cron.xml)
        """
        an_hour_ago = fields.Datetime.to_string(
            datetime.datetime.now() - datetime.timedelta(hours=1))
        self.search([('type', '=', 'manually'), ('state', '=', 'new'),
                    ('date_create', '<', an_hour_ago)]).unlink()

    @api.multi
    def action_step_resend(self):
        """ Send again the invitation """
        self.ensure_one()
        local_context = {
            'step_resent_user_input': self.id,
            'step_resent_token': True,
            'default_partner_ids':
                self.partner_id and [self.partner_id.id] or [],
            'default_multi_email': self.email or "",
            'default_public': 'email_private',
        }
        return self.step_id.with_context(local_context).action_send_step()

    @api.multi
    def action_view_answers(self):
        """ Open the website page with the step form """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'name': "View Answers",
            'target': 'self',
            'url': '%s/%s' % (self.print_url, self.token)
        }

    @api.multi
    def action_step_results(self):
        """ Open the website page with the step results """
        self.ensure_one()
        lead_id_url = ""
        if self.env.context.get('lead_id', False):
            lead_id_url = "?lead_id=" + str(
                self.env.context.get('lead_id', False))
        return {
            'type': 'ir.actions.act_url',
            'name': "Step Results",
            'target': 'self',
            'url': self.result_url + lead_id_url
        }


class StepUserInputLine(models.Model):
    _name = 'step.user_input_line'
    _description = 'Step User Input Line'
    _rec_name = 'date_create'

    user_input_id = fields.Many2one(
        'step.user_input', string='User Input',
        ondelete='cascade', required=True)
    question_id = fields.Many2one(
        'step.question', string='Question',
        ondelete='restrict', required=True)
    page_id = fields.Many2one(
        related='question_id.page_id',
        string="Page", readonly=False)
    step_id = fields.Many2one(
        related='user_input_id.step_id',
        string='Step', store=True, readonly=False)
    date_create = fields.Datetime(
        'Create Date',
        default=fields.Datetime.now, required=True)
    skipped = fields.Boolean('Skipped')
    answer_type = fields.Selection([
        ('text', 'Text'),
        ('email', 'Email'),
        ('url', 'URL'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('free_text', 'Free Text'),
        ('suggestion', 'Suggestion'),
        ('upload_file', 'Upload file'),
        ('main_business_objective', 'Main business objective'),
        ('why_communication', 'Why Communication?'),
        ('main_objective_of_communication', 'Main objective of communication'),
        ('budget', 'Budget'),
        ('target_audience', 'Target Audience'),
        ('multiple_text_area', 'Multiple Text Area'),
        ('multiple_file_upload', 'Multiple File Upload'),
        ('summary_popup', 'Summary Popup'),
        ('audience_brief', 'Audience Brief'),
        ('textarea_collapsible', 'Textarea Collapsible'),
        ('divider', 'Divider'),
        ('component_group', 'Component Group'),
        ('paragraph', 'Paragraph'),
        ('header', 'Header'),
        ('prequote', 'prequote'),
        ('iframeViewer', 'iframe Viewer'),
        ('country_state_city', 'Country-State-City'),
        ('content_cluster', 'Content-Cluster'),
        ('audience_custom', 'Audience-Custom'),
        ('frequency_custom', 'Frequency-Custom'),
        ('feedback', 'Feedback')
    ], string='Answer Type')
    value_text = fields.Char('Text answer')
    value_number = fields.Float('Numerical answer')
    value_date = fields.Date('Date answer')
    value_free_text = fields.Text('Free Text answer')
    value_suggested = fields.Many2one('step.label', string="Suggested answer")
    value_suggested_row = fields.Many2one('step.label', string="Row answer")
    quizz_mark = fields.Float('Score given for this choice')
    file = fields.Binary('Upload file')
    file_type = fields.Selection([('image', 'image'), ('pdf', 'pdf')])
    value_json_data = fields.Text('Json Data Answer')
    value_email = fields.Char('Email answer')
    value_url = fields.Char('URL answer')

    @api.constrains('skipped', 'answer_type')
    def _answered_or_skipped(self):
        for uil in self:
            if not uil.skipped != bool(uil.answer_type):
                raise ValidationError(_(
                    'This question cannot be unanswered or skipped.'))

    @api.constrains('answer_type')
    def _check_answer_type(self):
        for uil in self:
            fields_type = {
                'text': bool(uil.value_text),
                'number': (bool(uil.value_number) or uil.value_number == 0),
                'date': bool(uil.value_date),
                'free_text': bool(uil.value_free_text),
                'suggestion': bool(uil.value_suggested)
            }
            if not fields_type.get(uil.answer_type, True):
                raise ValidationError(_(
                    'The answer must be in the right type'))

    def _get_mark(self, value_suggested):
        label = self.env['step.label'].browse(int(value_suggested))
        mark = label.quizz_mark if label.exists() else 0.0
        return mark

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            value_suggested = vals.get('value_suggested')
            if value_suggested:
                vals.update({'quizz_mark': self._get_mark(value_suggested)})
        return super(StepUserInputLine, self).create(vals_list)

    @api.multi
    def write(self, vals):
        value_suggested = vals.get('value_suggested')
        if value_suggested:
            vals.update({'quizz_mark': self._get_mark(value_suggested)})
        return super(StepUserInputLine, self).write(vals)

    @api.model
    def save_lines(self, user_input_id, question, post, answer_tag):
        """ Save answers to questions, depending on question type

            If an answer already exists for question and
            user_input_id, it will be
            overwritten (in order to maintain data consistency).
        """
        try:
            saver = getattr(self, 'save_line_' + question.type)
        except AttributeError:
            _logger.error(question.type + ": This type of "
                                          "question has no saving function")
            return False
        else:
            saver(user_input_id, question, post, answer_tag)

    @api.model
    def save_line_free_text(self, user_input_id, question, post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'free_text', 'value_free_text')

    @api.model
    def save_line_generic(self, user_input_id, question, post,
                          answer_tag, answer_type, field_name):
        vals = {
            'user_input_id': user_input_id,
            'question_id': question.id,
            'step_id': question.step_id.id,
            'skipped': False,
        }
        if answer_tag in post and post[answer_tag].strip():
            vals.update({'answer_type': answer_type,
                         field_name: post[answer_tag]})
        else:
            vals.update({'answer_type': None, 'skipped': True})
        old_uil = self.search([
            ('user_input_id', '=', user_input_id),
            ('step_id', '=', question.step_id.id),
            ('question_id', '=', question.id)
        ])
        if old_uil:
            old_uil.write(vals)
        else:
            old_uil.create(vals)
        return True

    @api.model
    def save_line_multiple_text_area(self, user_input_id, question,
                                     post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'multiple_text_area', 'value_json_data')

    @api.model
    def save_line_multiple_file_upload(self, user_input_id, question,
                                       post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'multiple_file_upload', 'value_json_data')

    @api.model
    def save_line_summary_popup(self, user_input_id, question,
                                post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'summary_popup', 'value_json_data')

    @api.model
    def save_line_textarea_collapsible(self, user_input_id, question,
                                       post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'textarea_collapsible', 'value_json_data')

    @api.model
    def save_line_divider(self, user_input_id, question, post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'divider', 'value_json_data')

    @api.model
    def save_line_component_group(self, user_input_id, question,
                                  post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'component_group', 'value_json_data')

    @api.model
    def save_line_paragraph(self, user_input_id, question,
                            post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'paragraph', 'value_json_data')

    @api.model
    def save_line_header(self, user_input_id, question,
                         post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'header', 'value_json_data')

    @api.model
    def save_line_budget(self, user_input_id, question, post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'budget', 'value_json_data')

    @api.model
    def save_line_target_audience(self, user_input_id, question,
                                  post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'target_audience', 'value_json_data')

    @api.model
    def save_line_audience_brief(self, user_input_id, question,
                                 post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'audience_brief', 'value_json_data')

    @api.model
    def save_line_main_business_objective(self, user_input_id,
                                          question, post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'main_business_objective', 'value_json_data')

    @api.model
    def save_line_why_communication(self, user_input_id, question,
                                    post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'why_communication', 'value_json_data')

    @api.model
    def save_line_feedback(self, user_input_id, question,
                                    post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'feedback', 'value_json_data')

    @api.model
    def save_line_frequency_custom(self, user_input_id, question,
                                    post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'frequency_custom', 'value_json_data')

    @api.model
    def save_line_audience_custom(self, user_input_id, question,
                                    post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'audience_custom', 'value_json_data')

    @api.model
    def save_line_content_cluster(self, user_input_id, question,
                                    post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'content_cluster', 'value_json_data')

    @api.model
    def save_line_country_state_city(self, user_input_id, question,
                                    post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'country_state_city', 'value_json_data')

    @api.model
    def save_line_iframeViewer(self, user_input_id, question,
                                    post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'iframeViewer', 'value_json_data')

    @api.model
    def save_line_prequote(self, user_input_id, question,
                                    post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'prequote', 'value_json_data')

    @api.model
    def save_line_main_objective_of_communication(self, user_input_id,
                                                  question, post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'main_objective_of_communication', 'value_json_data')

    @api.model
    def save_line_textbox(self, user_input_id, question, post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'text', 'value_text')

    @api.model
    def save_line_email(self, user_input_id, question, post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'email', 'value_email')

    @api.model
    def save_line_url(self, user_input_id, question, post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'url', 'value_url')

    @api.model
    def save_line_numerical_box(
            self, user_input_id, question, post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'number', 'value_number')

    @api.model
    def save_line_date(self, user_input_id, question, post, answer_tag):
        return self.save_line_generic(
            user_input_id, question, post, answer_tag,
            'date', 'value_date')

    @api.model
    def save_line_simple_choice(
            self, user_input_id, question, post, answer_tag):
        vals = {
            'user_input_id': user_input_id,
            'question_id': question.id,
            'step_id': question.step_id.id,
            'skipped': False
        }
        old_uil = self.search([
            ('user_input_id', '=', user_input_id),
            ('step_id', '=', question.step_id.id),
            ('question_id', '=', question.id)
        ])
        old_uil.sudo().unlink()

        if answer_tag in post and post[answer_tag].strip():
            vals.update({
                'answer_type': 'suggestion',
                'value_suggested': post[answer_tag]})
        else:
            vals.update({'answer_type': None, 'skipped': True})

        # '-1' indicates 'comment count as
        # an answer' so do not need to record it
        if post.get(answer_tag) and post.get(answer_tag) != '-1':
            self.create(vals)

        comment_answer = post.pop((
                "%s_%s" % (answer_tag, 'comment')), '').strip()
        if comment_answer:
            vals.update({
                'answer_type': 'text',
                'value_text': comment_answer,
                'skipped': False, 'value_suggested': False})
            self.create(vals)

        return True

    @api.model
    def save_line_multiple_choice(
            self, user_input_id, question, post, answer_tag):
        vals = {
            'user_input_id': user_input_id,
            'question_id': question.id,
            'step_id': question.step_id.id,
            'skipped': False
        }
        old_uil = self.search([
            ('user_input_id', '=', user_input_id),
            ('step_id', '=', question.step_id.id),
            ('question_id', '=', question.id)
        ])
        old_uil.sudo().unlink()

        ca_dict = dict_keys_startswith(post, answer_tag + '_')
        comment_answer = ca_dict.pop((
                "%s_%s" % (answer_tag, 'comment')), '').strip()
        if len(ca_dict) > 0:
            for key in ca_dict:
                # '-1' indicates 'comment count as
                # an answer' so do not need to record it
                if key != ('%s_%s' % (answer_tag, '-1')):
                    vals.update({
                        'answer_type': 'suggestion',
                        'value_suggested': ca_dict[key]})
                    self.create(vals)
        if comment_answer:
            vals.update({
                'answer_type': 'text',
                'value_text': comment_answer,
                'value_suggested': False})
            self.create(vals)
        if not ca_dict and not comment_answer:
            vals.update({'answer_type': None, 'skipped': True})
            self.create(vals)
        return True

    @api.model
    def save_line_matrix(self, user_input_id, question, post, answer_tag):
        vals = {
            'user_input_id': user_input_id,
            'question_id': question.id,
            'step_id': question.step_id.id,
            'skipped': False
        }
        old_uil = self.search([
            ('user_input_id', '=', user_input_id),
            ('step_id', '=', question.step_id.id),
            ('question_id', '=', question.id)
        ])
        old_uil.sudo().unlink()

        no_answers = True
        ca_dict = dict_keys_startswith(post, answer_tag + '_')

        comment_answer = ca_dict.pop((
                "%s_%s" % (answer_tag, 'comment')), '').strip()
        if comment_answer:
            vals.update({'answer_type': 'text', 'value_text': comment_answer})
            self.create(vals)
            no_answers = False

        if question.matrix_subtype == 'simple':
            for row in question.labels_ids_2:
                a_tag = "%s_%s" % (answer_tag, row.id)
                if a_tag in ca_dict:
                    no_answers = False
                    vals.update({
                        'answer_type': 'suggestion',
                        'value_suggested': ca_dict[a_tag],
                        'value_suggested_row': row.id})
                    self.create(vals)

        elif question.matrix_subtype == 'multiple':
            for col in question.labels_ids:
                for row in question.labels_ids_2:
                    a_tag = "%s_%s_%s" % (answer_tag, row.id, col.id)
                    if a_tag in ca_dict:
                        no_answers = False
                        vals.update({
                            'answer_type': 'suggestion',
                            'value_suggested': col.id,
                            'value_suggested_row': row.id})
                        self.create(vals)
        if no_answers:
            vals.update({'answer_type': None, 'skipped': True})
            self.create(vals)
        return True

    @api.model
    def save_line_upload_file(self, user_input_id, question, post, answer_tag):
        vals = {
            'user_input_id': user_input_id,
            'question_id': question.id,
            'step_id': question.step_id.id,
            'skipped': False
        }
        file_name = str(post[answer_tag])
        file_type = file_name.find("('application/pdf')")
        image_type = file_name.find("('image/png')")
        if file_type > -1:
            vals.update({'file_type': 'pdf'})
        if image_type > -1:
            vals.update({'file_type': 'image'})
        if question.constr_mandatory:
            file = base64.encodebytes(post[answer_tag].read())
        else:
            file = base64.encodebytes(
                post[answer_tag].read()) if post[answer_tag] else None
        if answer_tag in post:
            vals.update({'answer_type': 'upload_file', 'file': file})
        else:
            vals.update({'answer_type': None, 'skipped': True})
        old_uil = self.search([
            ('user_input_id', '=', user_input_id),
            ('step_id', '=', question.step_id.id),
            ('question_id', '=', question.id)
        ])
        if old_uil:
            old_uil.write(vals)
        else:
            old_uil.create(vals)
        return True
