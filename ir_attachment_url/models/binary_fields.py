from odoo import fields
from . import image


class Binary(fields.Binary):

    def create(self, record_values):
        assert self.attachment
        if not record_values:
            return
        # create the attachments that store the values
        env = record_values[0][0].env
        with env.norecompute():
            if record_values[0][1] and image.check_url(record_values[0][1]):
                env['ir.attachment'].sudo().with_context(
                    binary_field_real_user=env.user,
                ).create([{
                    'name': self.name,
                    'res_model': self.model_name,
                    'res_field': self.name,
                    'res_id': record.id,
                    'type': 'url',
                    'datas': None,
                    'url': record_values[0][1],
                }
                    for record, value in record_values
                    if value
                ])
            else:
                super(Binary, self).create(record_values)

    def write(self, records, value):
        domain = [
            ('res_model', '=', records._name),
            ('res_field', '=', self.name),
            ('res_id', 'in', records.ids),
        ]
        atts = records.env['ir.attachment'].sudo().search(domain)
        if value and atts.url and atts.type == 'url' and not \
                image.check_url(value):
            atts.write({
                'url': None,
                'type': 'binary',
            })
        if value and image.check_url(value):
            with records.env.norecompute():
                if value:
                    import urllib.request
                    with urllib.request.urlopen(value) as response:
                        info = response.info()
                        mimetype = info.get_content_type()

                    index_content = \
                        records.env['ir.attachment']._index(
                            None, None, mimetype)
                    # update attachments
                    atts.write({
                        'url': value,
                        'mimetype': mimetype,
                        'datas': None,
                        'type': 'url',
                        'index_content': index_content,
                    })
                    # create Other Attachment
                    for record in (records -
                                   records.browse(atts.mapped('res_id'))):
                        atts.create({
                            'name': self.name,
                            'res_model': record._name,
                            'res_field': self.name,
                            'res_id': record.id,
                            'type': 'url',
                            'url': value,
                            'mimetype': mimetype,
                            'index_content': index_content,
                        })
                else:
                    atts.unlink()
        else:
            super(Binary, self).write(records, value)


fields.Binary = Binary
