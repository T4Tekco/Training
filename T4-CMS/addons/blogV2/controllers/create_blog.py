import ast
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
        
    def _upload_attachment_to_server(self, login_params, attachment_data, filename, domain, headers):
        _logger.info('def _upload_image_to_server')
        try:

            attachment_data_prepare = {
                'name': filename,
                'type': 'binary',
                'datas': base64.b64encode(attachment_data).decode('utf-8'),
                'public': True,
                'res_model': 'ir.ui.view',
            }

            attachment_response = self.call_external_api(
                login_params,
                "ir.attachment",
                "create",
                attachment_data_prepare,
                domain,
                headers
            )
            _logger.info(f'Attachment_response: {attachment_response}')

            return attachment_response

        except Exception as e:
            _logger.error(f"Error uploading/creating new attachment with error: {str(e)}")
            return None
          
    def _get_attachment_url_path(self, login_params, attachment_response, domain, headers):
        _logger.info('def _get_attachment_url_path')
        try:
            # Check if the response is valid and contains a result
            if not attachment_response or 'result' not in attachment_response:
                _logger.error("Invalid attachment response")
                return None

            # Get the attachment ID from the response
            attachment_server_id = attachment_response.get('result')[0]
            _logger.info(f'attachment_server_id: {attachment_server_id}')
            
            if not attachment_server_id:
                _logger.error("No attachment ID found in response")
                return None

            # Read attachment details
            attachment_detail = self.call_external_api(                 
                login_params,                 
                "ir.attachment",                 
                "read",                 
                attachment_server_id,                  
                domain,                 
                headers             
            )        
            #_logger.info(f'attachment_detail: {attachment_detail}') 

            if not attachment_detail or 'result' not in attachment_detail:
                _logger.error(f"Failed to get attachment details for {attachment_server_id}")
                return None

            attachment_details = attachment_detail.get('result', [{}])[0]
            
            attachment_url_path = attachment_details.get('image_src')
            
            if not attachment_url_path:
                _logger.warning("Could not find attachment URL path")
                return None
            
            _logger.info(f'attachment_url_path: {attachment_url_path}')
            return attachment_url_path
            
        except Exception as e:             
            _logger.error(f'Error when get attachment_url_path: {str(e)}')             
            return None

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
                #"args": [args] if method != "write" else [[id], args],
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

    def check_server_attachment_by_id(self, login_params, server_attachment_id, server_id, domain, headers):
        _logger.info('def check_server_attachment_by_id')
        try:
            attachment_server_mapping = request.env['attachment.mapping'].search([
                ('server_attachment_id', '=', server_attachment_id),
                ('server_id', '=', server_id)
            ])
            _logger.info(f'attachment_server_mapping: {attachment_server_mapping}')
            
            if not attachment_server_mapping:
                _logger.info(f"Don't have attachment in mapping with attachment_id {server_attachment_id} and server_id {server_id}")

            server_attachment = self.call_external_api(
                login_params,
                "ir.attachment",
                "search_read",
                ["id", "=", server_attachment_id],
                domain,
                headers,
                {"fields": ["image_src"]}
            )

            if not server_attachment:
                _logger.info(f"Can't get any server_attachment with attachment_id: {server_attachment_id}")

            _logger.info(f'Server_attachment: {server_attachment}')
            return None
        except Exception as e:
            _logger.info(f'Error when get attachment on server with attachment_id: {server_attachment_id} and error: {str(e)}')
            return None

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
    
    def get_all_attachment_mapping(self):
        _logger.info('def get_all_attachment_mapping')
        try:
            attachment_mapping = request.env['attachment.mapping'].search([])
            _logger.info(f'attachment_mapping: {attachment_mapping}')

            if not attachment_mapping:
                _logger.info("Can't get attachment_mapping")

            return attachment_mapping
        except Exception as e:
            _logger.info(f'Error when get attachment mapping: {str(e)}')
    
    def upload_attachment(self, upload_attachment):
        _logger.info(f'def upload_attachment')
        
        try:
            attachment = upload_attachment.local_attachment_id
            server = upload_attachment.server_id

            _logger.info(f'attachment: {attachment}, server: {server}')

            login_params={
                    'database': server.database,
                    'username': server.username,
                    'password': server.password,
                    'db_name_local': request.env.cr.dbname,
                    'server_id': server.id
            }
            _logger.info(f'login_params: {login_params}')
            attachment_data = base64.b64decode(attachment.datas)
            _logger.info('attachment_data')

            headers = {
                'Content-Type': 'application/json',
                'Cookie': f"session_id={server.session}"
            }

            attachment_response = self._upload_attachment_to_server(
                login_params,
                attachment_data=attachment_data,
                filename=attachment.name,
                domain=server.domain,
                headers=headers
            )
            
            _logger.info(f"attachment_response['result']: {attachment_response['result']}")

            if not attachment_response:
                _logger.warning(f"Upload attachment failed!")

            server_attachment_path = self._get_attachment_url_path(login_params,
                                                                                attachment_response, 
                                                                                server.domain, 
                                                                                headers)
           
            # Create mapping record
            new_attachment_mapping = request.env['attachment.mapping'].create({
                'server_attachment_id': attachment_response['result'],
                'server_attachment_path': server_attachment_path,
                'local_attachment_id': attachment.id,
                'server_id': server.id
            })

            _logger.info(f'Create ATTACHMENT.MAPPING success: {new_attachment_mapping}')
            #records_to_unlink.append(record)
            
            upload_attachment.unlink()
            _logger.info(f'Unlink success upload_attachment')

        except Exception as e:
            _logger.error(f"Error uploading attachment {upload_attachment.local_attachment_id.name}: {str(e)}")

    def _process_image_urls(self, login_params, post_id, server_id, domain, headers):
        _logger.info('def _process_image_urls')
        try:
            attachment_posts = request.env['ir.attachment'].search([
                ('res_model', '=', 'blog.post'),
                ('res_id', '=', post_id)
            ])
            _logger.info(f'Total attachments found: {len(attachment_posts)}')

            for attachment_post in attachment_posts:
                _logger.info(f'Processing attachment: {attachment_post.name}')
                
                # Kiểm tra mapping hiện tại 
                existing_attachment_mappings = request.env['attachment.mapping'].search([
                    ('local_attachment_id', '=', attachment_post.id),
                    ('server_id', '=', server_id)
                ])
                _logger.info(f'existing_attachment_mappings: {existing_attachment_mappings}')

                # Luôn tạo attachment upload để đảm bảo upload
                new_upload_attachment = request.env['attachment.upload'].create({
                    'local_attachment_id': attachment_post.id,
                    'server_id': server_id
                })

                # Nếu chưa có mapping, thực hiện upload
                if not existing_attachment_mappings:
                    _logger.info('No existing attachment mappings, uploading...')
                    try:
                        self.upload_attachment(new_upload_attachment)
                    except Exception as e:
                        _logger.error(f'Upload failed for {attachment_post.name}: {e}')
                        continue

                # Cập nhật URL cho tất cả các attachment
                for attachment_mapping in existing_attachment_mappings:
                    new_url = attachment_mapping.server_attachment_path
                    _logger.info(f'New URL for {attachment_post.name}: {new_url}')

                    server_attachment_id_list = ast.literal_eval(attachment_mapping.server_attachment_id)
                    server_att_id = server_attachment_id_list[0]
                    server_mapping_id = attachment_mapping.server_id['id']

                    # check attachment is exist on server
                    self.check_server_attachment_by_id(login_params, server_att_id,
                                                        server_mapping_id, domain, headers)

                    if new_url:
                        # Kiểm tra URL và cập nhật
                        try:
                            attachment_post.write({
                                'image_src': new_url
                            })
                            _logger.info(f'Successfully updated image_src for {attachment_post.name}')
                        except Exception as e:
                            _logger.error(f'Failed to update image_src: {e}')
                    else:
                        _logger.warning(f'No valid server attachment path for {attachment_post.name}')

        except Exception as e:
            _logger.error(f'Error processing image URLs: {e}')

    @http.route('/api/create/blog', type='json', auth='user', methods=["POST"], csrf=False)
    def create_blog(self, **kw):
        _logger.info('API create_blog is called...')
        try:                        

            # Validate required fields
            required_fields = [
                'blog_folder', 'title', 'content',  'post_id', 'server_id',
                'server_tag_ids', 'domain', 'database', 
                'session', 'username', 'password', 'db_name_local'
            ]

            for field in required_fields:
                if field not in kw:
                    return {
                        "message": f"Missing required field: {field}",
                        "status": "error"
                    }

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

            cleaned_content = self._clean_content(kw['content'])

            # xu ly anh
            self._process_image_urls(login_params, kw['post_id'], kw['server_id'], kw['domain'], headers)

            # Process blog folder
            blog_folder = self._process_blog_folder(login_params, kw['blog_folder'], kw['domain'], headers)
            _logger.info(f'blog_folder: {blog_folder}')

            # Process blog post
            blog_post = self._process_blog_post(
                login_params, blog_folder, kw['title'], cleaned_content, kw['domain'], headers)
            _logger.info(f'blog_post: {blog_post}')

            blog_post_id = blog_post["result"][0]['id']

            # Handle server tags 
            try:
                _logger.info('handle server_tag')
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
            login_params.update({'blog_post_id': blog_post_id})

            _logger.info('SUCCESS TRANSFER BLOG')

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
