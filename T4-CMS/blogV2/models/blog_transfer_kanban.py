from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import pytz # Import thư viện `pytz` để làm việc với múi giờ.
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class BlogTransferkanban(models.Model):
    _name = 'blog.transfer.kanban'
    _description = 'Blog Transfer kanban'

    name = fields.Char(string='Kanban', required=True)

    blog_post_ids = fields.Many2many(
        'blog.post',
        'blog_post_kanban_ref',
        'kanban_id',
        'blog_post_id',
        string='Các chuyến dịch chuyển',
        required=True
    )

    # Liên kết với cron job, sẽ bị xóa nếu bản ghi này bị xóa.
    cron_id = fields.Many2one(
        'ir.cron',
        string='Scheduled Job',
        ondelete='cascade'
    )

    # Số lượng khoảng thời gian giữa các lần thực thi cron job.
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

    # Số lần gọi phương thức, mặc định là không giới hạn.
    numbercall = fields.Integer(
        string='Number of Calls',
        default=-1,
        help='How many times the method is called.\n'
             '-1 = no limit'
    )

    # Cho phép thực hiện các lần bị bỏ lỡ khi server khởi động lại.
    doall = fields.Boolean(
        string='Repeat Missed',
        help="Specify if missed occurrences should be executed when the server restarts."
    )

    # Thời gian thực hiện tiếp theo, được tính toán tự động.
    nextcall = fields.Datetime(
        string='Next Execution Date',
        readonly=False,
        compute="_compute_nextcall",
        default=fields.Datetime.now,
    )

    active = fields.Boolean(default=True)   # Trạng thái kích hoạt của bản ghi, mặc định là `True`.
    user_id = fields.Many2one( # Người dùng tạo bản ghi, mặc định là người dùng hiện tại.
        'res.users',
        string='User',
        default=lambda self: self.env.user
    )

    state = fields.Selection([   # Trạng thái của bản ghi, mặc định là `Nháp`.
        ('draft', 'Nháp'),
        ('running', 'Đang chạy'),
        ('done', 'Hoàn thành'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', default='draft')

    def _compute_nextcall(self):
        _logger.info('def _comute_nextcall')
        for record in self:
            if not record.cron_id:
                record.nextcall = fields.Datetime.now()
            else:
                record.nextcall = record.cron_id.nextcall

    @api.model
    def action_show(self):  # Phương thức mở form xem chi tiết bản ghi đầu tiên.
        _logger.info('def action_show')
        form_view_id = self.env.ref(
            'blogV2.view_blog_transfer_kanban_form').id
        record = self.env['blog.transfer.kanban'].search([], limit=1)
        # Xây dựng một action dictionary để mở form view cho bản ghi đầu tiên
        action = {
            'type': 'ir.actions.act_window',  # Loại action là 'act_window', mở cửa sổ mới
            'res_model': 'blog.transfer.kanban',  # Xác định model của bản ghi sẽ hiển thị trong action
            'name': 'Blog Transfer kanban',  # Tên hiển thị của action trong giao diện người dùng
            'view_mode': 'form',  # Chế độ hiển thị là form view
            'res_id': record.id,  # ID của bản ghi mà form view sẽ mở
            'views': [[form_view_id, 'form']],  # Chỉ định form view sẽ sử dụng, với ID form_view_id đã lấy ở trên
            'domain': [],  # Không áp dụng bộ lọc domain nào cho các bản ghi
            'context': {}  # Không truyền thêm context nào trong action này
        }
        return action

    def _prepare_cron_vals(self):
        _logger.info('def _prepare_cron_vals')
        """Chuẩn bị giá trị cho cron job"""

        return {
            'name': f'Blog Transfer Schedule: {self.name}',
            'model_id': self.env['ir.model'].search([('model', '=', self._name)]).id, # # Lấy `id` của model hiện tại (`self._name`) từ bảng `ir.model`.
            'state': 'code',     # Trạng thái cron job sẽ được đặt là 'code', tức là thực thi đoạn mã Python được cung cấp.
            'code': 'model._run_transfer_jobs()', # Cron job sẽ gọi phương thức này
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
        # Tạo bản ghi và cron job cho bản ghi đó
        record = super(BlogTransferkanban, self).create(vals)
        cron = self.env['ir.cron'].sudo().create(record._prepare_cron_vals())

        # Gán cron job ID cho bản ghi và đánh dấu trạng thái là 'running'
        record.write({
            'cron_id': cron.id,
            'state': 'running'
        })
        return record
   
    def write(self, vals):
        """Override write để cập nhật cron job khi cập nhật record"""
        # Gọi phương thức write gốc
        result = super(BlogTransferkanban, self).write(vals)

        # Kiểm tra nếu trường 'active' không bị thay đổi, thì cập nhật các giá trị liên quan đến cron
        if vals.get('active', None) == None:
            for record in self:
                # Kiểm tra các trường liên quan đến cron
                cron_related_fields = [
                    'interval_number', 'interval_type', 'numbercall',
                    'doall', 'nextcall', 'active', 'user_id'
                ]

                # Nếu có trường nào liên quan đến cron được thay đổi, sửa đổi cron job
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
        return super(BlogTransferkanban, self).unlink()     # Gọi phương thức unlink gốc

    def action_deactivate(self):
        """Hủy kích hoạt lập lịch chuyển"""
        if self.cron_id:
            _logger.info(self.cron_id)
            self.cron_id.write({'active': False})  # Đánh dấu cron job là không hoạt động
        self.write({
            'state': 'cancelled',
            'active': False
        })

    def action_activate(self):
        _logger.info(f'def action_activate')
        """Kích hoạt lập lịch chuyển"""
        if self.cron_id:
            self.cron_id.write({'active': True})
        self.write({   # Cập nhật trạng thái thành 'running' và 'active' thành True
            'state': 'running',
            'active': True
        })


    @api.model
    def _run_transfer_jobs(self):
        _logger.info('def _run_transfer_jobs_kanban')
        """Phương thức được gọi bởi cron job để thực hiện các chiến dịch chuyển"""
        # Lấy tất cả các Kanban blog đang hoạt động
        kanbans = self.search([
            ('active', '=', True)
        ])

        _logger.info(f'kanbans: {kanbans}')
        for kanban in kanbans:
            _logger.info(kanban)
            try:

                # blog_posts = kanban.blog_post_ids.filtered(
                #     lambda x: x.is_published == False
                # )
                blog_posts = kanban.blog_post_ids

                _logger.info(f'blog_post arr: {blog_posts}')

                if blog_posts:
                    
                    # Thực hiện chuyển cho từng chiến dịch
                    for blog_post in blog_posts:
                        _logger.info(f'Ten blog_post: {blog_post.name}')
                        try:
                            self.action_start_publish(blog_post)
                        except Exception as e:
                            _logger.error(
                                f"Error processing blog_post {blog_post.name}: {str(e)}")
                            continue
                    
                    # Đánh dấu kanban là 'done' sau khi hoàn tất chuyển
                    kanban.write({'state': 'done'})

            except Exception as e:
                _logger.error(f"Error in kanban {kanban.name}: {str(e)}")


    def action_start_publish(self, blog_post):
        _logger.info('def action_start_publish')

        # Kiểm tra nếu blog_post không tồn tại
        if not blog_post:
            _logger.info('Blog post is not provided or invalid.')
            return

        try:
            blog_post.write({
                'is_published': True
                })
            _logger.info(f"Blog post '{blog_post.name}' has been published.")
        except Exception as e:
            _logger.error(f"Exception occurred when updating blog post: {str(e)}")


    # def action_start_publish(self, blog_post):
    #     _logger.info('def action_start_publish')

    #     try: 
    #         if blog_post:
    #             if not blog_post.is_published:
    #                 blog_post.write({
    #                     'is_published': True
    #                 })
    #             _logger.info(f'blog_post.is_published: {blog_post.is_published}')
    #     except Exception as e: 
    #         _logger.info(f'Exception occured when write blog_post: {str(e)}')

