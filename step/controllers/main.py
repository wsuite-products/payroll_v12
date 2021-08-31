# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging
import werkzeug
from datetime import datetime
from math import ceil

from odoo import fields, http, SUPERUSER_ID
from odoo.http import request
from odoo.tools import ustr

_logger = logging.getLogger(__name__)


class Step(http.Controller):
    # HELPER METHODS #

    def _check_bad_cases(self, step, token=None):
        # In case of bad step, redirect to steps list
        if not step.sudo().exists():
            return werkzeug.utils.redirect("/step/")

        # In case of auth required, block public user
        if step.auth_required and request.env.user._is_public():
            return request.render(
                "step.auth_required", {'step': step, 'token': token})

        # In case of non open steps
        if step.stage_id.closed:
            return request.render("step.notopen")

        # If there is no pages
        if not step.page_ids:
            return request.render("step.nopages", {'step': step})

        # Everything seems to be ok
        return None

    def _check_deadline(self, user_input):
        '''Prevent opening of the step if the deadline has turned out

        ! This will NOT disallow access to users who have already
        partially filled the step !'''
        deadline = user_input.deadline
        if deadline:
            dt_deadline = fields.Datetime.from_string(deadline)
            dt_now = datetime.now()
            if dt_now > dt_deadline:  # step is not open anymore
                return request.render("step.notopen")
        return None

    # ROUTES HANDLERS #

    # Step start
    @http.route(['/step/start/<model("step.step"):step>',
                 '/step/start/<model("step.step"):step>/<string:token>'],
                type='http', auth='public', website=True)
    def start_step(self, step, token=None, **post):
        UserInput = request.env['step.user_input']
        lead_id = request.env['crm.lead'].browse(post.get('lead_id', False))
        request.session['lead_id'] = int(lead_id.id)
        # Test mode
        if token and token == "phantom":
            _logger.info("[step] Phantom mode")
            user_input = UserInput.create({
                'step_id': step.id, 'test_entry': True})
            data = {'step': step, 'page': None, 'token': user_input.token}
            return request.render('step.step_init', data)
        # END Test mode

        # Controls if the step can be displayed
        errpage = self._check_bad_cases(step, token=token)
        if errpage:
            return errpage

        # Manual steping
        if not token:
            vals = {'step_id': step.id}
            if not request.env.user._is_public():
                vals['partner_id'] = request.env.user.partner_id.id
            user_input = UserInput.create(vals)
        else:
            user_input = UserInput.sudo().search(
                [('token', '=', token)], limit=1)
            if not user_input:
                return request.render("step.403", {'step': step})

        # Do not open expired step
        errpage = self._check_deadline(user_input)
        if errpage:
            return errpage

        # Select the right page
        if user_input.state == 'new':  # Intro page
            data = {'step': step, 'page': None, 'token': user_input.token}
            return request.render('step.step_init', data)
        else:
            return request.redirect(
                '/step/fill/%s/%s' % (step.id, user_input.token))

    # Step displaying
    @http.route(['/step/fill/<model("step.step"):step>/<string:token>',
                 '/step/fill/<model("step.step"):step>/'
                 '<string:token>/<string:prev>'],
                type='http', auth='public', website=True)
    def fill_step(self, step, token, prev=None, **post):
        '''Display and validates a step'''
        Step = request.env['step.step']
        UserInput = request.env['step.user_input']

        # Controls if the step can be displayed
        errpage = self._check_bad_cases(step)
        if errpage:
            return errpage

        # Load the user_input
        user_input = UserInput.sudo().search([('token', '=', token)], limit=1)
        if not user_input:  # Invalid token
            return request.render("step.403", {'step': step})

        # Do not display expired step (even if some pages have already been
        # displayed -- There's a time for everything!)
        errpage = self._check_deadline(user_input)
        if errpage:
            return errpage

        # Select the right page
        if user_input.state == 'new':  # First page
            page, page_nr, last = Step.next_page(user_input, 0, go_back=False)
            data = {
                'step': step, 'page': page,
                'page_nr': page_nr, 'token': user_input.token}
            if last:
                data.update({'last': True})
            return request.render('step.step', data)
        elif user_input.state == 'done':  # Display success message
            return request.render('step.sfinished', {
                'step': step,
                'token': token,
                'user_input': user_input})
        elif user_input.state == 'skip':
            flag = (True if prev and prev == 'prev' else False)
            page, page_nr, last = Step.next_page(
                user_input, user_input.last_displayed_page_id.id, go_back=flag)

            # special case if you click "previous" from the last page,
            # then leave the step, then reopen it from the URL, avoid crash
            if not page:
                page, page_nr, last = Step.next_page(
                    user_input, user_input.last_displayed_page_id.id,
                    go_back=True)

            data = {
                'step': step, 'page': page,
                'page_nr': page_nr, 'token': user_input.token}
            if last:
                data.update({'last': True})
            return request.render('step.step', data)
        else:
            return request.render("step.403", {'step': step})

    # AJAX prefilling of a step
    @http.route(['/step/prefill/<model("step.step"):step>/<string:token>',
                 '/step/prefill/<model("step.step"):step>/'
                 '<string:token>/<model("step.page"):page>'],
                type='http', auth='public', website=True)
    def prefill(self, step, token, page=None, **post):
        UserInputLine = request.env['step.user_input_line']
        ret = {}

        # Fetch previous answers
        if page:
            previous_answers = UserInputLine.sudo().search([
                ('user_input_id.token', '=', token),
                ('page_id', '=', page.id)])
        else:
            previous_answers = UserInputLine.sudo().search([
                ('user_input_id.token', '=', token)])

        # Return non empty answers in a JSON compatible format
        for answer in previous_answers:
            if not answer.skipped:
                answer_tag = '%s_%s_%s' % (
                    answer.step_id.id,
                    answer.page_id.id,
                    answer.question_id.id)
                answer_value = None
                if answer.answer_type == 'free_text':
                    answer_value = answer.value_free_text
                elif answer.answer_type == 'text' and \
                        answer.question_id.type == 'textbox':
                    answer_value = answer.value_text
                elif answer.answer_type == 'text' and \
                        answer.question_id.type != 'textbox':
                    # here come comment answers for matrices,
                    # simple choice and multiple choice
                    answer_tag = "%s_%s" % (answer_tag, 'comment')
                    answer_value = answer.value_text
                elif answer.answer_type == 'number':
                    answer_value = str(answer.value_number)
                elif answer.answer_type == 'date':
                    answer_value = fields.Date.to_string(answer.value_date)
                elif answer.answer_type == 'suggestion' and not \
                        answer.value_suggested_row:
                    answer_value = answer.value_suggested.id
                elif answer.answer_type == 'suggestion' and \
                        answer.value_suggested_row:
                    answer_tag = "%s_%s" % (
                        answer_tag, answer.value_suggested_row.id)
                    answer_value = answer.value_suggested.id
                elif answer.answer_type in ['main_business_objective',
                                            'why_communication',
                                            'main_objective_of_communication',
                                            'budget',
                                            'target_audience',
                                            'multiple_text_area',
                                            'multiple_file_upload',
                                            'summary_popup',
                                            'textarea_collapsible', 'divider',
                                            'component_group',
                                            'paragraph',
                                            'header',
                                            'audience_brief']:
                    answer_value = answer.value_json_data
                elif answer.answer_type == 'email':
                    answer_value = answer.value_email
                elif answer.answer_type == 'url':
                    answer_value = answer.value_url
                if answer_value:
                    ret.setdefault(answer_tag, []).append(answer_value)
                else:
                    _logger.warning("[step] No answer has been found for "
                                    "question %s marked as non "
                                    "skipped" % answer_tag)
        return json.dumps(ret, default=str)

    # AJAX scores loading for quiz correction mode
    @http.route(['/step/scores/<model("step.step"):step>/<string:token>'],
                type='http', auth='public', website=True)
    def get_scores(self, step, token, page=None, **post):
        ret = {}

        # Fetch answers
        previous_answers = request.env['step.user_input_line'].sudo().search([
            ('user_input_id.token', '=', token)])

        # Compute score for each question
        for answer in previous_answers:
            tmp_score = ret.get(answer.question_id.id, 0.0)
            ret.update({answer.question_id.id: tmp_score + answer.quizz_mark})
        return json.dumps(ret)

    # AJAX submission of a page
    @http.route(['/step/submit/<model("step.step"):step>'],
                type='http', methods=['POST'],
                auth='public', website=True)
    def submit(self, step, **post):
        _logger.debug('Incoming data: %s', post)
        page_id = int(post['page_id'])
        questions = request.env['step.question'].search([
            ('page_id', '=', page_id)])
        # Answer validation
        errors = {}
        for question in questions:
            answer_tag = "%s_%s_%s" % (step.id, page_id, question.id)
            errors.update(question.validate_question(post, answer_tag))

        ret = {}
        if len(errors):
            # Return errors messages to webpage
            ret['errors'] = errors
        else:
            # Store answers into database
            try:
                user_input = \
                    request.env['step.user_input'].sudo().search([
                        ('token', '=', post['token'])], limit=1)
            except KeyError:  # Invalid token
                return request.render("step.403", {'step': step})
            user_id = request.env.user.id \
                if user_input.type != 'link' else SUPERUSER_ID

            for question in questions:
                answer_tag = "%s_%s_%s" % (step.id, page_id, question.id)
                request.env['step.user_input_line'].sudo(
                    user=user_id).save_lines(
                    user_input.id, question, post, answer_tag)
            go_back = post['button_submit'] == 'previous'
            next_page, _, last = request.env['step.step'].next_page(
                user_input, page_id, go_back=go_back)
            vals = {'last_displayed_page_id': page_id}
            if next_page is None and not go_back:
                vals.update({'state': 'done'})
            else:
                vals.update({'state': 'skip'})
            user_input.sudo(user=user_id).write(vals)
            ret['redirect'] = '/step/fill/%s/%s' % (step.id, post['token'])
            if go_back:
                ret['redirect'] += '/prev'
        return json.dumps(ret)

    # Printing routes
    @http.route(['/step/print/<model("step.step"):step>',
                 '/step/print/<model("step.step"):step>/<string:token>'],
                type='http', auth='public', website=True)
    def print_step(self, step, token=None, **post):
        '''Display an step in printable view; if <token> is set, it will
        grab the answers of the user_input_id that has <token>.'''
        if post.get('lead_id', False):
            lead_id = request.env['crm.lead'].browse(
                post.get('lead_id', False))
            request.session['lead_id'] = int(lead_id.id)
        if step.auth_required and request.env.user == request.website.user_id:
            return request.render(
                "step.auth_required", {'step': step, 'token': token})

        step_question = request.env['step.question']
        question_ids = step_question.sudo().search([
            ('type', '=', 'upload_file'), ('step_id', '=', step.id)])
        user_input_line_upload_file = []
        if question_ids:
            user_input = request.env['step.user_input']
            user_input_line = request.env['step.user_input_line']
            user_input_id = user_input.sudo().search([
                ('token', '=', token), ('step_id', '=', step.id)])
            for question in question_ids:
                user_input_line = user_input_line.search([
                    ('user_input_id', '=', user_input_id.id),
                    ('step_id', '=', step.id),
                    ('question_id', '=', question.id),
                    ('answer_type', '=', 'upload_file')
                ])
                user_input_line_upload_file.append(user_input_line)
        return request.render(
            'step.step_print', {
                'step': step,
                'token': token,
                'page_nr': 0,
                'quizz_correction':
                    True if step.quizz_mode and token else False,
                'user_input_line_upload_file': user_input_line_upload_file,
            })

    @http.route(['/step/results/<model("step.step"):step>'],
                type='http', auth='user', website=True)
    def step_reporting(self, step, token=None, **post):
        '''Display step Results & Statistics for given step.'''
        lead_id = request.env['crm.lead'].browse(post.get('lead_id', False))
        request.session['lead_id'] = int(lead_id.id)
        result_template = 'step.result'
        current_filters = []
        filter_display_data = []
        filter_finish = False

        if not step.user_input_ids or not \
                [input_id.id for input_id in step.user_input_ids
                 if input_id.state != 'new']:
            result_template = 'step.no_result'
        if 'finished' in post:
            post.pop('finished')
            filter_finish = True
        if post or filter_finish:
            filter_data = self.get_filter_data(post)
            current_filters = step.filter_input_ids(filter_data, filter_finish)
            filter_display_data = step.get_filter_display_data(filter_data)
        return request.render(
            result_template, {
                'step': step,
                'step_dict': self.prepare_result_dict(step, current_filters),
                'page_range': self.page_range,
                'current_filters': current_filters,
                'filter_display_data': filter_display_data,
                'filter_finish': filter_finish
            })

    def prepare_result_dict(self, step, current_filters=None):
        """Returns dictionary having values for rendering template"""
        current_filters = current_filters if current_filters else []
        Step = request.env['step.step']
        result = {'page_ids': []}
        for page in step.page_ids:
            page_dict = {'page': page, 'question_ids': []}
            for question in page.question_ids:
                question_dict = {
                    'question': question,
                    'input_summary':
                        Step.get_input_summary(question, current_filters),
                    'prepare_result':
                        Step.prepare_result(question, current_filters),
                    'graph_data':
                        self.get_graph_data(question, current_filters),
                }

                page_dict['question_ids'].append(question_dict)
            result['page_ids'].append(page_dict)
        return result

    def get_filter_data(self, post):
        """Returns data used for filtering the result"""
        filters = []
        for ids in post:
            # if user add some random data in query URI, ignore it
            try:
                row_id, answer_id = ids.split(',')
                filters.append({
                    'row_id': int(row_id),
                    'answer_id': int(answer_id)})
            except:
                return filters
        return filters

    def page_range(self, total_record, limit):
        '''Returns number of pages required for pagination'''
        total = ceil(total_record / float(limit))
        return range(1, int(total + 1))

    def get_graph_data(self, question, current_filters=None):
        '''Returns formatted data required by graph library
        on basis of filter'''
        # TODO refactor this terrible method and merge
        #  it with prepare_result_dict
        current_filters = current_filters if current_filters else []
        Step = request.env['step.step']
        result = []
        if question.type == 'multiple_choice':
            result.append({'key': ustr(question.question),
                           'values': Step.prepare_result(
                               question, current_filters)['answers']
                           })
        if question.type == 'simple_choice':
            result = Step.prepare_result(question, current_filters)['answers']
        if question.type == 'matrix':
            data = Step.prepare_result(question, current_filters)
            for answer in data['answers']:
                values = []
                for row in data['rows']:
                    values.append({
                        'text': data['rows'].get(row),
                        'count': data['result'].get((row, answer))})
                result.append({
                    'key': data['answers'].get(answer),
                    'values': values})
        return json.dumps(result)
