from odoo import http  # Nhập module http của Odoo
from odoo.http import request, Response  # Nhập các đối tượng 'request' và 'Response' từ Odoo
import json  # Nhập thư viện json để xử lý dữ liệu JSON
import html  # Nhập thư viện html để xử lý HTML
import re  # Nhập thư viện re để xử lý các biểu thức chính quy (regex)
import ast  # Nhập thư viện ast để phân tích cú pháp
import requests  # Nhập thư viện requests để thực hiện các yêu cầu HTTP
import logging  # Nhập thư viện logging để ghi lại thông tin và lỗii
_logger = logging.getLogger(__name__)  # Tạo logger để ghi lại thông tin

class DatabaseController(http.Controller): # Khai báo controller cho API, kế thừa từ http.Controller
  
    @http.route('/api/load/database', type='json', auth='user', methods=["POST"], csrf=False)
    def load_databases(self, **kw): # API load danh sách database từ server
        if not kw['domain']:  # Kiểm tra nếu không có domain
            return {
                "message": "Domain không hợp lệ", # Trả về lỗi nếu domain không hợp lệ
                "status": "error"
            }
        # Xây dựng Doamain để lấy danh sách database
        url = f"{kw['domain']}/web/database/list"
        try:
            # Gửi yêu cầu POST tới server
            response = requests.post(
                url, json={"jsonrpc": "2.0", "method": "call", "params": {}})

            if response.status_code == 200:  # Kiểm tra nếu phản hồi thành công
                result = response.json().get('result', [])  # Lấy kết quả từ phản hồi
                if result:  # Nếu có kết quả
                    return { 
                        "message": "Thành công", # Trả về thông báo thành công
                        "status": "success",
                        "databases": result  # Trả về danh sách databases
                    }
            return {
                "message": "No databases found, Could you check the domain is correct?",
                "status": "error"
            }
        except Exception as e:
            _logger.info(e) # Ghi lại thông tin lỗi nếu có
            return {
                "message": "Server Error", # Thông báo lỗi nếu xảy ra sự cố trong quá trình xử lý
                "status": "error"
            }

    # Phương thức để thực hiện đăng nhập
    def action_login(self, domain, database, username, password):
        url = f"{domain}/web/session/authenticate"  # Xây dựng URL để đăng nhập
        data = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "db": database,  # Tên database
                "login": username,  # Tên người dùng
                "password": password  # Mật khẩu
            },
            "id": 1
        }
        # Gửi yêu cầu đăng nhập
        session_data = requests.post(url, json=data)  # Gửi yêu cầu POST
        session_data.json()  # Lấy dữ liệu phản hồi
        return session_data  # Trả về dữ liệu phiên làm việc
    
    # API đồng bộ các tags từ server từ xa
    @http.route('/api/compute/sync/tag', type='json', auth='user', methods=["POST"], csrf=False)
    def _sync_remote_tags(self, **kw):
        # Login vào server từ xa
        session_data = self.action_login(kw["domain"], kw["database"], kw["username"], kw["password"])
        auth_response_data = session_data.json() # Lấy dữ liệu phản hồi sau khi đăng nhập
        if not (auth_response_data.get("result") and auth_response_data["result"].get("uid")):
            _logger.error(f"_sync_remote_tags Authentication failed for server")  # Ghi lỗi nếu đăng nhập không thành công
            return False
        session_id = session_data.cookies['session_id'] # Lấy session_id từ cookies
        # Lấy tags từ server từ xa
        headers = {
            'Content-Type': 'application/json',
            'Cookie': f'session_id={session_id}' # Đặt session_id trong header để duy trì phiên làm việc
        }
        data = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                 "model": "blog.tag",  # Mô hình cần lấy (blog.tag)
                "method": "search_read",  # Phương thức để tìm kiếm và đọc các tag
                "args": [[]],  # Tham số tìm kiếm rỗng
                "kwargs": {
                    "fields": ["name", "id"]  # Lấy các trường name và id của tag
                }
            },
            "id": 2
        }
        try:
            # Gửi yêu cầu POST để lấy danh sách tags từ server
            response = requests.post(
                f"{kw['domain']}/web/dataset/call_kw",
                headers=headers,
                json=data
            )
            result = response.json() # Lấy dữ liệu phản hồi
            if result.get('error'):  # Kiểm tra lỗi từ phản hồi
                _logger.error(f"Error fetching tags: {result['error']}")   # Ghi lỗi nếu có lỗi
                return False
            return result.get('result', [])  # Trả về kết quả tags
        except Exception as e:
            _logger.error(f"Error syncing remote tags: {str(e)}") # Ghi lỗi nếu có ngoại lệ xảy ra
            return False

    # API để đồng bộ tag vào server
    @http.route('/api/sync/tag', type='http', auth='user', methods=["POST"], csrf=False)
    def sync_tag(self, **kw):
        # Try cactch để bắt sự kiện nếu tồn tại domain trùng database
        try:
            request.env['server'].browse(int(kw['server_id'])).write({
                'database': kw["database"]}) # Cập nhật database cho server
        except Exception as e:
            return Response(
                json.dumps({
                    "status": "error", # Trả về thông báo lỗi
                    "message": str(e),
                }),
                content_type='application/json;charset=utf-8',
                status=200  # Đảm bảo iframe có thể đọc response
            )
        try:
            # Cập nhật thông tin người dùng và mật khẩu cho server
            request.env['server'].browse(int(kw['server_id'])).write({
                'username': kw["username"],
                'password': kw["password"],
            })
            return Response(
                json.dumps({
                    "status": "success", # Trả về thông báo thành công
                    "message": "Sync completed successfully!",
                }),
                content_type='application/json;charset=utf-8',
                status=200 # Đảm bảo iframe có thể đọc response
            )
        except Exception as e:
            return Response(
                json.dumps({
                    "status": "error", # Trả về thông báo lỗi nếu có ngoại lệ xảy ra
                    "message": str(e),
                }),
                content_type='application/json;charset=utf-8',
                status=200  # Đảm bảo iframe có thể đọc response
            )
