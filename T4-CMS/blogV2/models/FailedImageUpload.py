from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import pytz # Import thư viện `pytz` để làm việc với múi giờ.
from datetime import datetime, timedelta
import base64

_logger = logging.getLogger(__name__)

class FailedImageUpload(models.Model):
    _name = 'failed.image.upload'
    _description = 'Failed Image Upload Tracking'

    blog_post_id = fields.Many2one('blog.post', string='Blog Post')
    image_src = fields.Char(string='Original Image URL')
    retry_count = fields.Integer(string='Retry Count', default=0)
    last_retry_date = fields.Datetime(string='Last Retry Date')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('failed', 'Permanently Failed')
    ], default='pending')


    def retry_failed_image_uploads(self):
        _logger.info('Retrying failed image uploads')
        
        # Tìm các ảnh chưa upload thành công
        failed_images = self.env['failed.image.upload'].search([
            ('status', '=', 'pending'),
            ('retry_count', '<', 3)  # Giới hạn số lần retry
        ])
        
        for failed_image in failed_images:
            try:
                # Lấy thông tin bài blog
                blog_post = failed_image.blog_post_id
                
                # Chuẩn bị thông tin đăng nhập và headers
                login_params = {
                    'database': blog_post.server_id.database,
                    'username': blog_post.server_id.username,
                    'password': blog_post.server_id.password,
                    'db_name_local': blog_post.server_id.db_name_local,
                    'server_id': blog_post.server_id.id,
                    'blog_post_id': blog_post.id
                }
                
                # Lấy session và headers
                session = self._authenticate_session(
                    blog_post.server_id.domain, 
                    login_params['database'], 
                    login_params['username'], 
                    login_params['password']
                )
                
                headers = {
                    'Content-Type': 'application/json',
                    'Cookie': f"session_id={session}"
                }
                
                # Thử upload lại ảnh
                attachment = self.env['ir.attachment'].search([
                    ('image_src', '=', failed_image.image_src)
                ], limit=1)
                
                if attachment:
                    new_url = self._upload_attachment_to_server(
                        login_params, 
                        base64.b64decode(attachment.datas), 
                        attachment.name, 
                        failed_image.image_src, 
                        blog_post.server_id.domain, 
                        headers
                    )
                    
                    if new_url:
                        # Upload thành công, xóa bản ghi failed image
                        failed_image.unlink()
                    else:
                        # Cập nhật thông tin retry
                        failed_image.write({
                            'retry_count': failed_image.retry_count + 1,
                            'last_retry_date': fields.Datetime.now(),
                            'status': 'failed' if failed_image.retry_count >= 2 else 'pending'
                        })
                
            except Exception as e:
                _logger.error(f"Error retrying image upload: {str(e)}")
                failed_image.write({
                    'retry_count': failed_image.retry_count + 1,
                    'last_retry_date': fields.Datetime.now(),
                    'status': 'failed' if failed_image.retry_count >= 2 else 'pending'
                })