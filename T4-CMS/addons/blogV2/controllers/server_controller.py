import logging
import requests
import json
from odoo import http
from odoo.http import request, Response

# Khởi tạo logger để ghi lại thông tin log
_logger = logging.getLogger(__name__)

class ServerController(http.Controller):
    def _prepare_login_payload(self, database, username, password):
        """Chuẩn bị payload đăng nhập"""
        # Trả về payload cho yêu cầu đăng nhập với các tham số như database, username, password
        return {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "db": database,
                "login": username,
                "password": password
            },
            "id": 1
        }

    def _authenticate_remote_session(self, domain, database, username, password):
        """Xác thực phiên làm việc từ xa"""
        # Xây dựng URL endpoint cho xác thực và chuẩn bị payload
        url = f"{domain}/web/session/authenticate"
        payload = self._prepare_login_payload(database, username, password)

        try:
            # Gửi yêu cầu POST để xác thực và lấy phản hồi
            session_response = requests.post(url, json=payload)
            auth_response_data = session_response.json()

            # Kiểm tra phản hồi xác thực và lấy session ID nếu thành công
            if not (auth_response_data.get("result") and auth_response_data["result"].get("uid")):
                _logger.error("Authentication failed")
                return None

            _logger.info(f"session_response.cookies.get('session_id'): {session_response.cookies.get('session_id')}")
            return session_response.cookies.get('session_id')

        except Exception as e:
            # Ghi lại lỗi nếu xảy ra vấn đề trong quá trình xác thực
            _logger.error(f"Authentication error: {str(e)}")
            return None

    def _prepare_api_headers(self, session_id):
        """Chuẩn bị headers cho API request"""
        # Headers chứa thông tin session ID cho xác thực
        return {
            'Content-Type': 'application/json',
            'Cookie': f"session_id={session_id}"
        }

    def _prepare_api_payload(self, model, method, args=None, kwargs=None):
        """Chuẩn bị payload cho API request"""
        # Payload chứa thông tin model, phương thức và các tham số cho API
        return {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": model,
                "method": method,
                "args": args or [],
                "kwargs": kwargs or {}
            },
            "id": 2
        }

    def _make_remote_api_call(self, domain, headers, data):
        """Thực hiện gọi API từ xa"""
        try:
            # Gửi yêu cầu POST đến API với headers và payload đã chuẩn bị
            response = requests.post(
                f"{domain}/web/dataset/call_kw",
                headers=headers,
                json=data
            )
            response.raise_for_status()  # Kiểm tra trạng thái HTTP
            result = response.json()

            # Xử lý lỗi nếu có trong kết quả API
            if result.get('error'):
                _logger.error(f"API Error: {result['error']}")
                return {'status': 'error', 'message': str(result['error'])}

            return result

        except requests.exceptions.HTTPError as e:
            # Xử lý các lỗi HTTP và trả về thông báo phù hợp
            error_status = {
                404: 'Session expired or not found',
                403: 'Forbidden access',
                401: 'Unauthorized'
            }.get(e.response.status_code, 'Unknown HTTP error')
            
            return {
                'status': 'error',
                'message': f'{error_status}: {e.response.status_code}'
            }

        except Exception as e:
            # Ghi lại lỗi và trả về thông báo lỗi chung
            _logger.error(f"Remote API call error: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/compute/sync/tag', type='json', auth='user', methods=["POST"], csrf=False)
    def sync_remote_tags(self, **params):
        """Đồng bộ tags từ server từ xa"""
        if not params.get('session'):
            # Kiểm tra session, nếu không có thì trả về False
            return False

        headers = self._prepare_api_headers(params['session'])
        payload = self._prepare_api_payload(
            model="blog.tag", 
            method="search_read", 
            kwargs={"fields": ["name", "id"]}
        )

        response = self._make_remote_api_call(params['domain'], headers, payload)

        # Nếu session hết hạn, thử đăng nhập lại
        if response.get('status') == 'error' and 'session expired' in response.get('message', '').lower():
            new_session = self._authenticate_remote_session(
                params["domain"], 
                params["database"], 
                params["username"], 
                params["password"]
            )
            
            if new_session:
                headers = self._prepare_api_headers(new_session)
                response = self._make_remote_api_call(params['domain'], headers, payload)
                response['session'] = new_session  # Cập nhật session mới vào kết quả

        return response

    @http.route('/api/sync/tag', type='http', auth='user', methods=["POST"], csrf=False)
    def sync_server_info(self, **params):
        """Đồng bộ thông tin server"""
        try:
            session_id = self._authenticate_remote_session(
                params["domain"], 
                params["database"], 
                params["username"], 
                params["password"]
            )

            if not session_id:
                # Trả về lỗi nếu không thể xác thực session
                return Response(
                    json.dumps({
                        "status": "error",
                        "message": "Invalid username or password",
                    }),
                    content_type='application/json;charset=utf-8',
                    status=400
                )

            # Cập nhật thông tin server trong cơ sở dữ liệu Odoo
            request.env['server'].browse(int(params['server_id'])).write({
                'username': params["username"],
                'session': session_id,
                'database': params["database"],
                'password': params["password"],
            })

            return Response(
                json.dumps({
                    "status": "success",
                    "message": "Sync completed successfully!",
                }),
                content_type='application/json;charset=utf-8',
                status=200
            )

        except Exception as e:
            # Trả về lỗi và chi tiết lỗi nếu có vấn đề trong quá trình đồng bộ
            return Response(
                json.dumps({
                    "status": "error",
                    "message": str(e),
                }),
                content_type='application/json;charset=utf-8',
                status=200
            )

    @http.route('/api/load/database', type='json', auth='user', methods=["POST"], csrf=False)
    def load_databases(self, **params):
        """Tải danh sách database"""
        if not params.get('domain'):
            # Kiểm tra domain, nếu không có thì trả về lỗi
            return {
                "message": "Invalid Domain",
                "status": "error"
            }

        url = f"{params['domain']}/web/database/list"

        try:
            # Gửi yêu cầu tải danh sách database từ server từ xa
            response = requests.post(
                url, 
                json={"jsonrpc": "2.0", "method": "call", "params": {}}
            )

            if response.status_code == 200:
                databases = response.json().get('result', [])
                return {
                    "message": "Success" if databases else "No databases found",
                    "status": "success" if databases else "error",
                    "databases": databases
                }

            return {
                "message": "Could not retrieve databases. Check domain.",
                "status": "error"
            }

        except Exception as e:
            # Ghi lại lỗi nếu xảy ra vấn đề và trả về thông báo lỗi
            _logger.error(f"Database loading error: {str(e)}")
            return {
                "message": "Server Error",
                "status": "error"
            }
