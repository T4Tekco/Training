# Odoo Blog API Controller

A Python controller for managing blog posts in Odoo, with advanced image handling capabilities.

## Features

- Create and update blog posts
- Automatic image processing and optimization
- Preserve image attributes during processing
- Support for both inline images and CSS background images
- Image deduplication using MD5 hash checking
- Session-based authentication
- Tag management support

## API Usage

### Create/Update Blog Post For Specific domain name

**Endpoint:** `/api/create/blog`  
**Method:** POST  
**Authentication:** User authentication required

**Request Parameters:**
```json
{
    "blog_folder": "Technology",
    "title": "My Blog Post",
    "content": "<p>Blog content with <img src='/path/to/image.jpg' alt='test'></p>",
    "server_tag_ids": [1, 2, 3],
    "domain": "https://your-odoo-domain.com",
    "database": "your_database",
    "username": "your_username",
    "password": "your_password"
}
```

**Response:**
```json
{
    "message": "Blog post created successfully",
    "status": "success",
    "data": {
        "blog_post_server_id": 123
    }
}
```

### Image Processing Features
- Automatic upload of external images to Odoo server
- Image deduplication based on MD5 hash
- Preservation of HTML attributes during image processing
- Support for both `<img>` tags and CSS `url()` images
- Original source URL tracking in attachment descriptions

## Code Structure for 

```
blogV2/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── create_blog.py
└── static/
    └── description/
        └── icon.png
```

## Key Components

### BlogController Class

Main controller class handling blog operations:

1. **Authentication Methods:**
   - `action_login`: Handles user authentication
   - `call_external_api`: Manages API calls to Odoo

2. **Image Processing:**
   - `_get_image_hash`: Generates MD5 hash for images
   - `_get_existing_attachment`: Checks for duplicate images
   - `_upload_image_to_server`: Handles image uploads
   - `_process_images_in_content`: Processes images in blog content

3. **Content Management:**
   - `_clean_content`: Sanitizes and formats blog content
   - `create_blog`: Main method for blog post creation/update

## Image Processing Flow

1. Content is received with image references
2. Each image is processed:
   - Original attributes are preserved
   - Image is downloaded and hashed
   - Duplicate check is performed
   - Image is uploaded if new or modified
   - URLs are updated in content
3. Both src and data-original-src attributes are updated
4. All other HTML attributes are preserved

## Security Considerations

- Session-based authentication required
- CSRF protection enabled
- Secure image processing with validation
- Error logging for debugging
- Input sanitization

## Error Handling

The controller includes comprehensive error handling:
- Authentication failures
- Image processing errors
- API call failures
- Missing required fields
- Tag management errors

## Logging

Logging is implemented using Odoo's logging system:
```python
_logger = logging.getLogger(__name__)
```

Key events logged:
- Authentication attempts
- Image processing results
- API call responses
- Error conditions

## Contributing

## Support

For support and issues, please create an issue in the repository or contact [nhan.dang.dev@gmail.com].




## NOTE:
1. **Session cookie**
    Đây có thể là cookie phiên được sử dụng khi bạn gọi API từ phía client.
    Cookie này thường được gửi kèm trong các yêu cầu HTTP (request) để duy trì phiên làm việc giữa client và server API.
    
2. **Session id**
    Đây là ID phiên được lưu trữ trên server để nhận diện người dùng cụ thể trong phiên làm việc.
    Session_id thường được lưu trong bộ nhớ hoặc cơ sở dữ liệu trên server và liên kết với thông tin người dùng như quyền truy cập, 
    thông tin xác thực, v.v.
3. **Cơ chế tạo ra**
    Cookie phiên API (Session cookie call_api):
    Có thể được tạo riêng cho các yêu cầu API, đặc biệt khi hệ thống sử dụng các dịch vụ khác nhau và yêu cầu các loại token/cookie khác nhau để quản lý truy cập.
    Cookie này có thể được mã hóa hoặc sinh ra dựa trên một thuật toán hash cụ thể.

    Session_id:
    ID này thường được tạo bởi framework hoặc hệ thống quản lý session (như Flask, Django, hoặc Odoo).
    Nó là một chuỗi ký tự duy nhất (unique) được gán cho mỗi người dùng khi bắt đầu phiên làm việc.



## BlogController:
Mục đích
Code này xử lý các thao tác liên quan đến blog trong hệ thống Odoo, tập trung vào các chức năng sau:

Đăng nhập hệ thống qua API.
Quản lý hình ảnh:
Tải lên hoặc cập nhật hình ảnh.
Tính toán hash hình ảnh để kiểm tra sự thay đổi.
Xử lý URL hình ảnh trong nội dung blog.
Các thành phần chính
1. Phương thức action_login
Gửi yêu cầu API để đăng nhập vào hệ thống Odoo.
Trả về session_id nếu đăng nhập thành công.
2. Phương thức _get_image_hash
Tính toán giá trị hash MD5 từ dữ liệu hình ảnh.
Dùng để kiểm tra xem hình ảnh có bị thay đổi hay không.
3. Phương thức _get_existing_attachment
Kiểm tra hình ảnh đã tồn tại trên server Odoo hay chưa.
4. Phương thức _upload_image_to_server
Tải lên hình ảnh mới hoặc cập nhật ảnh cũ dựa trên URL và dữ liệu hình ảnh.
5. Phương thức _process_images_in_content
Phân tích nội dung HTML để tìm và thay thế các URL hình ảnh.
Xử lý cả hình ảnh trong thẻ <img> và thuộc tính CSS (background-image).
6. Phương thức _clean_content
Làm sạch nội dung blog:
Giải mã ký tự HTML (html.unescape).
Thay thế ký tự xuống dòng bị escaped (\\n).
Sửa các URL hình ảnh bị escaped.
Ý nghĩa sử dụng
Tự động hóa quá trình xử lý nội dung blog và quản lý hình ảnh trên nền tảng Odoo.
Hỗ trợ các thao tác:
Đăng nhập.
Tải lên hoặc cập nhật hình ảnh.
Tối ưu nội dung HTML.

