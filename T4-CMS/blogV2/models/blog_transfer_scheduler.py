from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import pytz
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class BlogTransferScheduler(models.Model):
    _name = 'blog.transfer.scheduler'
    _description = 'Blog Transfer Scheduler'

    name = fields.Char(string='Tên Chiến Dịch', required=True)
    blog_transfer_id = fields.Many2one(
        'blog.transfer',
        string='Chiến dịch chuyển',
    )
   
