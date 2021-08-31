import base64
import hashlib
import logging

from odoo import api, models, _, fields

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def _inverse_datas(self):
        if not self.env.context.get('force_s3'):
            s3_records = self.sudo().search([('id', 'in', self.ids),
                                             ('res_id', '>', 0),
                                             ('res_model', '=', 'hr.novelty')])
        else:
            s3_records = self

        if s3_records:
            s3 = self._get_s3_resource()
            if not s3:
                _logger.info(
                    'something wrong on aws side, keep attachments as usual')
                s3_records = self.env[self._name]
            else:
                s3_records = s3_records._filter_protected_attachments()
                s3_records = s3_records.filtered(lambda r: r.type != 'url')

        resized_to_remove = self.env['ir.attachment.resized'].sudo()
        HrNovelty = self.env['hr.novelty'].sudo()
        for attach in self & s3_records:
            _logger.info("attach Novelty ==> %s", attach)
            resized_to_remove |= attach.sudo().resized_ids
            value = attach.datas
            bin_data = base64.b64decode(value) if value else b''
            fname = hashlib.sha1(bin_data).hexdigest()
            contentdisposition = ''
            if 'pdf' in attach.mimetype:
                contentdisposition = \
                    'inline; filename={0}'.format(attach.datas_fname)
            bucket_name = self._get_s3_settings('s3.bucket', 'S3_BUCKET')
            folder_name = self._get_s3_settings('s3.folder', 'S3_FOLDER')
            s3.Bucket(bucket_name).put_object(
                Key='{1}/{0}'.format(fname, folder_name),
                Body=bin_data,
                ACL='public-read',
                ContentDisposition=contentdisposition,
                ContentType=attach.mimetype,
            )
            url_data = self._get_s3_object_url(s3, bucket_name, fname,
                                               folder_name)
            hr_novelty_id = HrNovelty.search([('id', '=', self.res_id)])
            if attach.res_field == 'original_maternity_leave':
                hr_novelty_id.sudo().with_context(
                    support_data=True).original_maternity_leave_url = url_data
            elif attach.res_field == 'certificate_week_of_gestation':
                hr_novelty_id.sudo().with_context(
                    support_data=True).certificate_week_of_gestation_url =\
                    url_data
            elif attach.res_field == 'birth_certificate':
                hr_novelty_id.sudo().with_context(
                    support_data=True).birth_certificate_url = url_data
            elif attach.res_field == 'certificate_born_alive':
                hr_novelty_id.sudo().with_context(
                    support_data=True).certificate_born_alive_url = url_data
            elif attach.res_field == 'support':
                hr_novelty_id.sudo().with_context(support_data=True).write({
                    'support_attachment_url': url_data,
                    'support_size': len(bin_data),
                    'support_name': hr_novelty_id.file_name})
            vals = {
                'file_size': len(bin_data),
                'checksum': self._compute_checksum(bin_data),
                'index_content': self._index(
                    bin_data, attach.datas_fname, attach.mimetype),
                'store_fname': fname,
                'db_datas': False,
                'type': 'url',
                'url': url_data,
            }
            super(IrAttachment, attach.sudo()).write(vals)
        resized_to_remove.mapped('resized_attachment_id').unlink()
        resized_to_remove.unlink()
        super(IrAttachment, self - s3_records)._inverse_datas()
