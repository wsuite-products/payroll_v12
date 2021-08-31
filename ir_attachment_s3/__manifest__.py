{
    "name": """S3 Attachment Storage""",
    "summary": """Upload attachments on Amazon S3""",
    "category": "Tools",
    "images": [],
    "version": "12.0",
    "application": False,

    "author": "IT-Projects LLC, Ildar Nasyrov, Quadi",
    "depends": [
        'base_setup',
        'ir_attachment_url',
        'hr',
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "views/res_partner_view.xml",
    ],
    "qweb": [
    ],
    "demo": [
    ],

    "post_load": None,
    "pre_init_hook": None,
    "post_init_hook": None,

    "auto_install": False,
    "installable": True,
}
