# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Steps',
    'version': '3.0',
    'category': 'Marketing',
    'description': """
Create beautiful steps and visualize answers
==============================================

It depends on the answers or reviews of some questions by different users. A
step may have multiple pages. Each page may contain multiple questions and
each question may have multiple answers. Different users may give different
answers of question and according to that step is done. Partners are also
sent mails with personal token for the invitation of the step.
    """,
    'summary': 'Create steps and analyze answers',
    'depends': ['http_routing', 'mail', 'crm_lead_extended'],
    'data': [
        'security/step_security.xml',
        'security/ir.model.access.csv',
        'views/step_views.xml',
        'views/step_templates.xml',
        'views/step_result.xml',
        'views/crm_stage_view.xml',
        'views/crm_lead_view.xml',
        'data/mail_template_data.xml',
        'wizard/step_email_compose_message.xml',
        'data/step_stages.xml',
    ],
    'demo': ['data/step_demo_user.xml',
             'data/step_demo_feedback.xml',
             'data/step.user_input.csv',
             'data/step.user_input_line.csv'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 105,
}
