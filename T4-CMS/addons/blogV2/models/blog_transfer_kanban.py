from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import pytz
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class BlogTransferkanban(models.Model):
    _name = 'blog.transfer.kanban'
    _description = 'Blog Transfer kanban'

    name = fields.Char(string='Kanban', required=True)
    blog_transfer_ids = fields.Many2many(
        'blog.transfer',
        'blog_transfer_kanban_rel',
        'kanban_id',
        'transfer_id',
        string='Các chiến dịch chuyển',
        required=True
    )

    cron_id = fields.Many2one(
        'ir.cron',
        string='Scheduled Job',
        ondelete='cascade'
    )

    interval_number = fields.Integer(
        default=1,
        string='Repeat Every',
        help="Repeat every x."
    )

    interval_type = fields.Selection([
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months')
    ], string='Interval Unit', default='days')

    numbercall = fields.Integer(
        string='Number of Calls',
        default=-1,
        help='How many times the method is called.\n'
             '-1 = no limit'
    )

    doall = fields.Boolean(
        string='Repeat Missed',
        help="Specify if missed occurrences should be executed when the server restarts."
    )

    nextcall = fields.Datetime(
        string='Next Execution Date',
        readonly=False,
        compute="_compute_nextcall",
        default=fields.Datetime.now,
    )

    active = fields.Boolean(default=True)
    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user
    )

    state = fields.Selection([
        ('draft', 'Nháp'),
        ('running', 'Đang chạy'),
        ('done', 'Hoàn thành'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', default='draft')

    def _compute_nextcall(self):
        for record in self:
            if not record.cron_id:
                record.nextcall = fields.Datetime.now()
            else:
                record.nextcall = record.cron_id.nextcall

    @api.model
    def action_show(self):
        form_view_id = self.env.ref(
            'blogV2.view_blog_transfer_kanban_form').id
        record = self.env['blog.transfer.kanban'].search([], limit=1)
        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'blog.transfer.kanban',
            'name': 'Blog Transfer kanban',
            'view_mode': 'form',
            'res_id': record.id,
            'views': [[form_view_id, 'form']],
            'domain': [],
            'context': {}
        }
        return action

    @api.model
    def _run_transfer_jobs_kanban(self):
        """Phương thức được gọi bởi cron job để thực hiện các chiến dịch chuyển"""
        kanbans = self.search([
            ('active', '=', True)
        ])
        for kanban in kanbans:
            _logger.info(kanban)
            try:
                # Đánh dấu các chiến dịch đang được xử lý
                transfer_jobs = kanban.blog_transfer_ids.filtered(
                    lambda x: x.state in ['draft', 'failed']
                )
                if transfer_jobs:
                    _logger.info(
                        f"Starting scheduled transfer for {kanban.name}")

                    # Thực hiện chuyển cho từng chiến dịch
                    for transfer in transfer_jobs:
                        try:
                            transfer.action_start_transfer()
                        except Exception as e:
                            _logger.error(
                                f"Error processing transfer {transfer.name}: {str(e)}")
                            continue

                    kanban.write({'state': 'done'})

            except Exception as e:
                _logger.error(f"Error in kanban {kanban.name}: {str(e)}")

    def _prepare_cron_vals(self):
        """Chuẩn bị giá trị cho cron job"""
        return {
            'name': f'Blog Transfer Schedule: {self.name}',
            'model_id': self.env['ir.model'].search([('model', '=', self._name)]).id,
            'state': 'code',
            'code': 'model._run_transfer_jobs()',
            'user_id': self.user_id.id,
            'interval_number': self.interval_number,
            'interval_type': self.interval_type,
            'numbercall': self.numbercall,
            'doall': self.doall,
            'nextcall': self.nextcall,
        }

    @api.model
    def create(self, vals):
        """Override create để tạo cron job khi tạo mới record"""
        record = super(BlogTransferkanban, self).create(vals)

        cron = self.env['ir.cron'].sudo().create(record._prepare_cron_vals())
        record.write({
            'cron_id': cron.id,
            'state': 'running'
        })
        # Tạo cron job
        cron = self.env['ir.cron'].sudo().create(record._prepare_cron_vals())
        record.write({
            'cron_id': cron.id,
            'state': 'running'
        })

        return record

    def write(self, vals):
        """Override write để cập nhật cron job khi cập nhật record"""
        result = super(BlogTransferkanban, self).write(vals)
        if vals.get('active', None) == None:
            for record in self:
                # Kiểm tra các trường liên quan đến cron
                cron_related_fields = [
                    'interval_number', 'interval_type', 'numbercall',
                    'doall', 'nextcall', 'active', 'user_id'
                ]

                if any(field in vals for field in cron_related_fields):
                    if record.cron_id:
                        # Cập nhật cron job hiện tại
                        record.cron_id.write(record._prepare_cron_vals())
                    else:
                        # Tạo mới cron job nếu chưa có
                        cron = self.env['ir.cron'].sudo().create(
                            record._prepare_cron_vals())
                        record.write({
                            'cron_id': cron.id,
                            'state': 'running'
                        })
        return result

    def unlink(self):
        """Xóa cả cron job khi xóa bản ghi"""
        for record in self:
            if record.cron_id:
                record.cron_id.unlink()
        return super(BlogTransferkanban, self).unlink()

    def action_deactivate(self):
        """Hủy kích hoạt lập lịch chuyển"""
        if self.cron_id:
            _logger.info(self.cron_id)
            self.cron_id.write({'active': False})
        self.write({
            'state': 'cancelled',
            'active': False
        })

    def action_activate(self):
        """Kích hoạt lập lịch chuyển"""
        if self.cron_id:
            self.cron_id.write({'active': True})
        self.write({
            'state': 'running',
            'active': True
        })
