def _process_image_urls(self, post_id, server_id):
    _logger.info('def _process_image_urls')
    try:
        # Lấy bài đăng blog
        blog_post = request.env['blog.post'].browse(post_id)
        
        # Tìm tất cả attachment của bài đăng
        attachment_posts = request.env['ir.attachment'].search([
            ('res_model', '=', 'blog.post'),
            ('res_id', '=', post_id)
        ])
        _logger.info(f'Total attachments found: {len(attachment_posts)}')

        # Lưu trữ nội dung gốc của bài đăng
        original_content = blog_post.content

        for attachment_post in attachment_posts:
            _logger.info(f'Processing attachment: {attachment_post.name}')
            
            # Kiểm tra mapping hiện tại 
            existing_attachment_mappings = request.env['attachment.mapping'].search([
                ('local_attachment_id', '=', attachment_post.id),
                ('server_id', '=', server_id)
            ])

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
                    existing_attachment_mappings = request.env['attachment.mapping'].search([
                        ('local_attachment_id', '=', attachment_post.id),
                        ('server_id', '=', server_id)
                    ])
                except Exception as e:
                    _logger.error(f'Upload failed for {attachment_post.name}: {e}')
                    continue

            # Cập nhật URL cho tất cả các attachment
            for attachment_mapping in existing_attachment_mappings:
                new_url = attachment_mapping.server_attachment_path
                _logger.info(f'New URL for {attachment_post.name}: {new_url}')

                if new_url:
                    # Thay thế URL cũ bằng URL mới trong nội dung
                    if attachment_post.local_url:
                        original_content = original_content.replace(
                            attachment_post.local_url, 
                            new_url
                        )
                    
                    # Cập nhật image_src của attachment
                    try:
                        attachment_post.write({
                            'image_src': new_url
                        })
                        _logger.info(f'Successfully updated image_src for {attachment_post.name}')
                    except Exception as e:
                        _logger.error(f'Failed to update image_src: {e}')
                else:
                    _logger.warning(f'No valid server attachment path for {attachment_post.name}')

        # Cập nhật lại nội dung bài đăng với URLs mới
        blog_post.write({
            'content': original_content
        })

    except Exception as e:
        _logger.error(f'Error processing image URLs: {e}')