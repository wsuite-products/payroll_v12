# Copyright 2017 - 2018 Modoolar <info@modoolar.com>
# License LGPLv3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

{
    "name": "Project Agile Kanban",
    "summary": "Manage your projects by using agile kanban methodology",
    "category": "Project",
    "version": "12.0.1.0.0",
    "license": "LGPL-3",
    "author": "Modoolar",
    "website": "https://www.modoolar.com/",
    "depends": ["project_agile", "project_agile_analytic"],
    "data": [
        "security/ir.model.access.csv",
        "views/project_agile_board_views.xml",
    ],
    "demo": [],
    "qweb": [],
    "application": True,
    "post_init_hook": "post_init_hook",
}
