import logging
import threading
import base64
import hashlib
import html
import re
import requests

from odoo import http, api, SUPERUSER_ID
from odoo.http import request

_logger = logging.getLogger(__name__)

class BlogController(http.Controller):

    def _authenticate_session(self, domain, database, username, password):
        _logger.info('def _authenticate_session')
        try:
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
            
            session_data = requests.post(url, json=data)
            auth_response_data = session_data.json()
            
            if not (auth_response_data.get("result") and auth_response_data["result"].get("uid")):
                return None
            
            return session_data.cookies.get('session_id')
        
        except Exception as e:
            _logger.error(f"Authentication error: {str(e)}")
            return None

    def _update_local_session(self, db_name_local, server_id, new_session):
        _logger.info('def _update_local_session')
        try:
            registry = api.Registry(db_name_local)
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                env['server'].browse(int(server_id)).write({
                    'session': new_session,
                })
        except Exception as e:
            _logger.error(f"Error updating local session: {str(e)}")

    def _get_image_hash(self, image_data):
        _logger.info('def _get_image_hash')
        return hashlib.md5(image_data).hexdigest()

    def _get_existing_attachment(self, login_params, original_url, domain, headers):
        _logger.info('def _get_existing_attachment')
        try:
            attachment = self.call_external_api(
                login_params,
                "ir.attachment",
                "search_read",
                ["description", "=", original_url],
                domain,
                headers,
                {"fields": ["id", "checksum"]}
            )

            return attachment["result"][0] if attachment.get("result") else None
        except Exception as e:
            _logger.error(f"Error getting existing attachment: {str(e)}")
            return None

    def _upload_image_to_server(self, login_params, image_data, filename, original_url, domain, headers):
        _logger.info('def _upload_image_to_server')
        try:
            existing_attachment = self._get_existing_attachment(
                login_params, original_url, domain, headers)

            new_image_hash = self._get_image_hash(image_data)

            if existing_attachment and existing_attachment.get("checksum") == new_image_hash:
                return f"{domain}/web/image/{existing_attachment['id']}"

            attachment_data = {
                'name': filename,
                'type': 'binary',
                'datas': base64.b64encode(image_data).decode('utf-8'),
                'public': True,
                'res_model': 'ir.ui.view',
                'description': original_url
            }

            if existing_attachment:
                self.call_external_api(
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
                attachment_response = self.call_external_api(
                    login_params,
                    "ir.attachment",
                    "create",
                    attachment_data,
                    domain,
                    headers
                )
                attachment_id = attachment_response["result"][0]

            return f"/web/image/{attachment_id}"
        except Exception as e:
            _logger.error(f"Error uploading image: {str(e)}")
            return None

    def _process_images_in_content(self, login_params, content, domain, headers, db_name_local):
        _logger.info('def _process_image_in_content')
        _logger.info(f"Processing images for blog post id [{login_params['server_blog_post_id']}]")
        #_logger.info(f"Thread _process_images_in_content for blog post id [{login_params['server_blog_post_id']}] is RUNNING")

        if not content:
            return content

        def replace_image(login_params, match, db_name_local):
            _logger.info('def replace_image')
            try:
                # CSS background image handling
                if "url('" in match.group(0):
                    image_url = match.group(1)
                    if _is_local_image(domain, image_url):
                        return match.group(0)
                    return f"url('{replace_image_url(login_params, image_url, db_name_local)}')"

                # img tag handling
                full_tag = match.group(0)
                src_url = match.group(1)

                if _is_local_image(domain, src_url):
                    return full_tag

                new_url = replace_image_url(login_params, src_url, db_name_local)
                if not new_url:
                    return full_tag

                return _update_image_tag(full_tag, new_url)

            except Exception as e:
                _logger.error(f"Error processing image: {str(e)}")
                return match.group(0)

        def replace_image_url(login_params, image_url, db_name_local):
            _logger.info('def replace_image_url')
            try:
                registry = api.Registry(db_name_local)
                with registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})

                    attachment = env['ir.attachment'].search(
                        [('image_src', '=', image_url)], limit=1)
                    if not attachment:
                        return None
                    
                    image_data = base64.b64decode(attachment.datas)
                    filename = attachment.name
                    return self._upload_image_to_server(
                        login_params, image_data, filename, image_url, domain, headers
                    )
            except Exception as e:
                _logger.error(f"Error processing image URL {image_url}: {str(e)}")
                return None

        def _is_local_image(domain, url):
            _logger.info('def _is_local_image')
            return (domain in url or 
                    "/website/static/src" in url or 
                    "/web/image/website" in url)

        def _update_image_tag(tag, new_url):
            _logger.info('def _update_image_tag')
            updated_tag = re.sub(r'src="[^"]*"', f'src="{new_url}"', tag)
            
            if 'data-original-src="' in updated_tag:
                updated_tag = re.sub(
                    r'data-original-src="[^"]*"', f'data-original-src="{new_url}"', updated_tag)
            else:
                updated_tag = updated_tag.replace(
                    f'src="{new_url}"', f'src="{new_url}" data-original-src="{new_url}"')

            return updated_tag

        # Process CSS and img tags
        content = re.sub(r"url\('([^']+)'\)", 
                         lambda m: replace_image(login_params, m, db_name_local), content)
        
        content = re.sub(r'<img\s+[^>]*src="([^"]+)"[^>]*>', 
                         lambda m: replace_image(login_params, m, db_name_local), content)

        # Update blog post content
        self.call_external_api(
            login_params, 
            "blog.post", 
            "write", 
            {'content': content}, 
            domain, 
            headers, 
            {}, 
            int(login_params["server_blog_post_id"])
        )
        
        _logger.info(f"Image processing complete for blog post id [{login_params['server_blog_post_id']}]")

    def _clean_content(self, content):
        _logger.info('def _clean_content')
        if not content:
            return ""
        
        # Unescape HTML entities
        content = html.unescape(content)

        # Replace escaped newlines
        content = content.replace('\\n', '\n')

        # Fix image URLs
        content = re.sub(r"url\(\\+'([^)]+)\\+'\)", r"url('\1')", content)

        # Normalize newlines
        content = re.sub(r'\n\s*\n', '\n', content)

        # Remove excess whitespace
        content = content.strip()

        # Handle escaped quotes
        content = content.replace("\\'", "'")
        
        return content

    def call_external_api(self, login_params, model, method, args, domain, headers, kwargs={}, id=0, retry_count=0, max_retries=1):
        _logger.info('Calling external API....')

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
            response.raise_for_status()
            result = response.json()

            if result.get('error'):
                _logger.error(f"API Error: {result['error']}")
                return {
                    'status': 'error',
                    'message': f"Error: {result['error']}"}
            return result

        except requests.exceptions.HTTPError as httpError:
            error_code = httpError.response.status_code

            if (error_code == 401 or error_code == 404) and (retry_count < max_retries):
                _logger.warning(f"Session expired. Retrying... Attempt {retry_count + 1}/{max_retries}")

                new_session = self._authenticate_session(
                    domain, login_params['database'], login_params['username'], login_params['password']
                    )
                
                if new_session:
                    headers.update({'Cookie': f'session_id={new_session}'})
                    self._update_local_session(
                        login_params['db_name_local'], login_params['server_id'], new_session
                        )

                    return self.call_external_api(
                        login_params, model, method, args, domain, headers, kwargs, id, retry_count + 1, max_retries
                    )

            _logger.error(f'HTTP Error: {httpError}')
            return {
                'status': 'error',
                'message': str(httpError)
            }

        except Exception as e:
            _logger.error(f"API Exception: {str(e)}")
            return {
                'status': 'Exception',
                'message': str(e)
            }

    @http.route('/api/create/blog', type='json', auth='user', methods=["POST"], csrf=False)
    def create_blog(self, **kw):
        _logger.info('API create_blog is called...')
        try:
            # Validate required fields
            required_fields = [
                'blog_folder', 'title', 'content', 'server_id',
                'server_tag_ids', 'domain', 'database', 
                'session', 'username', 'password', 'db_name_local'
            ]
            for field in required_fields:
                if field not in kw:
                    return {
                        "message": f"Missing required field: {field}",
                        "status": "error"
                    }

            cleaned_content = self._clean_content(kw['content'])

            if not kw['session']:
                return {
                    "message": "Login failed, incorrect username or password!",
                    "status": "error"
                }

            headers = {
                'Content-Type': 'application/json',
                'Cookie': f"session_id={kw['session']}"
            }
            login_params = {
                'database': kw['database'],
                'username': kw['username'],
                'password': kw['password'],
                'db_name_local': kw['db_name_local'],
                'server_id': kw['server_id']
            }

            # Process blog folder
            blog_folder = self._process_blog_folder(login_params, kw['blog_folder'], kw['domain'], headers)
            
            # Process blog post
            blog_post = self._process_blog_post(
                login_params, blog_folder, kw['title'], cleaned_content, kw['domain'], headers)

            blog_post_id = blog_post["result"][0]['id']

            # Handle server tags
            try:
                self.call_external_api(
                    login_params, 
                    "blog.post", 
                    "write", 
                    {'tag_ids': [(6, 0, kw.get('server_tag_ids'))]}, 
                    kw['domain'], 
                    headers, 
                    {}, 
                    blog_post_id
                )
            except Exception as e:
                return {
                    "message": f"Error adding server tag {str(e)}",
                    "status": "error"
                }

            # Prepare login parameters for image processing
            login_params.update({'server_blog_post_id': blog_post_id})
            
            # Start a separate thread for image processing
            thread = threading.Thread(
                target=self._process_images_in_content,
                args=(login_params, cleaned_content, kw['domain'], headers, kw['db_name_local'])
            )
            thread.start()

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

    def _process_blog_folder(self, login_params, blog_folder_name, domain, headers):
        blog_folder = self.call_external_api(
            login_params, 
            "blog.blog", 
            "search_read", 
            ["name", "=", blog_folder_name], 
            domain, 
            headers, 
            {"fields": ["id"]}
        )

        # Create blog folder if it doesn't exist
        if blog_folder.get("result", []) == []:
            blog_folder = self.call_external_api(
                login_params, 
                "blog.blog", 
                "create", 
                {'name': blog_folder_name}, 
                domain, 
                headers
            )
            blog_folder["result"] = [{"id": blog_folder["result"][0]}]

        return blog_folder

    def _process_blog_post(self, login_params, blog_folder, title, cleaned_content, domain, headers):
        blog_post = self.call_external_api(
            login_params, 
            "blog.post", 
            "search_read", 
            ["name", "=", title], 
            domain, 
            headers, 
            {"fields": ["id"]}
        )

        if blog_post.get("result", []) == []:
            blog_post = self.call_external_api(
                login_params, 
                "blog.post", 
                "create", 
                {
                    'blog_id': blog_folder.get("result")[0].get("id"),
                    'name': title,
                    'content': cleaned_content
                }, 
                domain, 
                headers
            )
            blog_post["result"] = [{"id": blog_post["result"][0]}]
        else:
            self.call_external_api(
                login_params, 
                "blog.post", 
                "write", 
                {
                    'blog_id': blog_folder.get("result")[0].get("id"),
                    'name': title,
                    'content': cleaned_content
                }, 
                domain, 
                headers, 
                {}, 
                blog_post["result"][0]['id']
            )

        return blog_post