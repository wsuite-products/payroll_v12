{
    "name": "Attachment Url",
    "summary": """Use attachment URL and upload data to external storage""",
    "category": "Tools",
    "images": [],
    "version": "12.0",
    "application": False,

    "author": "IT-Projects LLC, Ildar Nasyrov, Destiny",
    "license": "AGPL-3",
    "depends": [
        "web",
    ],
    "data": [
        "views/ir_attachment_url_template.xml",
        "demo/ir_attachment.xml",
    ],
    "qweb": [
        "static/src/xml/ir_attachment_url.xml",
    ],
    "demo": [
    ],

    "post_load": "post_load",
    "pre_init_hook": None,
    "post_init_hook": None,

    "auto_install": False,
    "installable": True,
}
