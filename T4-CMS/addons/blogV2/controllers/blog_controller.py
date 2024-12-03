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
from .blog_sync_service import BlogSyncService

_logger = logging.getLogger(__name__)

class BlogController(http.Controller):
    """
    Enhanced Odoo Blog Controller with improved modularity and error handling
    """

    @http.route('/api/create/blog', type='json', auth='user', methods=["POST"], csrf=False)
    def create_blog(self, **kw):
        """
        Endpoint API để tạo hoặc cập nhật bài viết blog
        
        :param kw: Các tham số từ yêu cầu (request)
        :return: Kết quả tạo/cập nhật blog
        """
        _logger.info(f'def create_blog api/create/blog')
        try:
            # Kiểm tra các trường bắt buộc
            required_fields = [
                'blog_folder', 'title', 'content', 'server_id', 
                'server_tag_ids', 'domain', 'database', 
                'session', 'username', 'password', 'db_name_local'
            ]
            
            for field in required_fields:
                if field not in kw:
                    return {"message": f"Thiếu trường bắt buộc: {field}", "status": "error"}

            # Chuẩn bị thông tin đăng nhập và kết nối
            _logger.info('Prepare login_params')
            login_params = {
                'database': kw['database'],
                'username': kw['username'],
                'password': kw['password'],
                'db_name_local': kw['db_name_local'],
                'server_id': kw['server_id']
            }

            _logger.info('Prepare headers')
            headers = {
                'Content-Type': 'application/json',
                'Cookie': f"session_id={kw['session']}"
            }

            # Khởi tạo dịch vụ đồng bộ blog
            _logger.info('Prepare an instance BlogSyncService')
            sync_service = BlogSyncService(login_params, kw['domain'], headers)
            _logger.info(f'create an instantce sync_service successfully')

            # Làm sạch nội dung bài viết
            _logger.info('Call clean_content method')
            cleaned_content = sync_service.clean_content(kw['content'])

            # Tìm hoặc tạo thư mục blog
            _logger.info('blog_folder call_external_api search_read')
            blog_folder = sync_service.call_external_api(
                "blog.blog", 
                "search_read", 
                ["name", "=", kw["blog_folder"]], 
                {"fields": ["id"]}
            )
            #_logger.info(f'blog_folder: {blog_folder}') # log like result

            # nếu không tồn tại blog_folder thì gọi API tạo mới
            if not blog_folder.get("result", []):
                _logger.info('if not blog_folder call_external_api create')
                blog_folder = sync_service.call_external_api(
                    "blog.blog", 
                    "create", 
                    {'name': kw["blog_folder"]}
                )
                blog_folder["result"] = [{"id": blog_folder["result"][0]}]
                _logger.info(f'blog_folder["result"]: {blog_folder["result"]}')

            # Tìm và kiểm tra xem blog post đã tồn tại ở server chưa
            _logger.info('blog_post call_external_api search_read')
            blog_post = sync_service.call_external_api(
                "blog.post", 
                "search_read", 
                ["name", "=", kw['title']], 
                {"fields": ["id"]}
            )

            # tạo mới blog.post mới
            if not blog_post.get("result", []):
                _logger.info('blog_post call_external_api create')
                blog_post = sync_service.call_external_api(
                    "blog.post", 
                    "create", 
                    {
                        'blog_id': blog_folder.get("result")[0].get("id"),  # ID của thư mục blog
                        'name': kw['title'],
                        'content': cleaned_content
                    }
                )
                # log ra folder của blog_post. our_blog có id là 1
                _logger.info(f'blog_folder.get("result")[0].get("id"): {blog_folder.get("result")[0].get("id")}')
                            
                blog_post["result"] = [{"id": blog_post["result"][0]}]
                
                # log ra id của blog_post mới hoặc cũ
                _logger.info(f'blog_post["result"]: {blog_post["result"]}')

            else:
                _logger.info('blog_post call_external_api write')
                sync_service.call_external_api(
                    "blog.post", 
                    "write", 
                    {
                        'blog_id': blog_folder.get("result")[0].get("id"),
                        'name': kw['title'],
                        'content': cleaned_content
                    }, 
                    record_id = blog_post["result"][0]['id'] # truyền tham số record_id để thực hiện cập nhật, vì method là write
                )

                _logger.info(f'record_id to update blog.post: {blog_post["result"][0]["id"]}')

            blog_post_id = blog_post["result"][0]['id']

            # Gắn thẻ (tags) cho bài viết, cập nhật lại tag của bài viết ở server dựa trên blog_post_id
            _logger.info('start update tag_ids in server')
            sync_service.call_external_api(
                "blog.post", 
                "write", 
                {'tag_ids': [(6, 0, kw.get('server_tag_ids'))]}, 
                record_id=blog_post_id
            )
            _logger.info('Update tag in server successfully')

            # Xử lý hình ảnh trong nội dung bài viết trên một luồng riêng
            login_params['server_blog_post_id'] = blog_post_id # 
            thread = threading.Thread(
                target=sync_service._process_images_in_content,
                args=(login_params, cleaned_content, kw['domain'], headers, kw['db_name_local'])
            )
            thread.start()

            return {
                "message": "Tạo bài viết blog thành công",
                "status": "success",
                "data": {"blog_post_server_id": blog_post_id}
            }

        except Exception as e:
            _logger.error(f"Lỗi khi tạo bài viết blog: {str(e)}")
            return {
                "message": f"Lỗi khi tạo bài viết blog: {str(e)}",
                "status": "error"
            }
