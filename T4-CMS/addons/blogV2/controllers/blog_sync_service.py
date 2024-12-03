from odoo import http, api, SUPERUSER_ID
from odoo.http import request
import logging
import requests
import base64
import hashlib
import threading
import html
import re
import json

_logger = logging.getLogger(__name__)

class BlogSyncService:
    """
    Service class to handle blog synchronization operations
    Separates concerns and makes code more modular
    """
    def __init__(self, login_params, domain, headers):
        """
        Initialize sync service with login and connection parameters
        
        :param login_params: Dictionary containing login credentials and database info
        :param domain: Server domain
        :param headers: Request headers
        """
        _logger.info('def __init__() BlogSyncService')
        self.login_params = login_params
        self.domain = domain
        self.headers = headers
        self.db_name_local = login_params.get('db_name_local')

    def authenticate_session(self):
        """
        Authenticate user session and handle re-authentication if needed
        
        :return: Authenticated session or None
        """
        _logger.info('def authenticate_session')

        try:
            url = f"{self.domain}/web/session/authenticate"
            _logger.info(f'url: {url}')
            data = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "db": self.login_params['database'],
                    "login": self.login_params['username'],
                    "password": self.login_params['password']
                },
                "id": 1
            } 
            
            session_data = requests.post(url, json=data)
            auth_response_data = session_data.json()
            _logger.info(f'auth_response_data: {auth_response_data}')
            
            if not (auth_response_data.get("result") and auth_response_data["result"].get("uid")):
                return None
            
            _logger.info(f"new session/ session_data.cookies.get('session_id'): {session_data.cookies.get('session_id')}")
            return session_data.cookies.get('session_id')
        
        except Exception as e:
            _logger.error(f"Authentication error: {str(e)}")
            return None
        
    def _get_image_hash(self, image_data):
        """
        Tính toán giá trị hash của dữ liệu hình ảnh để kiểm tra thay đổi.

        Args:
            image_data: Dữ liệu nhị phân của hình ảnh

        Returns:
            str: Giá trị hash MD5 của hình ảnh
        """
        return hashlib.md5(image_data).hexdigest()

    def call_external_api(self, model, method, args, kwargs=None, record_id=None, retry_count=0, max_retries=1):
        _logger.info('Calling external API...')
        kwargs = kwargs or {}
        
        # Prepare payload
        data = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": model,
                "method": method,
                "args": [[args]] if method != 'write' else [[record_id], args],
                "kwargs": kwargs
            },
            "id": 2
        }

        try:
            # Make the API call
            response = requests.post(
                f"{self.domain}/web/dataset/call_kw",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()  # Raise HTTPError for bad responses
            result = response.json()

            if result.get('error'):
                _logger.error(f"API Error: {result['error']}")
                return {'status': 'error', 'message': str(result['error'])}

            _logger.info(f'Call API successed with result: {result}')
            return result

        except requests.exceptions.HTTPError as e:
            if (e.response.status_code == 401
                and e.response.status_code == 404
                and retry_count < max_retries):
                _logger.warning(f"Session expired. Retrying... Attempt {retry_count + 1}/{max_retries}")
                
                # Re-authenticate session and retry
                new_session = self.authenticate_session()
                if new_session:
                    self.headers.update({'Cookie': f'session_id={new_session}'})
                    self._update_local_session(new_session)
                    return self.call_external_api(model, method, args, kwargs, record_id, retry_count + 1, max_retries)
            
            _logger.error(f"HTTP Error: {e}")
            return {'status': 'error', 'message': str(e)}

        except Exception as e:
            _logger.error(f"Unexpected error: {str(e)}")
            return {'status': 'error', 'message': str(e)}


    def _update_local_session(self, new_session):
        """
        Update session in local database
        
        :param new_session: New session ID
        """
        _logger.info(f'def _update_local_session')
        try:
            registry = api.Registry(self.db_name_local)
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                env['server'].browse(int(self.login_params['server_id'])).write({
                    'session': new_session,
                })
                _logger.info(f'update local new_session: {new_session}')
        except Exception as e:
            _logger.error(f"Error updating local session: {str(e)}")

    def clean_content(self, content):
        """
        Clean and format blog content
        
        :param content: Raw content to clean
        :return: Cleaned content
        """
        _logger.info(f'def clean_content')
        if not content:
            return ""

        # Unescape HTML entities
        content = html.unescape(content)
        
        # Replace escaped newlines
        content = content.replace('\\n', '\n')
        
        # Fix escaped image URLs
        content = re.sub(r"url\(\\+'([^)]+)\\+'\)", r"url('\1')", content)
        
        # Remove excess blank lines
        content = re.sub(r'\n\s*\n', '\n', content)
        
        # Strip whitespace
        content = content.strip()
        
        # Replace escaped single quotes
        content = content.replace("\\'", "'")

        _logger.info('cleaned content')
        return content
    
    def _process_images_in_content(self, login_params, content, domain, headers, db_name_local):
        """
        Xử lý tất cả hình ảnh trong nội dung, giữ nguyên các thuộc tính.

        Args:
            content: Nội dung HTML cần xử lý
            domain: Domain của server Odoo  
            headers: Headers cho request API

        Returns:
            str: Nội dung đã xử lý với các URL hình ảnh mới
        """
        _logger.info('def _process_images_in_content')
        _logger.info(f"Thread _process_images_in_content for blog post id [{login_params['server_blog_post_id']}] is RUNNING")

        if not content:
            return content

        def replace_image(login_params, match, db_name_local):
            """
            Hàm callback thay thế URL hình ảnh.
            Xử lý cả hình ảnh trong CSS và thẻ img.
            """
            _logger.info('def replace_image')
            try:
                # Xử lý ảnh trong CSS background
                # Kiểm tra và xử lý URL hình ảnh trong CSS background
                if "url('" in match.group(0):
                    image_url = match.group(1) # Lấy URL hình ảnh từ match
                    _logger.info(f'image_url: {image_url}')

                    # Bỏ qua nếu URL đã hợp lệ (thuộc domain hoặc là đường dẫn tĩnh)
                    if domain in image_url or "/website/static/src" in image_url or "/web/image/website" in image_url:
                        return match.group(0)
                    return f"url('{replace_image_url(login_params, image_url, db_name_local)}')"

                # Xử lý URL hình ảnh trong thẻ <img>        
                # Lấy toàn bộ thẻ img và giá trị src URL từ match
                full_tag = match.group(0)
                src_url = match.group(1)
                _logger.info(f'full_tag: {match.group(0)}')
                _logger.info(f'src_url: {match.group(1)}')

                # Bỏ qua nếu URL đã hợp lệ (thuộc domain hoặc là đường dẫn tĩnh)
                if domain in src_url or "/website/static/src" in src_url or "/web/image/website" in src_url:
                    _logger.info(f'full_tag: {match.group(0)}')
                    return full_tag

                # Gọi hàm replace_image_url để tạo URL mới
                new_url = replace_image_url(login_params, src_url, db_name_local)

                # Nếu không tạo được URL mới, trả về thẻ gốc
                if not new_url:
                    return full_tag

                # Cập nhật cả thuộc tính `src` và `data-original-src` trong thẻ img
                # Cập nhật giá trị thuộc tính `src`
                updated_tag = re.sub(
                    r'src="[^"]*"', f'src="{new_url}"', full_tag)
                
                # Nếu có thuộc tính `data-original-src`, cập nhật giá trị của nó
                if 'data-original-src="' in updated_tag:
                    updated_tag = re.sub(
                        r'data-original-src="[^"]*"', f'data-original-src="{new_url}"', updated_tag)
                else:
                    # Nếu không có, thêm mới thuộc tính `data-original-src` với giá trị giống `src`
                    updated_tag = updated_tag.replace(
                        f'src="{new_url}"', f'src="{new_url}" data-original-src="{new_url}"')

                return updated_tag # Trả về thẻ img đã được cập nhật

            except Exception as e:
                _logger.error(f"Error processing image: {str(e)}")

                return match.group(0)   # Trả về thẻ ban đầu nếu có lỗi

        def replace_image_url(login_params, image_url, db_name_local):
            """
            Thay thế URL hình ảnh bằng cách tải và upload lại lên server.
            """
            _logger.info(f'def replace_image_url')
            try:
                # Đăng ký với đối tượng Registry để thao tác với cơ sở dữ liệu db_name_local
                registry = api.Registry(db_name_local)

                # Đảm bảo rằng con trỏ được tự động đóng khi khối lệnh hoàn thành, dù có xảy ra lỗi hay không.
                with registry.cursor() as cr:  #Tạo một con trỏ (cursor) để giao tiếp trực tiếp với cơ sở dữ liệu. cr là con trỏ dùng để truy vấn db
                    env = api.Environment(cr, SUPERUSER_ID, {})

                    attachment = env['ir.attachment'].search(
                        [('image_src', '=', image_url)], limit=1)
                    _logger.info(f'attachment: {attachment}')

                    if not attachment:
                        return None
                    image_data = base64.b64decode(attachment.datas)
                    filename = attachment.name
                    new_url = self._upload_image_to_server(login_params,
                                                           image_data,
                                                           filename,
                                                           image_url,
                                                           domain,
                                                           headers
                                                           )
                    return new_url
                
            except Exception as e:
                _logger.error(
                    f"Error processing image URL {image_url}: {str(e)}")
                return None

        # Xử lý ảnh trong CSS
        content = re.sub(
            r"url\('([^']+)'\)", lambda m: replace_image(login_params, m, db_name_local), content)

        # Xử lý thẻ img
        content = re.sub(
            r'<img\s+[^>]*src="([^"]+)"[^>]*>', lambda m: replace_image(login_params, m, db_name_local), content)

        self.call_external_api("blog.post", "write", {
            'content': content
        }, domain, headers, {}, int(login_params["server_blog_post_id"]))
        _logger.info(f"Thread _process_images_in_content for blog post id [{login_params['server_blog_post_id']}] is DONE")



    def _upload_image_to_server(self, login_params, image_data, filename, original_url, domain, headers):
        """
        Upload hình ảnh lên server Odoo và lưu trữ tham chiếu URL gốc.

        Args:
            image_data: Dữ liệu nhị phân của hình ảnh
            filename: Tên file
            original_url: URL gốc của hình ảnh
            domain: Domain của server Odoo
            headers: Headers cho request API

        Returns:
            str: URL của hình ảnh đã upload
        """
        _logger.info('def _upload_image_to_server')
        try:
            # Kiểm tra attachment tồn tại
            existing_attachment = self._get_existing_attachment(
                login_params, original_url, domain, headers)
            _logger.info(f'existing_attachment: {existing_attachment}')

            # Tính hash mới
            new_image_hash = self._get_image_hash(image_data)
            _logger.info(f'new_image_hash : {new_image_hash}')

            # Kiểm tra nếu ảnh không thay đổi
            if existing_attachment and existing_attachment.get("checksum") == new_image_hash:
                return f"{domain}/web/image/{existing_attachment['id']}"

            # Chuẩn bị dữ liệu attachment
            attachment_data = {
                'name': filename,
                'type': 'binary',
                'datas': base64.b64encode(image_data).decode('utf-8'),
                'public': True,
                'res_model': 'ir.ui.view',
                'description': original_url
            }

            if existing_attachment:
                # Cập nhật attachment cũ
                _logger.info('Cập nhật attachment')
                attachment_response = self.call_external_api(
                    login_params,
                    "ir.attachment",
                    "write",
                    attachment_data,
                    domain,
                    headers,
                    {},
                    existing_attachment['id']
                )
                attachment_id = existing_attachment['id']
                _logger.info(f'Cập nhật attachment thành công: {attachment_id}')
            else:
                # Tạo attachment mới
                _logger.info('Tạo mới attachment')
                attachment_response = self.call_external_api(
                    login_params,
                    "ir.attachment",
                    "create",
                    attachment_data,
                    domain,
                    headers
                )
                attachment_id = attachment_response["result"][0]
                _logger.info(f'Tạo mới attachment thành công: {attachment_id}')

            _logger.info(f'f"/web/image/{attachment_id}"')
            return f"/web/image/{attachment_id}"
        except Exception as e:
            _logger.error(f"Error uploading image: {str(e)}")
            return None
        

    def _get_existing_attachment(self, login_params, original_url, domain, headers):
        """
        Lấy thông tin attachment đã tồn tại dựa trên URL gốc.

        Args:
            original_url: URL gốc của hình ảnh
            domain: Domain của server Odoo
            headers: Headers cho request API

        Returns:
            dict: Thông tin attachment nếu tồn tại, None nếu không
        """
        _logger.info(f'def _get_existing_attachment')
        try:
            # Tìm attachment dựa trên URL gốc trong field description
            attachment = self.call_external_api(login_params,
                                                "ir.attachment",
                                                "search_read",
                                                ["description", "=", original_url],
                                                domain,
                                                headers,
                                                {"fields": ["id", "checksum"]}
                                                )

            if attachment.get("result"):
                _logger.info(f'Ton tai attachment: {attachment["result"][0]}')
                return attachment["result"][0]
            return None
        except Exception as e:
            _logger.error(f"Error getting existing attachment: {str(e)}")
            return None
