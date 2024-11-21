from odoo import models, fields, api, _  # Import các module từ Odoo
from odoo.exceptions import UserError  # Import ngoại lệ UserError
import logging  # Dùng để ghi log
import pytz  # Thư viện xử lý múi giờ
from datetime import datetime, timedelta  # Dùng để xử lý ngày và giờ
_logger = logging.getLogger(__name__)  # Tạo logger để ghi log cho module này

class BlogTransferScheduler(models.Model):
    _name = 'blog.transfer.scheduler'  # Tên model
    _description = 'Blog Transfer Scheduler'  # Mô tả model
    
    blog_transfer_id = fields.Many2one('blog.transfer',string='Chiến dịch chuyển',required=True)# Danh sách các chiến dịch chuyển liên kết

    @api.model
    def _run_transfer_jobs(self):
        """Phương thức được gọi bởi cron job để thực hiện các chiến dịch chuyển"""
        current_time = fields.Datetime.now()
        schedulers = self.search([])
        for scheduler in schedulers:
            try:
                if scheduler.blog_transfer_id.scheduled_date <= current_time:
                    scheduler.blog_transfer_id.action_start_transfer()
            except Exception as e:
                _logger.error(f"Error processing transfer: {str(e)}")
                continue