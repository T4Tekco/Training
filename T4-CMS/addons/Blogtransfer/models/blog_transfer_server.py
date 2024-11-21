from base64 import b64encode
from odoo import models, fields, api, _  # Nhập các mô-đun cần thiết từ Odoo
from odoo.exceptions import UserError  # Nhập ngoại lệ UserError để xử lý lỗi
import requests  # Nhập thư viện requests để thực hiện các yêu cầu HTTP
import logging  # Nhập thư viện logging để ghi lại thông tin và lỗi
from urllib.parse import urlparse, urljoin
from odoo.http import request
from odoo.exceptions import ValidationError
import xmlrpc.client
_logger = logging.getLogger(__name__)  # Tạo logger để ghi lại thông tin

class Server(models.Model):
    _name = 'server'  # Định nghĩa tên model là 'server'
    _description = 'server'  # Mô tả ngắn về model

    avatar_128 = fields.Image( string="avatar 128", compute='_compute_avatar_128', max_width=128, max_height=128) # Trường ảnh đại diện cho server, có kích thước tối đa 128x128
    image_1920 = fields.Image(string="Avatar", max_width=1920, max_height=1920)  # Trường ảnh đại diện với kích thước lớn hơn

    name = fields.Char(string="Server Name", required=True)  # Tên của server
    domain = fields.Char(string="Domain", required=True)  # Tên miền của server
    database = fields.Char(string="Database")  # Cơ sở dữ liệu của server
    username = fields.Char(string="Username")  # Tên người dùng của server
    password = fields.Char(string="Password")  # Mật khẩu của server

    # Các trường dữ liệu One2many để liên kết với các model khác
    server_tag_ids = fields.One2many("server.tag", "server_id", string="Server Tags", compute="_compute_sync_tag")  # Liên kết với model 'server.tag' để lấy danh sách tags của server
    tag_mapping_ids = fields.One2many('tag.mapping', 'server_id', string='Tag Mappings', compute="_compute_sync_local_tag")  # Liên kết với model 'tag.mapping' để lấy danh sách tag mapping
    
    # Phương thức 'create' để xử lý việc tạo bản ghi mới
    def create(self, vals):
        server = self.env['server'].search(
            domain=[('name', '=', vals['name'])], limit=1)  # Kiểm tra xem tên server đã tồn tại chưa
        if server:
            raise UserError(_("Server Name already existed!"))  # Nếu server đã tồn tại, ném lỗi
        new_record = super(Server, self).create(vals)  # Nếu chưa tồn tại, tạo bản ghi mới
        return new_record

    # Phương thức 'write' để xử lý việc cập nhật bản ghi
    def write(self, vals):
        if vals.get('name', False):  # Kiểm tra nếu có thay đổi tên server
            server = self.env['server'].search(domain=[('name', '=', vals['name'])], limit=1)  # Kiểm tra xem tên server đã tồn tại chưa
            if server:
                raise UserError(_("Server Name already existed!"))  # Nếu đã tồn tại, ném lỗi
        new_record = super(Server, self).write(vals)  # Nếu không có lỗi, cập nhật bản ghi
        return new_record
    
        # Phương thức tính toán avatar 128px
    def _compute_avatar_128(self):
        for record in self:
            avatar = record['image_1920']
            if not avatar: # Nếu không có avatar, tạo avatar mặc định
                if record.id and record[record._avatar_name_field]:
                    avatar = record._avatar_generate_svg()
                else:
                    avatar = b64encode(record._avatar_get_placeholder())
            record['avatar_128'] = avatar # Gán giá trị avatar vào trường avatar_128

    @api.onchange('domain') # Sự kiện onchange khi domain thay đổi
    def _onchange_domain(self):
        """Chuẩn hóa domain khi người dùng nhập"""
        if self.domain:
            self.domain = self.normalize_domain(self.domain) #Gọi hàm normalize_domain để chuẩn hóa giá trị của domain mà người dùng đã nhập.

    def normalize_domain(self, domain):
        """Chuẩn hóa domain về format thống nhất"""
        if not domain:
            return domain
        # Chuẩn hóa domain
        # Loại bỏ khoảng trắng thừa
        domain = domain.strip()
        if not domain.startswith(('http://', 'https://')):
            domain = 'https://' + domain

        # Parse và rebuild URL để chuẩn hóa
        parsed = urlparse(domain)
        # Tạo base URL
        # Lấy hostname (và port nếu có)
        base_url = f"{parsed.scheme}://{parsed.netloc or parsed.path}"
        # Loại bỏ dấu / ở cuối
        base_url = base_url.rstrip('/')
        return base_url

    def call_api(self, data, url):       
        session_cookie = request.httprequest.cookies.get(
            'session_id') # Lấy session cookie của người dùng hiện tại từ yêu cầu HTTP.
        # Chuẩn bị headers với session
        headers = {
            'Content-Type': 'application/json', # Thông báo rằng dữ liệu gửi đi được định dạng dưới dạng JSON
            'Cookie': f'session_id={session_cookie}', # Gửi session ID hiện tại dưới dạng cookie để xác thực người dùng.
            'X-Openerp-Session-Id': request.session.sid,# Đây là session ID trong môi trường Odoo. 
            # request.session.sid: Lấy session ID từ đối tượng request trong Odoo. Điều này đảm bảo rằng yêu cầu đang được thực hiện trong cùng một phiên làm việc.
            'X-CSRF-Token': request.csrf_token() # CSRF Token được sử dụng để bảo vệ chống lại các cuộc tấn công Cross-Site Request Forgery (CSRF).
            # request.csrf_token(): Lấy token bảo mật từ đối tượng request. Token này đảm bảo yêu cầu API hợp lệ trong ngữ cảnh của phiên người dùng hiện tại.
        }
        # Gọi API
        response = requests.post(url=f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}{url}", json=data, timeout=30,  headers=headers,
                            cookies=request.httprequest.cookies) # Gửi yêu cầu POST đến API, bao gồm URL, dữ liệu JSON và header đã chuẩn bị, đồng thời truyền session cookie.
        response_data = response.json() # Chuyển đổi phản hồi từ API thành định dạng JSON.
        # Đồng bộ tags từ server từ xa 
        return response_data.get("result", {}) # Trả về kết quả từ phản hồi JSON (nếu có) hoặc một đối tượng rỗng nếu không có kết quả.

    def action_load_databases(self):
        # Chuẩn bị dữ liệu để gửi
        data = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'domain': self.domain,
            },
            'id': None
        }
        response = self.call_api(data, "/api/load/database") # Gọi API qua hàm call_api (một phương thức được định nghĩa trước trong module).
        if response['status'] == "error": # Nếu API trả về trạng thái "error"
            return {
                'type': 'ir.actions.client', # Loại: ir.actions.client.
                'tag': 'display_notification', # hiển thị thông báo
                'params': {
                    'title': 'Warning', # Tiêu đề thông báo ("Warning").
                    'message': response['message'], #Nội dung thông báo, lấy từ response['message'].
                    'type': 'warning', # Loại thông báo, ở đây là "warning".
                    'sticky': False, # Không cố định, thông báo sẽ tự động ẩn sau một thời gian.
                }
            }
        action = {
            'type': 'ir.actions.client', # hành động phía client.
            'tag': "Blogtransfer.database", # gắn với component Owl hiển thị dữ liệu
            'target': 'new',# mở trong cửa sổ mới hoặc dialog
            'name': "Load Database",
            'params': {
                'doamin': self.domain,# Giá trị domain mà người dùng đã nhập.
                'databases': response['databases'], # Danh sách cơ sở dữ liệu nhận được từ API (response['databases']).
                'server_id': self.id, # ID của server hiện tại.
            },
        }
        return action

    # Phương thức tính toán danh sách tags của server
    def _compute_sync_tag(self):
        """Compute method cho server_tag_ids và tag_mapping_ids"""
        for record in self:
            if not record.database: # Nếu không có cơ sở dữ liệu, xóa danh sách tags
                record.server_tag_ids = [(6, 0, [])]
            else:
                try:
                    server_tag_ids = []  # Khởi tạo danh sách tags
                    data = {  # Chuẩn bị dữ liệu gửi đến API
                        'jsonrpc': '2.0',
                        'method': 'call',
                        'params': {
                            'domain': record.domain,
                            'database': record.database,
                            'username': record.username,
                            'password': record.password
                        },
                        'id': None
                    }
                    remote_tags = self.call_api(data, "/api/compute/sync/tag") # Gọi API để đồng bộ tags
                    if not remote_tags:
                        record.server_tag_ids = [(6, 0, server_tag_ids)]  # Nếu không có tags, gán danh sách trống
                        continue
                    tag_server_ids_for_delete = [] # Danh sách các tag cần xóa
                    for tag_server in remote_tags: # Duyệt qua các tag từ server
                        
                        server_tag = self.env['server.tag'].search([  # Tìm kiếm tag trong hệ thống
                            ('server_id', '=', record.id), # Kiểm tra xem trường server_id trong bản ghi server.tag có khớp với record.id hay không.
                            ('tag_server_id', '=', tag_server['id'])], limit=1) # Kiểm tra xem trường tag_server_id trong bản ghi server.tag có khớp với giá trị id từ dictionary tag_server hay không.
                        if server_tag: # Nếu tag đã tồn tại, cập nhật thông tin
                            if server_tag.name != tag_server['name']:
                                server_tag.write({'name': tag_server['name']})
                        else: # Nếu chưa tồn tại, tạo mới tag
                            server_tag = self.env['server.tag'].create({ 
                                'name': tag_server['name'], #  Trường trong model server.tag để lưu tên của tag trên server.
                                'server_id': record.id, # Trường Many2one trong model server.tag, liên kết với bản ghi server hiện tại.
                                'tag_server_id': tag_server['id'] #Trường để lưu ID của tag trên server.
                            })
                        server_tag_ids.append(server_tag.id)  # Thêm ID tag vào danh sách
                        tag_server_ids_for_delete.append(tag_server['id'])  # Thêm ID tag vào danh sách xóa

                    # Xóa các tag không còn tồn tại trên server
                    if tag_server_ids_for_delete:
                        obsolete_tags = self.env['server.tag'].search([
                            ('server_id', '=', record.id),
                            ('tag_server_id', 'not in', tag_server_ids_for_delete)
                        ])
                        if obsolete_tags:
                            obsolete_tags.unlink()  # Xóa các tag không còn tồn tại
                    # Cập nhật các trường computed
                    record.server_tag_ids = [(6, 0, server_tag_ids)]
                except Exception as e:
                    _logger.error(f"Error in _compute_sync_tag for server {record.id}: {str(e)}") # Ghi lại lỗi vào log nếu có

    # Phương thức tính toán danh sách tag mapping (mối quan hệ giữa tag local và tag trên server)
    def _compute_sync_local_tag(self):
        for record in self:
            if not record.database:  # Nếu không có cơ sở dữ liệu, xóa danh sách tag mapping
                record.tag_mapping_ids = [(6, 0, [])]
            else:
                # Lấy tất cả blog tags hiện có
                local_blog_tags = self.env['blog.tag'].search([]) # Lấy tất cả blog tags hiện có
                local_blog_tag_ids = [] # Danh sách ID tag mapping
                local_blog_tag_ids_for_delete = [] # Danh sách tag cần xóa
                for tag in local_blog_tags:
                    # tìm kiếm tag.mapping nếu chưa có thì tạo
                    local_tag_mapping = self.env['tag.mapping'].search(
                        [('server_id', '=', self.id), ('local_tag_id', '=', tag.id)], limit=1)
                    if not local_tag_mapping: # Nếu tag mapping chưa tồn tại, tạo mới
                        local_tag_mapping = self.env['tag.mapping'].create({"name": tag.name, "server_id": self.id, "local_tag_id": tag.id})
                        self.tag_mapping_ids = [(4, local_tag_mapping.id)] # Thêm vào danh sách tag mapping
                    local_blog_tag_ids.append(local_tag_mapping.id) # Thêm ID tag mapping vào danh sách
                    local_blog_tag_ids_for_delete.append(tag.id)  # Thêm ID tag vào danh sách xóa
                # Tìm kiếm và xóa những tag mapping không có tag local với server id
                if local_blog_tag_ids != []:
                    local_tag_mapping = request.env['tag.mapping'].search(
                        [("server_id", "=", record.id), ("local_tag_id", "not in", local_blog_tag_ids_for_delete)])
                    if local_tag_mapping:
                        local_tag_mapping.unlink() # Xóa các tag mapping không còn tồn tại
                # Cập nhật lại danh sách tag mapping
                record.tag_mapping_ids = [(6, 0, local_blog_tag_ids)]

  