from odoo import http, _,  api, SUPERUSER_ID

from odoo.http import request, Response
import json
import html
import re
import ast
import logging
import requests
import base64
from urllib.parse import urlparse, urljoin
import os
import hashlib

_logger = logging.getLogger(__name__)

class BlogController(http.Controller):

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
        _logger.info('BlogController: action_login')

        url = f"{domain}/web/session/authenticate"
        data = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "db": database,
                "login": username,
                "password": password
            },
            "id": 1
        }
        # Gửi yêu cầu đăng nhập
        session_data = requests.post(url, json=data)  # Gửi yêu cầu POST

        auth_response_data = session_data.json()
        if not (auth_response_data.get("result") and auth_response_data["result"].get("uid")):
            return False

        session_id = session_data.cookies['session_id']
        _logger.info(f'Session_id: {session_id}')
        return session_id

    def _get_image_hash(self, image_data):
        """
        Tính toán giá trị hash của dữ liệu hình ảnh để kiểm tra thay đổi.

        Args:
            image_data: Dữ liệu nhị phân của hình ảnh

        Returns:
            str: Giá trị hash MD5 của hình ảnh
        """
        _logger.info('def _get_image_hash')
        _logger.info(f'image_hash: {hashlib.md5(image_data).hexdigest()}')

        return hashlib.md5(image_data).hexdigest()

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
        _logger.info('def _get_existing_attachment')
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
                _logger.info(f'attachment["result"][0]: {attachment["result"][0]}')
                return attachment["result"][0]
            return None
        except Exception as e:
            _logger.error(f"Error getting existing attachment: {str(e)}")
            return None

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
            _logger.info(existing_attachment)

            # Tính hash mới
            new_image_hash = self._get_image_hash(image_data)
            _logger.info(f'new_image_hash: {new_image_hash}')

            # Kiểm tra nếu ảnh không thay đổi
            if existing_attachment and existing_attachment.get("checksum") == new_image_hash:
                _logger.info(f"{domain}/web/image/{existing_attachment['id']}")
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
            _logger.info(f'attachment_data: {attachment_data}')

            if existing_attachment:
                # Cập nhật attachment cũ
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
            else:
                # Tạo attachment mới
                attachment_response = self.call_external_api(
                    login_params,
                    "ir.attachment",
                    "create",
                    attachment_data,
                    domain,
                    headers
                )
                _logger.info(f'attachment_response: {attachment_response}')

                attachment_id = attachment_response["result"][0]
                _logger.info(f'attachment_id: {attachment_id}')

            return f"/web/image/{attachment_id}"
        except Exception as e:
            _logger.error(f"Error uploading image: {str(e)}")
            return None

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
        if not content:
            return content

        def replace_image(login_params, match, db_name_local):
            """
            Hàm callback thay thế URL hình ảnh.
            Xử lý cả hình ảnh trong CSS và thẻ img.

            Args:
                login_params: Thông tin đăng nhập cho việc thay thế URL.
                match: Đối tượng match được tìm thấy từ biểu thức chính quy.
                db_name_local: Tên database cục bộ.

            Returns:
                str: Chuỗi đã được cập nhật URL hình ảnh.
            """
            _logger.info('def replace_image')
            try:
                # Kiểm tra và xử lý URL hình ảnh trong CSS background
                
                if "url('" in match.group(0):
                    image_url = match.group(1) # Lấy URL hình ảnh từ match
                    _logger.info(f'image_url: {image_url}')

                    # Bỏ qua nếu URL đã hợp lệ (thuộc domain hoặc là đường dẫn tĩnh)
                    if domain in image_url or "/website/static/src" in image_url or "/web/image/website" in image_url:
                        return match.group(0)

                    return f"url('{replace_image_url(login_params, image_url, db_name_local)}')" # Thay thế URL bằng hàm replace_image_url

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
                
                _logger.info(f'updated_tag: {updated_tag}')
                return updated_tag # Trả về thẻ img đã được cập nhật

            except Exception as e:
                _logger.error(f"Error processing image: {str(e)}")

                return match.group(0)  # Trả về thẻ ban đầu nếu có lỗi


        def replace_image_url(login_params, image_url, db_name_local):
            """
            Thay thế URL hình ảnh bằng cách tải và upload lại lên server.
            """
            _logger.info(f'def replace_image_url')

            try:
                # Đăng ký với đối tượng Registry để thao tác với cơ sở dữ liệu db_name_local
                registry = api.Registry(db_name_local)

                # Đảm bảo rằng con trỏ được tự động đóng khi khối lệnh hoàn thành, dù có xảy ra lỗi hay không.
                with registry.cursor() as cr: #Tạo một con trỏ (cursor) để giao tiếp trực tiếp với cơ sở dữ liệu. cr là con trỏ dùng để truy vấn db
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

        _logger.info(f'content: {content}')
        return content

    def _clean_content(self, content):
        """
        Làm sạch và định dạng nội dung blog.

        Args:
            content: Nội dung cần làm sạch

        Returns:
            str: Nội dung đã được làm sạch
        """
        _logger.info('def _clean_content')
        # Kiểm tra nếu nội dung trống hoặc None, trả về chuỗi rỗng
        if not content:
            return ""
        #_logger.info(f'before content: {content}')

        # Giải mã các ký tự HTML entities như &lt;, &gt;, &amp; thành ký tự thông thường
        content = html.unescape(content)
        #_logger.info(f'before content: {content}')
        
        # Thay thế các ký tự xuống dòng escaped (\\n) thành ký tự xuống dòng thực tế (\n)
        content = content.replace('\\n', '\n')
        #_logger.info(f'content.replace: {content}')
        
        # Sửa các URL của hình ảnh bị escaped
        # Ví dụ: url(\'image/path.jpg\') -> url('image/path.jpg')
        content = re.sub(r"url\(\\+'([^)]+)\\+'\)", r"url('\1')", content)
        #_logger.info(f're.sub1: {content}')
        
        # Loại bỏ các dòng trống thừa (nhiều dòng trống liên tiếp) chỉ để lại một dòng trống
        content = re.sub(r'\n\s*\n', '\n', content)
        #_logger.info(f're.sub2: {content}')
        
        # Xóa các khoảng trắng thừa ở đầu và cuối nội dung
        content = content.strip()
        # _logger.info(f'content.strip: {content}')
        
        # Thay thế các ký tự nháy đơn bị escaped (\\') thành nháy đơn thông thường (')
        content = content.replace("\\'", "'")

        # Trả về nội dung đã được làm sạch
        #_logger.info(f'after content: {content}')
        return content


    def call_external_api(self, login_params, model, method, args, domain, headers, kwargs={}, id=0):
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
        _logger.info('def call_external_api')
        data = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": model,
                "method": method,
                "args": [[args]] if method != 'write' else [[id], args],
                "kwargs": kwargs
            },
            "id": 2
        }
        try:
            response = requests.post(
                f"{domain}/web/dataset/call_kw", headers=headers, json=data)
            #_logger.info(f'response: {response}')
            # Kiểm tra HTTP status
            response.raise_for_status()  # Raise exception for 4XX/5XX status
            result = response.json()
            
            _logger.info(f'result: {result}')

            if result.get('error'):
                _logger.error(f"Error fetching tags: {result['error']}")
                return {
                    'status': 'error',
                    'message': f"Error fetching tags: {result['error']}"}
            return result

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                session_id = self.action_login(
                    domain, login_params['database'], login_params['username'], login_params['password'])
                _logger.info(f'session: {session_id}')

                registry = api.Registry(login_params['db_name_local'])
                with registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    env['server'].browse(int(login_params['server_id'])).write({
                        'session': session_id,
                    })

                headers.update({'Cookie': f'session_id={session_id}'})
                response = requests.post(
                    f"{domain}/web/dataset/call_kw", headers=headers, json=data)
                # Kiểm tra HTTP status
                result = response.json()
                _logger.info(f'result: {result}')

                if result.get('error'):
                    _logger.error(f"Error fetching tags: {result['error']}")
                    return {
                        'status': 'error',
                        'message': f"Error fetching tags: {result['error']}"}
                return result
            return {
                'status': 'HTTPError',
                'message': f'HTTP Error: {e.response.status_code}'
            }
        except Exception as e:
            _logger.error(f"Error syncing remote tags: {str(e)}")
            return {
                'status': 'Exception',
                'message': f"Error syncing remote tags: {str(e)}"
            }

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
        _logger.info(f'create_blog API')
        try:
            required_fields = ['blog_folder', 'title', 'content', 'server_id',
                               'server_tag_ids', 'domain', 'database', 'session', 'username', 'password', 'db_name_local']
            for field in required_fields:
                if field not in kw:
                    return {
                        "message": f"Missing required field: {field}",
                        "status": "error"
                    }

            # Clean the content
            cleaned_content = self._clean_content(kw['content'])
            _logger.info(f'cleaned_content: {cleaned_content}')

            if not kw['session']:
                return {
                    "message": "Đăng nhập thất bại, sai username hoặc password!",
                    "status": "error"
                }
            headers = {
                'Content-Type': 'application/json',
                'Cookie': "session_id="+kw['session']
            }
            login_params = {
                'database': kw['database'],
                'username': kw['username'],
                'password': kw['password'],
                'db_name_local': kw['db_name_local'],
                'server_id': kw['server_id']
            }
            _logger.info(f'login_params: {login_params}')

            # Process and upload only modified images
            processed_content = self._process_images_in_content(
                login_params, cleaned_content, kw['domain'], headers, kw['db_name_local'])
            _logger.info(f'processed_content: {processed_content}')

            # Create/find blog folder
            blog_folder = self.call_external_api(login_params, "blog.blog", "search_read", [
                                                 "name", "=", kw["blog_folder"]], kw['domain'], headers, {"fields": ["id"]})
            _logger.info(f'blog_folder: {blog_folder}')

            if blog_folder.get("result", []) == []:
                blog_folder = self.call_external_api(login_params, "blog.blog", "create", {
                    'name': kw["blog_folder"]
                }, kw['domain'], headers)
                blog_folder["result"] = [{"id": blog_folder["result"][0]}]
                _logger.info(f'blog_folder["result"]: {blog_folder["result"]}')

            # Tìm blog_post
            blog_post = self.call_external_api(login_params, "blog.post", "search_read", [
                "name", "=", kw['title']], kw['domain'], headers, {"fields": ["id"]})
            _logger.info(f'blog_post: {blog_post}')

            # Trường hợp tạo blog_post thất bại -> gọi api tạo lại
            if blog_post.get("result", []) == []:
                blog_post = self.call_external_api(login_params, "blog.post", "create", {
                    'blog_id': blog_folder.get("result")[0].get("id"),
                    'name': kw['title'],
                    'content': processed_content
                }, kw['domain'], headers)
                blog_post["result"] = [{"id": blog_post["result"][0]}]
                _logger.info(f'blog_post: {blog_post}')

            # nếu tìm thấy thì cập nhật lại
            else:
                self.call_external_api(login_params, "blog.post", "write", {
                    'blog_id': blog_folder.get("result")[0].get("id"),
                    'name': kw['title'],
                    'content': processed_content
                }, kw['domain'], headers, {}, blog_post["result"][0]['id'])

            blog_post_id = blog_post["result"][0]['id']
            _logger.info(f'blog_post_id: {blog_post_id}')

            # Handle server tags
            try:
                # cập nhật lại tag cho blog đó
                self.call_external_api(login_params, "blog.post", "write", {
                    'tag_ids': [(6, 0, kw.get('server_tag_ids'))]
                }, kw['domain'], headers, {}, blog_post_id)
                _logger.info('Cập nhật tag cho blog thành công!!')
            except Exception as e:
                return {
                    "message": f"Error adding server tag {str(e)}",
                    "status": "error"
                }

            return {
                "message": "Blog post created successfully",
                "status": "success",
                "data": {
                    "blog_post_server_id": blog_post_id
                }
            }

        except Exception as e:
            _logger.error(f"Error creating blog post: {str(e)}")
            return {
                "message": f"Error creating blog post: {str(e)}",
                "status": "error"
            }
