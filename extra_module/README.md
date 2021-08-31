
Scrummer
=================================
This project aims to extend Odoo with agile project management methodologies like:

  * Scrum
  * Kanban
  * Scrumban
  * Lean
  * ...

as well as to introduce a completely fresh UI framework for agile project management.

[//]: # (addons)


Available addons
----------------
addon | version | summary
--- | --- | ---
[scrummer](scrummer/) | 12.0.1.0.0 | Base module for development of all scrummer components.
[scrummer_git](scrummer_git/) | 12.0.1.0.0 | Module which brings integration with [project_git](project_git/) module.
[scrummer_kanban](scrummer_kanban/) | 12.0.1.0.0 | Module which brings integration with [project_agile_kanban](project_agile_kanban/) module.
[scrummer_scrum](scrummer_scrum/) | 12.0.1.0.0 | Module which brings integration with [project_agile_scrum](project_agile_scrum/) module.
[scrummer_timesheet_category](scrummer_timesheet_category/) | 12.0.1.0.0 | Module which brings integration with [project_timesheet_category](project_timesheet_category/) module.
[scrummer_workflow_security](scrummer_workflow_security/) | 12.0.1.0.0 | Module which brings integration with [project_workflow_security](project_workflow_security/) module.
[scrummer_workflow_transition_by_project](scrummer_workflow_transition_by_project/) | 12.0.1.0.0 | Module which brings integration with [project_workflow_transition_by_project](project_workflow_transition_by_project/) module.
[scrummer_workflow_transitions_by_task_type](scrummer_workflow_transitions_by_task_type/) | 12.0.1.0.0 | Module which brings integration with [project_agile_workflow_transitions_by_task_type](project_agile_workflow_transitions_by_task_type/) module.
[project_agile](project_agile/) | 12.0.1.0.0 | Base module for development of all agile methodologies.
[project_agile_analytic](project_agile_analytic/) | 12.0.1.0.0 | Module which bring simple analytics for project tasks.
[project_agile_jira](project_agile_jira/) | 12.0.1.0.0 | Module which brings interface for migration from JIRA to Odoo. Very light.
[project_agile_kanban](project_agile_kanban/) | 12.0.1.0.0 | Module which brings agile kanban methodology.
[project_agile_scrum](project_agile_scrum/) | 12.0.1.0.0 | Module which brings agile scrum methodology
[project_agile_timesheet_category](project_agile_timesheet_category/) | 12.0.1.0.0 | Module which integrates [project_timesheet_category](project_timesheet_category/) with project_agile
[project_agile_workflow_transitions_by_task_type](project_agile_workflow_transitions_by_task_type/) | 12.0.1.0.0 | Module which integrates [project_workflow_transitions_by_task_type](project_workflow_transitions_by_task_type/) with project agile.
[project_git](project_git/) | 12.0.1.0.0 | Base module for development of other modules which will bring integration with specific git services like: GitHub, BitBucket, GitLab, etc.
[project_git_bitbucket](project_git_bitbucket/) | 12.0.1.0.0 | Module which extends [project_git](project_git/) module with BitBucket integration.
[project_git_github](project_git_github/) | 12.0.1.0.0 | Module which extends [project_git](project_git/) module with GitHub integration.
[project_git_gitlab](project_git_gitlab/) | 12.0.1.0.0 | Module which extends [project_git](project_git/) module with GitLab integration.
[project_key](project_key/) | 12.0.1.0.0 | Module which brings functionality to uniquely identify projects and tasks by simple auto generated ``key`` field.
[project_portal](project_portal/) | 12.0.1.0.0 | Module which extends project portal controller to be more extendable.
[project_task_archiving](project_task_archiving/) | 12.0.1.0.0 | Module which enables task archiving based on number of days task stays in a specific stage.
[project_timesheet_category](project_timesheet_category/) | 12.0.1.0.0 | Module which brings categorization to the project timesheet.
[project_workflow](project_workflow/) | 12.0.1.0.0 | This module provides functionality to create fully configurable workflow around ``project.task``
[project_workflow_action](project_workflow_action/) | 12.0.1.0.0 | This module provides functionality to execute server actions when executing task workflow.
[project_workflow_default_state_per_group](project_workflow_default_state_per_group/) | 12.0.1.0.0 | This module provides functionality to assign different initial state to task depending on the security group.
[project_workflow_security](project_workflow_security/) | 12.0.1.0.0 | Module which extends [project_workflow](project_workflow/) to provide allowed security groups for workflow transitions.
[project_workflow_transitions_by_project](project_workflow_transitions_by_project/) | 12.0.1.0.0 | Module which extends [project_workflow](project_workflow/) to provide project constraints for workflow transitions.
[web_diagram_position](web_diagram_position/) | 12.0.1.0.0 | Module provides functionality to save workflow elements coordinates.
[web_ir_actions_act_multi](web_ir_actions_act_multi/) | 12.0.1.0.0 | Module which brings new type of action to ActionManager which can execute provided list of actions.
[web_ir_actions_act_view_reload](web_ir_actions_act_view_reload/) | 12.0.1.0.0 | Module which brings new type of action to ActionManager which can reload currently active view only.
[web_syncer](web_syncer/) | 12.0.1.0.0 | Module which provides generic interface to receive CUD model notifications on web client side.
[web_widget_image_url](web_widget_image_url/) | 12.0.1.0.0 | Module which provides web widget for displaying image from an URL.

[//]: # (end addons)


Roadmap
=======
Roadmap for further development can be found [here](roadmap.md).

Credits
=======

Contributors
------------

* Igor Jovanović <igor.jovanovic@modoolar.com>
* Petar Najman <petar.najman@modoolar.com>
* Aleksandar Gajić <igor.jovanovic@modoolar.com>
* Jasmina Nikolić <jasmina.nikolic@modoolar.com>
* Sladjan Kantar <sladjan.kantar@modoolar.com>
* Miroslav Nikolić <miroslav.nikolic@modoolar.com>
* Mladen Meseldžija <mladen.meseldzija@modoolar.com>

Maintainer
----------
![Modoolar logo](https://www.modoolar.com/web/image/ir.attachment/3461/datas)

This repository is maintained by Modoolar.

As Odoo Gold partner, our company is specialized in Odoo ERP customization and business solutions development.
Beside that, we build cool apps on top of Odoo platform.

To contribute to this module, please visit https://modoolar.com