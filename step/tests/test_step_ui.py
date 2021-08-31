import odoo.tests
# Part of Odoo. See LICENSE file for full copyright and licensing details.


@odoo.tests.common.tagged('post_install', '-at_install')
class TestUi(odoo.tests.HttpCase):

    def test_01_admin_step_tour(self):
        self.phantom_js(
            "/",
            "odoo.__DEBUG__.services['web_tour.tour'].run('test_step')",
            "odoo.__DEBUG__.services['web_tour.tour'].tours.test_step.ready",
            login="admin")

    def test_02_demo_step_tour(self):
        self.phantom_js(
            "/",
            "odoo.__DEBUG__.services['web_tour.tour'].run('test_step')",
            "odoo.__DEBUG__.services['web_tour.tour'].tours.test_step.ready",
            login="demo")

    def test_03_public_step_tour(self):
        self.phantom_js(
            "/",
            "odoo.__DEBUG__.services['web_tour.tour'].run('test_step')",
            "odoo.__DEBUG__.services['web_tour.tour'].tours.test_step.ready")
