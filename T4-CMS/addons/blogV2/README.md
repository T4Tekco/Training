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



## BlogController:

# Mục đích

Dự án này xử lý các thao tác liên quan đến **blog trong hệ thống Odoo**, tập trung vào các chức năng chính như:

- **Đăng nhập hệ thống qua API**.
- **Quản lý hình ảnh**:
  - Tải lên hoặc cập nhật hình ảnh.
  - Tính toán hash hình ảnh để kiểm tra sự thay đổi.
  - Xử lý URL hình ảnh trong nội dung blog.

# Các thành phần chính

### 1. **Phương thức `action_login`**
- Gửi yêu cầu API để đăng nhập vào hệ thống Odoo.
- Trả về `session_id` nếu đăng nhập thành công.

### 2. **Phương thức `_get_image_hash`**
- Tính toán giá trị hash MD5 từ dữ liệu hình ảnh.
- Dùng để kiểm tra xem hình ảnh có bị thay đổi hay không.

### 3. **Phương thức `_get_existing_attachment`**
- Kiểm tra hình ảnh đã tồn tại trên server Odoo hay chưa.

### 4. **Phương thức `_upload_image_to_server`**
- Tải lên hình ảnh mới hoặc cập nhật ảnh cũ dựa trên URL và dữ liệu hình ảnh.

### 5. **Phương thức `_process_images_in_content`**
- Phân tích nội dung HTML để tìm và thay thế các URL hình ảnh.
- Xử lý cả hình ảnh trong thẻ `<img>` và thuộc tính CSS (`background-image`).

### 6. **Phương thức `_clean_content`**
- Làm sạch nội dung blog:
  - Giải mã ký tự HTML (`html.unescape`).
  - Thay thế ký tự xuống dòng bị escaped (`\\n`).
  - Sửa các URL hình ảnh bị escaped.

## Ý nghĩa sử dụng

- **Tự động hóa** quá trình xử lý nội dung blog và quản lý hình ảnh trên nền tảng Odoo.
- Hỗ trợ các thao tác như:
  - Đăng nhập.
  - Tải lên hoặc cập nhật hình ảnh.
  - Tối ưu hóa nội dung HTML.


## DatabaseController:
# 1. Chức năng chính

### a. Đăng nhập vào server Odoo (`action_login`)
- Gửi yêu cầu POST tới `/web/session/authenticate` với thông tin đăng nhập.
- Kiểm tra phản hồi để lấy `session_id` nếu đăng nhập thành công.

### b. Gọi API Odoo (`callAPI`)
- Gửi yêu cầu POST tới API `/web/dataset/call_kw` để thực hiện các phương thức của Odoo như `search_read`.
- Xử lý các lỗi HTTP và các trường hợp lỗi khác, như endpoint không tồn tại hoặc lỗi không xác định.

### c. Đồng bộ hóa các tags từ server Odoo (`_sync_remote_tags`)
- Gửi yêu cầu tới server để lấy danh sách tags (`blog.tag`).
- Nếu session hết hạn, tự động đăng nhập lại và thử lại yêu cầu.

### d. Cập nhật thông tin server (`write_server_info`)
- Cập nhật thông tin server như `username`, `session`, `database`, và `password` vào cơ sở dữ liệu Odoo.
- Trả về thông báo phản hồi thành công hoặc lỗi.

### e. Tải danh sách database từ server Odoo (`load_databases`)
- Gửi yêu cầu tới endpoint `/web/database/list` để lấy danh sách cơ sở dữ liệu.
- Xử lý lỗi nếu domain không hợp lệ hoặc không có cơ sở dữ liệu nào được tìm thấy.

---

## 2. Các điểm cần lưu ý

- **Xử lý lỗi rõ ràng**: Hầu hết các hàm đều xử lý lỗi tốt và trả về thông báo chi tiết trong trường hợp lỗi xảy ra.
- **Ghi nhật ký (logging)**: Sử dụng `_logger` để ghi lại thông tin quan trọng, giúp ích trong việc gỡ lỗi.
- **Xác thực session**: Hỗ trợ xác thực lại nếu `session_id` hết hạn.

---

## 3. Gợi ý cải tiến

### a. **Tăng cường bảo mật**
- **Ẩn thông tin nhạy cảm trong log**: Tránh log trực tiếp `username`, `password` hoặc `session_id` để bảo mật.
- **Mã hóa dữ liệu nhạy cảm**: Bảo vệ thông tin như mật khẩu khi lưu trữ hoặc truyền tải.

### b. **Cải thiện khả năng tái sử dụng**
- **Tách biệt các hàm chung**: Chuyển `callAPI` và `action_login` vào một lớp tiện ích để tái sử dụng.
- **Thêm cấu hình linh hoạt**: Để dễ dàng thay đổi URL endpoint hoặc cấu trúc API.

### c. **Xử lý lỗi chi tiết hơn**
- **Phân biệt rõ lỗi giữa `HTTPError`, `ConnectionError`, và lỗi logic từ API** (như dữ liệu không hợp lệ).





## Contributing

## Support

For support and issues, please create an issue in the repository or contact [nhan.dang.dev@gmail.com].



