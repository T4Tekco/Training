from odoo import http, _,  api, SUPERUSER_ID  # Import các module cần thiết trong Odoo
from odoo.http import request, Response
import json  # Thư viện để xử lý JSON
import html  # Thư viện để xử lý HTML
import re  # Thư viện cho biểu thức chính quy (regex)
import ast  # Thư viện để xử lý cây cú pháp (abstract syntax tree)
import logging  # Thư viện để ghi log
import requests  # Thư viện để gửi HTTP requests
import base64  # Thư viện để mã hóa và giải mã base64
from urllib.parse import urlparse, urljoin  # Thư viện xử lý URL
import os  # Thư viện làm việc với hệ thống tệp
import hashlib  # Thư viện để tính toán hàm băm (hash)
_logger = logging.getLogger(__name__) # Khởi tạo logger để ghi lại thông tin

class BlogController(http.Controller): # Định nghĩa một controller cho blog
    """
    Controller xử lý các thao tác liên quan đến blog trong Odoo.
    Bao gồm các chức năng tạo/cập nhật bài viết và xử lý hình ảnh.
    """
    def action_login(self, domain, database, username, password):
        """
        Thực hiện đăng nhập vào hệ thống Odoo thông qua API.
        Args:
            domain: Domain của server Odoo
            database: Tên database
            username: Tên đăng nhập
            password: Mật khẩu
        Returns:
            session_data: Dữ liệu phiên đăng nhập
        """
        url = f"{domain}/web/session/authenticate" # Địa chỉ URL để đăng nhập
        data = { # Dữ liệu gửi đi cho API
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "db": database,  # Tên database
                "login": username,  # Tên đăng nhập
                "password": password  # Mật khẩu
            },
            "id": 1
        }
        session_data = requests.post(url, json=data) # Gửi request đăng nhập
        session_data.json() # Chuyển kết quả thành định dạng JSON
        return session_data # Trả về dữ liệu phiên đăng nhập

    def _get_image_hash(self, image_data):
        """
        Tính toán giá trị hash của dữ liệu hình ảnh để kiểm tra thay đổi.
        Args:
            image_data: Dữ liệu nhị phân của hình ảnh
        Returns:
            str: Giá trị hash MD5 của hình ảnh
        """
        return hashlib.md5(image_data).hexdigest() # Tính hash MD5 của hình ảnh

    def _get_existing_attachment(self, original_url, domain, headers): # Phương thức lấy attachment đã tồn tại từ server
        """
        Lấy thông tin attachment đã tồn tại dựa trên URL gốc.
        Args:
            original_url: URL gốc của hình ảnh
            domain: Domain của server Odoo
            headers: Headers cho request API
        Returns:
            dict: Thông tin attachment nếu tồn tại, None nếu không
        """
        try:
            # Tìm attachment dựa trên URL gốc trong field description
            attachment = self.call_external_api(
                "ir.attachment",  # Model là 'ir.attachment'
                "search_read",  # Phương thức 'search_read' để tìm kiếm các attachment
                ["description", "=", original_url],  # Điều kiện tìm kiếm: description = original_url
                domain,  # Domain của server Odoo
                headers,  # Headers cho yêu cầu API
                {"fields": ["id", "checksum"]}  # Chỉ lấy các trường 'id' và 'checksum'
            )
            if attachment.get("result"):  # Kiểm tra xem kết quả có tồn tại không
                return attachment["result"][0]  # Trả về attachment nếu tìm thấy
            return None  # Trả về None nếu không tìm thấy attachment
        except Exception as e:
            _logger.error(f"Error getting existing attachment: {str(e)}")  # Ghi lại lỗi nếu có
            return None  # Trả về None nếu có lỗi

    def _upload_image_to_server(self, image_data, filename, original_url, domain, headers):
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
        try:
            # Kiểm tra attachment tồn tại
            existing_attachment = self._get_existing_attachment(
                original_url, domain, headers)
            _logger.info(existing_attachment)  # Ghi log thông tin của attachment
            # Tính hash mới
            new_image_hash = self._get_image_hash(image_data)  # Tính toán giá trị hash mới của ảnh
            # Kiểm tra nếu ảnh không thay đổi
            if existing_attachment and existing_attachment.get("checksum") == new_image_hash:
                return f"{domain}/web/image/{existing_attachment['id']}" # Trả về URL của ảnh nếu không thay đổi
            # Chuẩn bị dữ liệu attachment
            attachment_data = {
                'name': filename,  # Tên của file
                'type': 'binary',  # Loại dữ liệu là nhị phân
                'datas': base64.b64encode(image_data).decode('utf-8'),  # Dữ liệu ảnh đã mã hóa base64
                'public': True,  # Đặt thuộc tính là công khai
                'res_model': 'ir.ui.view',  # Mô hình đính kèm là 'ir.ui.view'
                'description': original_url  # Lưu trữ URL gốc trong phần mô tả
            }
            if existing_attachment:
                # Cập nhật attachment cũ
                attachment_response = self.call_external_api(
                    "ir.attachment",  # Gọi API 'ir.attachment'
                    "write",  # Phương thức 'write' để cập nhật
                    attachment_data,  # Dữ liệu cần cập nhật
                    domain,  # Domain của server Odoo
                    headers,  # Headers của yêu cầu API
                    {},  # Không có tham số bổ sung
                    existing_attachment['id']  # ID của attachment cũ
                )
                attachment_id = existing_attachment['id'] # Lấy ID của attachment cũ
            else: # Nếu chưa có, tạo mới
                # Tạo attachment mới
                attachment_response = self.call_external_api(
                     "ir.attachment",  # Gọi API 'ir.attachment'
                    "create",  # Phương thức 'create' để tạo attachment mới
                    attachment_data,  # Dữ liệu tạo mới attachment
                    domain,  # Domain của server Odoo
                    headers  # Headers của yêu cầu API
                )
                attachment_id = attachment_response["result"][0]  # Lấy ID của attachment mới
            return f"/web/image/{attachment_id}"
        except Exception as e:
            _logger.error(f"Error uploading image: {str(e)}") # Ghi log nếu có lỗi
            return None

    def _process_images_in_content(self, content, domain, headers, db_name_local):
        """
        Xử lý tất cả hình ảnh trong nội dung, giữ nguyên các thuộc tính.
        Args:
            content: Nội dung HTML cần xử lý
            domain: Domain của server Odoo  
            headers: Headers cho request API
        Returns:
            str: Nội dung đã xử lý với các URL hình ảnh mới
        """
        if not content: # Nếu không có nội dung, trả về luôn
            return content 
        
        # đảm bảo rằng tất cả URL hình ảnh đều được thay thế bằng các URL hợp lệ thông qua việc gọi hàm replace_image_url.
        def replace_image(match, db_name_local):  # Hàm callback thay thế URL hình ảnh
            """
            Hàm callback thay thế URL hình ảnh.
            Xử lý cả hình ảnh trong CSS và thẻ img.
            """
            try:
                # Phát hiện URL hình ảnh trong CSS.
                if "url('" in match.group(0):# Kiểm tra ảnh trong CSS
                    image_url = match.group(1)  # Lấy URL ảnh
                    if domain in image_url or "/website/static/src" in image_url or "/web/image/website" in image_url:
                        return match.group(0) # Giữ nguyên lại URL nếu hợp lệ
                    return f"url('{replace_image_url(image_url, db_name_local)}')"  # Thay thế URL ảnh nếu không hợp lệ

                # Xử lý thẻ img
                full_tag = match.group(0)
                src_url = match.group(1)

                if domain in src_url or "/website/static/src" in src_url or "/web/image/website" in src_url:
                    return full_tag   # Nếu URL hợp lệ thì không thay đổi

                new_url = replace_image_url(src_url, db_name_local) # Thay thế URL
                if not new_url:
                    return full_tag # Nếu không có URL mới, trả về thẻ img cũ

                # Cập nhật cả src và data-original-src
                updated_tag = re.sub(
                    r'src="[^"]*"', f'src="{new_url}"', full_tag)
                if 'data-original-src="' in updated_tag:
                    updated_tag = re.sub(
                        r'data-original-src="[^"]*"', f'data-original-src="{new_url}"', updated_tag)
                else:
                    updated_tag = updated_tag.replace(
                        f'src="{new_url}"', f'src="{new_url}" data-original-src="{new_url}"')
                return updated_tag
            except Exception as e:
                _logger.error(f"Error processing image: {str(e)}")
                return match.group(0)

        def replace_image_url(image_url, db_name_local):
            """
            Thay thế URL hình ảnh bằng cách tải và upload lại lên server.
            """
            try:
                # Lấy registry cho database local, cho phép truy cập mô hình Odoo
                registry = api.Registry(db_name_local)
                with registry.cursor() as cr:  # Mở một cursor để thực thi truy vấn
                    # Tạo môi trường Odoo với quyền SUPERUSER_ID
                    env = api.Environment(cr, SUPERUSER_ID, {})

                    # Tìm kiếm attachment có URL hình ảnh trùng với image_url
                    attachment = env['ir.attachment'].search(
                        [('image_src', '=', image_url)], limit=1)
                    if not attachment:  # Nếu không tìm thấy attachment, trả về None
                        return None

                    # Giải mã dữ liệu hình ảnh và lấy tên file
                    image_data = base64.b64decode(attachment.datas)
                    filename = attachment.name

                    # Upload lại hình ảnh lên server và lấy URL mới
                    new_url = self._upload_image_to_server(image_data, filename, image_url, domain, headers)
                    return new_url  # Trả về URL mới
            except Exception as e:
                # Ghi log lỗi và trả về None
                _logger.error(f"Error processing image URL {image_url}: {str(e)}")
                return None

        # Xử lý hình ảnh trong CSS
        content = re.sub(
            r"url\('([^']+)'\)",  # Regex để tìm URL hình ảnh trong CSS
            lambda m: replace_image(m, db_name_local),  # Callback thay thế URL
            content
        )

        # Xử lý hình ảnh trong thẻ <img>
        content = re.sub(
            r'<img\s+[^>]*src="([^"]+)"[^>]*>',  # Regex để tìm thẻ <img> và URL từ src
            lambda m: replace_image(m, db_name_local),  # Callback thay thế URL
            content
        )

        # Trả về nội dung sau khi thay thế URL hình ảnh
        return content


    def _clean_content(self, content):
        """
        Làm sạch và định dạng nội dung blog.
        Args:
            content: Nội dung cần làm sạch
        Returns:
            str: Nội dung đã được làm sạch
        """
        if not content:
            return ""

        content = html.unescape(content)# Giải mã HTML entities
        content = content.replace('\\n', '\n')# Thay thế escaped newlines
        content = re.sub(r"url\(\\+'([^)]+)\\+'\)", r"url('\1')", content)# Sửa URL hình ảnh
        content = re.sub(r'\n\s*\n', '\n', content)# Chuẩn hóa newlines
        content = content.strip()# Xóa khoảng trắng thừa
        content = content.replace("\\'", "'")# Xử lý escaped quotes
        return content

    def call_external_api(self, model, method, args, domain, headers, kwargs={}, id=0):
        """
        Gọi API external của Odoo.
        Args:
            model: Tên model Odoo
            method: Tên phương thức cần gọi
            args: Tham số cho phương thức
            domain: Domain của server
            headers: Headers cho request
            kwargs: Các tham số bổ sung
            id: ID của record (cho phương thức write)
        Returns:
            dict: Kết quả từ API
        """
        # Tạo một dictionary chứa thông tin yêu cầu API theo chuẩn JSON-RPC
        data = {
        "jsonrpc": "2.0",  # Phiên bản của JSON-RPC
        "method": "call",  # Phương thức gọi API
        "params": {  # Thông số gửi đi
            "model": model,  # Model Odoo cần tương tác
            "method": method,  # Phương thức trong model cần gọi
            "args": [[args]] if method != 'write' else [[id], args],  # Tham số (args) cho phương thức, với write có ID record đi kèm
            "kwargs": kwargs  # Các tham số bổ sung nếu có
        },
        "id": 2  # ID của yêu cầu, có thể dùng để theo dõi (thường là số bất kỳ)
        }
        response = requests.post(f"{domain}/web/dataset/call_kw", headers=headers, json=data) # Gửi yêu cầu API với phương thức POST tới endpoint của Odoo. # URL API với domain của Odoo, Headers chứa thông tin về session, Dữ liệu JSON gửi đi
        return response.json() # Trả về kết quả phản hồi dưới dạng JSON

    @http.route('/api/create/blog', type='json', auth='user', methods=["POST"], csrf=False)
    def create_blog(self, **kw):
        """
        API endpoint để tạo hoặc cập nhật bài viết blog.
        Args:
            kw: Các tham số từ request
                - blog_folder: Tên thư mục blog
                - title: Tiêu đề bài viết
                - content: Nội dung bài viết
                - server_tag_ids: IDs của các tag
                - domain: Domain server
                - database: Tên database
                - username: Tên đăng nhập
                - password: Mật khẩu
        Returns:
            dict: Kết quả tạo/cập nhật blog
        """
        try:
            # Danh sách các trường bắt buộc phải có trong request
            required_fields = ['blog_folder', 'title', 'content','server_tag_ids', 'domain', 'database', 'username', 'password','db_name_local']
            for field in required_fields:
                # Kiểm tra nếu thiếu trường nào thì trả về lỗi
                if field not in kw:
                    return {"message": f"Missing required field: {field}",
                            "status": "error"}
            # Làm sạch nội dung bài viết
            cleaned_content = self._clean_content(kw['content'])
            # Xử lý đăng nhập vào hệ thống Odoo để lấy session
            session_data = self.action_login(
                kw['domain'], kw['database'], kw['username'], kw['password'])
            auth_response_data = session_data.json()

            # Kiểm tra thông tin đăng nhập, nếu sai thì trả về thông báo lỗi
            if not (auth_response_data.get("result") and auth_response_data["result"]["uid"]):
                return {
                    "message": "Đăng nhập thất bại, sai username hoặc password!",
                    "status": "error"
                }
            # Lấy session ID từ cookies để sử dụng trong các yêu cầu sau
            session_id = session_data.cookies['session_id']
            headers = {
                'Content-Type': 'application/json', # Định dạng dữ liệu gửi đi là JSON
                'Cookie': f'session_id={session_id}'  # Cookie chứa session ID
            }
            # Xử lý và upload lại các hình ảnh đã thay đổi trong nội dung bài viết
            processed_content = self._process_images_in_content(
                cleaned_content, kw['domain'], headers, kw['db_name_local'])
            _logger.info(processed_content) # Ghi log lại nội dung đã xử lý

            # Tìm kiếm thư mục blog có tên trùng với kw['blog_folder']
            blog_folder = self.call_external_api("blog.blog", "search_read", [
                                                 "name", "=", kw["blog_folder"]], kw['domain'], headers, {"fields": ["id"]})
           
            if blog_folder.get("result", []) == []:
                # Nếu thư mục blog không tồn tại, tạo mới
                blog_folder = self.call_external_api("blog.blog", "create", {
                    'name': kw["blog_folder"]
                }, kw['domain'], headers)
                blog_folder["result"] = [{"id": blog_folder["result"][0]}]

            # Tìm kiếm bài viết blog có tiêu đề trùng với kw['title']
            blog_post = self.call_external_api("blog.post", "search_read", [
                "name", "=", kw['title']], kw['domain'], headers, {"fields": ["id"]})
            if blog_post.get("result", []) == []:
                # Nếu bài viết không tồn tại, tạo mới
                blog_post = self.call_external_api("blog.post", "create", {
                    'blog_id': blog_folder.get("result")[0].get("id"),
                    'name': kw['title'],
                    'content': processed_content
                }, kw['domain'], headers)
                blog_post["result"] = [{"id": blog_post["result"][0]}]
            else:
                 # Nếu bài viết đã tồn tại, cập nhật nội dung bài viết
                self.call_external_api("blog.post", "write", {
                    'blog_id': blog_folder.get("result")[0].get("id"), # Lấy ID của bài viết đã tạo hoặc cập nhật
                    'name': kw['title'],
                    'content': processed_content
                }, kw['domain'], headers, {}, blog_post["result"][0]['id'])

            blog_post_id = blog_post["result"][0]['id']
            # Xử lý các tag của bài viết
            try:
                # Cập nhật các tag cho bài viết
                self.call_external_api("blog.post", "write", {
                    'tag_ids': [(6, 0, kw.get('server_tag_ids'))] # Sử dụng tuple (6, 0, ids) để gán nhiều tag
                }, kw['domain'], headers, {}, blog_post_id)
            except Exception as e:
                # Nếu có lỗi khi thêm tag thì trả về lỗi
                return {
                    "message": f"Error adding server tag {str(e)}",
                    "status": "error"
                }
            # Trả về kết quả thành công
            return {
                "message": "Blog post created successfully",
                "status": "success",
                "data": {
                    "blog_post_server_id": blog_post_id
                }
            }
        except Exception as e:
            _logger.error(f"Error creating blog post: {str(e)}") # Ghi lại lỗi vào log
            return {
                "message": f"Error creating blog post: {str(e)}",
                "status": "error"
            }  # Trả về kết quả lỗi khi có ngoại lệ
