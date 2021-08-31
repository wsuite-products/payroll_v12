#!/bin/sh
COMPANY_DB=$1
BUCKET=$2
KEY=$3

aws s3 cp s3://${BUCKET}/${KEY} /tmp/
mkdir -p /filestore/odoo_prod_filestore/Odoo/filestore/${COMPANY_DB}
unzip -o /tmp/filestore.zip -d /filestore/odoo_prod_filestore/Odoo/filestore/${COMPANY_DB}/
chown -R odoo12:odoo12 /filestore/odoo_prod_filestore/Odoo/filestore/${COMPANY_DB}/
chmod -R 755 /filestore/odoo_prod_filestore/Odoo/filestore/${COMPANY_DB}/
chown -R odoo12:odoo12 /filestore/odoo_prod_filestore/Odoo/filestore/${COMPANY_DB}/
systemctl restart nginx
systemctl restart odoo12
