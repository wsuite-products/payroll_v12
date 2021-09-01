# -*- coding: utf-8 -*-
# Copyright 2019-TODAY WSuite Products <wsuite-products@destiny.ws>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

# import werkzeug.wrappers
# from odoo import http
# import json
#
#
# class WebhookController(http.Controller):
#
#     @http.route('/webhook/<model_name>', type='http', auth="none",
#                 methods=['POST', 'GET', 'PUT', 'DELETE'], csrf=False)
#     def webhook(self, **post):
#         return werkzeug.wrappers.Response(
#             status=200,
#             content_type='application/json; charset=utf-8',
#             headers=[('Cache-Control', 'no-store'),
#                      ('Pragma', 'no-cache')],
#             response=json.dumps({
#                 'report_name_list': "Test"
#             }),
#         )
