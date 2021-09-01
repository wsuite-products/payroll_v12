import base64
import os
import hashlib
import logging

from odoo import api, models, _, fields
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

import boto3


class IrAttachmentResized(models.Model):
    _name = 'ir.attachment.resized'
    _description = 'Url to resized image'

    attachment_id = fields.Many2one('ir.attachment')
    width = fields.Integer()
    height = fields.Integer()
    resized_attachment_id = fields.Many2one('ir.attachment', ondelete='cascade')


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    resized_ids = fields.One2many('ir.attachment.resized', 'attachment_id')

    def _get_s3_settings(self, param_name, os_var_name):
        config_obj = self.env['ir.config_parameter']
        res = config_obj.sudo().get_param(param_name)
        if not res:
            res = os.environ.get(os_var_name)
            if res:
                config_obj.sudo().set_param(param_name, res)
                _logger.info('parameter {} has been created from env {}'.format(param_name, os_var_name))
        return res

    @api.model
    def _get_s3_object_url(self, s3, s3_bucket_name, key_name, folder_name):
        bucket_location = s3.meta.client.get_bucket_location(Bucket=s3_bucket_name)
        location_constraint = bucket_location.get('LocationConstraint')
        domain_part = 's3' + '-' + location_constraint if location_constraint else 's3'
        if folder_name:
            key_name = "{0}/{1}".format(folder_name, key_name)
        object_url = "https://{1}.{0}.amazonaws.com/{2}".format(
            domain_part,
            s3_bucket_name,
            key_name)
        return object_url

    @api.model
    def _get_s3_resource(self):
        access_key_id = self._get_s3_settings('s3.access_key_id', 'S3_ACCESS_KEY_ID')
        secret_key = self._get_s3_settings('s3.secret_key', 'S3_SECRET_KEY')
        bucket_name = self._get_s3_settings('s3.bucket', 'S3_BUCKET')

        if not access_key_id or not secret_key or not bucket_name:
            _logger.info(_('Amazon S3 credentials are not defined properly. Attachments won\'t be saved on S3.'))
            return False

        s3 = boto3.resource(
            's3',
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_key,
            )
        bucket = s3.Bucket(bucket_name)
        if not bucket:
            s3.create_bucket(Bucket=bucket_name)
        return s3

    def _inverse_datas(self):
        condition = self._get_s3_settings('s3.condition', 'S3_CONDITION')
        if condition and not self.env.context.get('force_s3'):
            condition = safe_eval(condition, mode="eval")
            s3_records = self.sudo().search([('id', 'in', self.ids),
                                             ('res_id', '>', 0)] + condition)
        else:
            # if there is no condition or force_s3 in context
            # then store all attachments on s3
            s3_records = self

        if s3_records:
            s3 = self._get_s3_resource()
            if not s3:
                _logger.info('something wrong on aws side, keep attachments as usual')
                s3_records = self.env[self._name]
            else:
                s3_records = s3_records._filter_protected_attachments()
                s3_records = s3_records.filtered(lambda r: r.type != 'url')

        resized_to_remove = self.env['ir.attachment.resized'].sudo()
        HrEmployee = self.env['hr.employee'].sudo()
        ResPartner = self.env['res.partner'].sudo()
        ProductTemplate = self.env['product.template'].sudo()
        ProductSupplierinfo = self.env['product.supplierinfo'].sudo()
        for attach in self & s3_records:  # datas field has got empty somehow in the result of ``s3_records = self.sudo().search([('id', 'in', self.ids)] + condition)`` search for non-superusers but it is in original recordset. Here we use original (with datas) in case it intersects with the search result
            _logger.info("attach ===> %s", attach)
            resized_to_remove |= attach.sudo().resized_ids
            value = attach.datas
            bin_data = base64.b64decode(value) if value else b''
            fname = hashlib.sha1(bin_data).hexdigest()
            contentdisposition = ''
            if 'pdf' in attach.mimetype:
                contentdisposition =\
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
            if self.res_model == 'hr.employee' and self.res_field == 'image':
                employee_id = HrEmployee.search([('id', '=', self.res_id)])
                if employee_id:
                    employee_id.profile_image_url = url_data
            if self.res_model == 'res.partner' and self.res_field == 'image':
                partner_id = ResPartner.search([('id', '=', self.res_id)])
                partner_id.image_url = url_data
            if self.res_model == 'product.template' and self.res_field == 'image':
                product_tmpl_id = ProductTemplate.search([('id', '=', self.res_id)])
                product_tmpl_id.image_url = url_data
            if self.res_model == 'product.supplierinfo' and self.res_field == 'image':
                product_sup_info_id = ProductSupplierinfo.search([('id', '=', self.res_id)])
                product_sup_info_id.image_url = url_data
            vals = {
                'file_size': len(bin_data),
                'checksum': self._compute_checksum(bin_data),
                'index_content': self._index(bin_data, attach.datas_fname, attach.mimetype),
                'store_fname': fname,
                'db_datas': False,
                'type': 'url',
                'url': url_data,
            }
            super(IrAttachment, attach.sudo()).write(vals)
        resized_to_remove.mapped('resized_attachment_id').unlink()
        resized_to_remove.unlink()
        super(IrAttachment, self - s3_records)._inverse_datas()
