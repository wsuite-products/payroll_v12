###################################################################################
# 
#    Copyright (C) 2018 WERP IT GmbH
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################

{
    "name": "WERP Utils",
    "summary": """Utility Features""",
    "version": '12.0.1.1.5',   
    "category": 'Extra Tools',   
    "license": "AGPL-3",
    "author": "WERP IT",
    "website": "https://www.werpit.at",
    "live_test_url": "https://demo.werpit.at/web/login",
    "contributors": [
        "Quadi",
    ],
    "depends": [
        "base_setup",
    ],
    "data": [
        "views/mixins_groups.xml",
        "views/res_config_settings_view.xml",
    ],
    "qweb": [
        "static/src/xml/*.xml",
    ],
    "images": [
        'static/description/banner.png'
    ],
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "application": False,
    "installable": True,
    "auto_install": True,
}
