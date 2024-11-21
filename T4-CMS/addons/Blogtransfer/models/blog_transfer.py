import xmlrpc.client
import pytz
from datetime import datetime
import logging
import requests
from odoo.exceptions import UserError
from odoo import models, fields, api, _
from odoo import models, fields, api, _  # Nhập các mô-đun cần thiết từ Odoo
from odoo.exceptions import UserError  # Nhập ngoại lệ UserError để xử lý lỗi
import requests  # Nhập thư viện requests để thực hiện các yêu cầu HTTP
import logging  # Nhập thư viện logging để ghi lại thông tin và lỗi
from odoo.http import request
from odoo.addons.Blogtransfer.controllers.create_blog import BlogController
import json
_logger = logging.getLogger(__name__)  # Tạo logger để ghi lại thông tin

# Định nghĩa class BlogTransfer, là một model trong Odoo
class BlogTransfer(models.Model):
    _name = 'blog.transfer'  # Tên model
    _description = 'Blog Transfer to Multiple Servers'  # Mô tả model

    # Định nghĩa các trường (fields) cho model
    name = fields.Char(string="Tên chiến dịch chuyển", required=True)  # Tên chiến dịch chuyển, bắt buộc nhập

    selected_post_id = fields.Many2one('blog.post', string='Bài viết được chọn', store=True)  # Trường liên kết tới bài viết được chọn
    blog_tag_ids = fields.Many2many('blog.tag', related='selected_post_id.tag_ids', string='Tag bài viết được chọn')  # Lấy các tag từ bài viết đã chọn
    server_mapping_id = fields.Many2one('server', string='Server Mapping')  # Server đích để chuyển bài viết
    available_server_tags = fields.Many2many('server.tag', string='Tag server được chọn')  # Tag trên server đích

     # Trạng thái của tiến trình chuyển
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('in_progress', 'Đang chuyển'),
        ('done', 'Hoàn thành'),
        ('failed', 'Thất bại')
    ], string='Trạng thái', default='draft')
   
    start_time = fields.Datetime(string='Thời gian bắt đầu')# Thời gian bắt đầu chuyển
    end_time = fields.Datetime(string='Thời gian kết thúc')# Thời gian kết thúc
    blog_post_write_date = fields.Datetime(string='Blog last update on', related='selected_post_id.write_date')  # Ngày sửa bài viết lần cuối

    # Trường hiển thị tag từ server và map giữa server/tag
    server_tag_ids = fields.One2many("server.tag", "server_id", string="Server Tags", related='server_mapping_id.server_tag_ids')
    tag_mapping_ids = fields.One2many('tag.mapping', 'server_id', string='Tag Mappings', related='server_mapping_id.tag_mapping_ids')
    
    error_log = fields.Text(string='Log lỗi') # log lỗi
    is_error = fields.Boolean(string='Is error') # Trạng thái lỗi

    scheduled_date = fields.Datetime(
        string='Đặt thời gian dự kiến chuyển',
        required=True,
        default=lambda self: fields.Datetime.now()
    )

    _blog_controller = None # Biến class để lưu instance của controller để gọi hàm tạo ở api thay vì gọi api thì api tích hợp trong đây

    @api.constrains('scheduled_date')
    def _check_scheduled_date(self):
        for record in self:
            if record.scheduled_date < fields.Datetime.now():
                raise UserError(_('Thời gian dự kiến chuyển phải lớn hơn thời gian hiện tại!'))
            
    @classmethod
    def get_blog_controller(cls):
        """ Singleton pattern để lấy hoặc tạo instance của BlogController """
        if not cls._blog_controller:  # Kiểm tra nếu `_blog_controller` chưa được khởi tạo
            cls._blog_controller = BlogController()  # Nếu `_blog_controller` chưa tồn tại, tạo một instance của `BlogController`
        return cls._blog_controller  # Trả về instance đã được khởi tạo (hoặc đã tồn tại trước đó)
    
    def create(self, vals):
            new_record = super(BlogTransfer, self).create(vals)
            self.env['blog.transfer.scheduler'].create({
                'blog_transfer_id': new_record.id
            })
            return new_record

    @api.onchange('selected_post_id', 'server_mapping_id')
    def _onchange_available_server_tags(self):
        if self.blog_tag_ids and self.server_mapping_id:
            server_tags = self.env['server.tag'].search([
                ('local_tag_ids', 'in', self.blog_tag_ids.ids),
                ('server_id', 'in', self.server_mapping_id.ids)
            ])
            self.available_server_tags = [(6, 0, server_tags.ids)]  # Gán các tag này vào available_server_tags
        else:
            self.available_server_tags = [(6, 0, [])] # Nếu không có tag, xóa danh sách

    def _call_create_blog_api(self, server, post, server_tag_ids):
        """Gọi trực tiếp method create_blog từ BlogController Returns: (success, message)"""
        try:
            # Lấy controller instance từ singleton
            blog_controller = self.get_blog_controller()
           # Chuẩn bị params gửi đi 
            params = {
                'blog_folder': post.blog_id.name,  # Thư mục blog
                'title': post.name,  # Tiêu đề bài viết
                'content': post.content,  # Nội dung bài viết
                'server_tag_ids': server_tag_ids,  # Tag cần tạo trên server
                'domain': server.domain,  # Domain của server đích 
                'database': server.database,  # Tên database
                'username': server.username,  # Tên người dùng
                'password': server.password,  # Mật khẩu
                'blog_transfer_id': self.id,  # ID của chiến dịch chuyển
                'db_name_local': self.env.cr.dbname # Tên cơ sở dữ liệu của hệ thống hiện tại
            }
            # Gọi method create_blog
            result = blog_controller.create_blog(**params)
            # Kiểm tra kết quả
            if result.get('status') == "success":
                return True, result.get('message')
            else:
                error_message = result.get(
                    'message') or 'Unknown error occurred'
                return False, f"Error: {error_message}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    # Hàm bắt đầu quá trình chuyển bài viết
    def action_start_transfer(self):      
       # Khởi tạo lại trạng thái
        self.write({
            'state': 'in_progress', #Đặt trạng thái của quá trình chuyển bài viết
            'start_time': fields.Datetime.now(),#Ghi lại thời gian bắt đầu
            'error_log': '' #xóa log lỗi trước đó
        })
        isSuccess = False # Biến theo dõi trạng thái
        try:
            server = self.server_mapping_id # Lấy thông tin server
            post = self.selected_post_id # Lấy thông tin bài viết
            try:
                # Chuẩn bị dữ liệu tags
                server_tag_ids = self.available_server_tags.mapped('tag_server_id')
                # Gọi API và xử lý kết quả
                success, message = self._call_create_blog_api(server, post, server_tag_ids) # success Trạng thái thành công. và message Thông điệp phản hồi.
                # Ghi log và cập nhật counters
                self._log_transfer_result(post, server, success, message) #Ghi lại kết quả chuyển bài viết vào log thông qua hàm _log_transfer_result.
                if success:
                    isSuccess = True
                else:
                    isSuccess = False
            except Exception as e:
                isSuccess = False
                self._log_transfer_result(post, server, isSuccess,f"Error processing post: {str(e)}")
        except Exception as e:
            self._log_transfer_result(self.env['blog.post'], server, isSuccess,f"Critical error during transfer: {str(e)}") # Ghi log nếu xảy ra lỗi nghiêm trọng (bên ngoài các bước cụ thể).           
        finally:
            # Cập nhật trạng thái cuối cùng
            end_status = 'done' if isSuccess else 'failed'
            data_update = {
                'state': end_status, #Cập nhật trạng thái (state) là done (thành công) hoặc failed (thất bại).
                "is_error": False if isSuccess else True,#Đánh dấu trạng thái lỗi
                'end_time': fields.Datetime.now(),#Ghi lại thời gian kết thúc
            }
            if isSuccess:
                scheduler = self.env['blog.transfer.scheduler'].search( # tìm và xóa dựa vào blog_transfer_id
                    [('blog_transfer_id', '=', self.id)], limit=1)
                if  scheduler:
                    scheduler.unlink()

            self.write(data_update)
            # Log tổng kết ,Tạo một bản tóm tắt quá trình chuyển bài viết.
            summary = f"""
            Transfer completed:
            - Start time: {self.start_time}
            - End time: {self.end_time}
            - Final status: {end_status}
            """
            # Ghi log tổng kết vào trường error_log. Nếu đã có log trước đó, nối thêm vào sau log cũ.
            error_log = ""
            if self.error_log:
                error_log = self.error_log + "\n\n" + summary
            else:
                error_log = summary
            self.write({"error_log": error_log})

    def _log_transfer_result(self, post, server, success, message):
        """Ghi log kết quả chuyển bài viết """
         # Hàm này dùng để ghi lại kết quả chuyển bài viết (thành công hoặc thất bại).
        timestamp = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S UTC') # Lấy thời gian hiện tại (theo UTC) và định dạng thành chuỗi: 'YYYY-MM-DD HH:mm:ss UTC'.
        log_message = f"[{timestamp}] Post '{post.name}' to server '{server.name}': " # Tạo chuỗi log chứa thời gian, tên bài viết (`post.name`), và tên máy chủ đích (`server.name`).
        log_message += "SUCCESS" if success else "FAILED"  # Thêm kết quả (`SUCCESS` hoặc `FAILED`) vào chuỗi log dựa trên giá trị của `success`.
        log_message += f" - {message}" # Thêm thông điệp chi tiết (nếu có) vào chuỗi log.
        error_log = "" # Khởi tạo biến `error_log` để lưu thông tin log nếu có lỗi xảy ra.
        if not success:# Nếu lỗi, thêm vào error_log
            if self.error_log: 
                error_log = self.error_log + "\n" + log_message  # Nếu đã có log lỗi trước đó, nối chuỗi log mới vào sau log cũ, cách nhau bằng dòng trống.
            else:
                error_log = log_message # Nếu chưa có log lỗi, gán log mới vào `error_log`.
            self.write({'error_log': error_log
            })  # Cập nhật trường `error_log` của bản ghi hiện tại với thông tin log lỗi mới.            

# Tìm kiếm hình đã thay đổi
class IrAttachment(models.Model):
    _inherit = 'ir.attachment' # Kế thừa (inherit) từ model ir.attachment để mở rộng thêm trường mới image_src.
    image_src = fields.Char(store=True) # là một trường kiểu chuỗi (Char) và có thể được lưu trữ (store=True) trong cơ sở dữ liệu.




