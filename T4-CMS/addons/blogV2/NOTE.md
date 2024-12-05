## [Sự khác nhau giữa HTTP Method `GET` và `POST`:](https://viblo.asia/p/so-sanh-phuong-thuc-get-va-post-jvElaW8YKkw)

- GET: Lấy dữ liệu, dữ liệu gửi đi qua URL, nhanh hơn nhưng kém bảo mật, thích hợp cho truy vấn thông tin.

- POST: Gửi dữ liệu trong body, bảo mật hơn, không giới hạn kích thước, dùng để gửi dữ liệu nhạy cảm hoặc khi thao tác có thể thay đổi dữ liệu trên server.

| Tiêu chí           | GET                                              | POST                                                 |
|--------------------|--------------------------------------------------|------------------------------------------------------|
| Chức năng          | Lấy dữ liệu từ server.                           | Gửi dữ liệu lên server để xử lý (tạo hoặc cập nhật). |
| Dữ liệu gửi đi     | Dữ liệu được gửi trong URL query string.         | Dữ liệu được gửi trong body của request.            |
| Hiển thị dữ liệu   | Dữ liệu hiển thị trong URL.                      | Dữ liệu không hiển thị trong URL.                   |
| Bảo mật            | Kém bảo mật hơn, dữ liệu có thể lưu trong lịch sử trình duyệt. | Bảo mật hơn, dữ liệu ẩn trong body.                |
| Giới hạn dữ liệu   | Giới hạn kích thước (thường < 2048 ký tự).       | Không giới hạn kích thước cụ thể.                   |
| Tốc độ             | Nhanh hơn vì không xử lý body.                   | Chậm hơn do xử lý dữ liệu trong body.               |
| Idempotent         | Idempotent (kết quả không đổi khi gửi nhiều lần).| Không idempotent (kết quả thay đổi nếu gửi lại).    |
| Sử dụng cache      | Có thể cache kết quả.                            | Không cache kết quả.                                |
| Dùng khi nào       | Truy xuất dữ liệu (tìm kiếm, đọc dữ liệu).       | Gửi dữ liệu (đăng nhập, đăng ký, gửi form).         |



## [Sự khác nhau giữa Session và Cookie:](https://topdev.vn/blog/session-la-gi-cookie-la-gi/)

- Session: Lưu trữ trên server, bảo mật hơn, thích hợp cho dữ liệu tạm thời và nhạy cảm.

- Cookie: Lưu trữ trên client, hữu ích cho dữ liệu cần giữ lại sau khi người dùng rời khỏi trang, nhưng kém bảo mật hơn.

| Tiêu chí            | Session                                      | Cookie                                                      |
|---------------------|----------------------------------------------|-------------------------------------------------------------|
| Lưu trữ dữ liệu     | Trên server.                                 | Trên trình duyệt (client).                                  |
| Phạm vi lưu trữ      | Mỗi người dùng có một session riêng biệt, lưu trữ trên server. | Cookie được lưu trữ trên máy người dùng và được gửi lên server. |
| Dung lượng          | Không giới hạn rõ ràng nhưng bị giới hạn bởi bộ nhớ server. | Giới hạn khoảng 4KB cho mỗi cookie.                         |
| Thời gian tồn tại    | Kết thúc khi phiên làm việc của người dùng kết thúc hoặc bị xóa thủ công. | Có thể đặt thời gian hết hạn cụ thể, tồn tại lâu hơn.        |
| Bảo mật             | Bảo mật hơn, không thể bị sửa đổi bởi người dùng. | Ít bảo mật hơn, có thể bị chỉnh sửa nếu không mã hóa.       |
| Hiệu suất           | Tăng tải cho server vì dữ liệu được lưu trên server. | Không ảnh hưởng đến server vì dữ liệu lưu trên trình duyệt. |
| Dùng khi nào        | Khi cần lưu dữ liệu nhạy cảm hoặc dữ liệu chỉ cần tồn tại trong phiên làm việc. | Khi cần lưu dữ liệu không nhạy cảm như tuỳ chọn giao diện hoặc thông tin đăng nhập. |


**MATCH.GROUP**
- match.group() là gì?
- match: Là đối tượng Match được tạo ra từ việc sử dụng hàm re.sub hoặc re.search khi áp dụng biểu thức chính quy (regex) trên chuỗi.
- match.group(): Lấy dữ liệu tương ứng với từng nhóm được tìm thấy dựa trên biểu thức chính quy.

- Cụ thể:
- group(0): Trả về toàn bộ chuỗi khớp với regex. Tìm các đoạn trùn khớp với regex trong trường hợp này là r"url\(''\)"
- group(1): Trả về giá trị của nhóm đầu tiên (được xác định bằng cặp dấu ngoặc đơn () trong regex). Là đoạn bên trong của regex 
- được trùng với group(0) và bên trong dấu ngoặc đơn ().

### 1) Xử lý ảnh trong CSS
` Regex:
``` r"url\('([^']+)'\) ```
- Giải thích:
- url('([^']+)'):
-    url('...') tìm các đoạn CSS chứa URL hình ảnh trong dấu ngoặc đơn.
-    ([^']+): Nhóm 1 — Bắt tất cả các ký tự bên trong dấu ' (trừ dấu ').

- Ví dụ: 
``` background-image: url('https://example.com/image.jpg'); ```

- group(0): url('https://example.com/image.jpg') (toàn bộ khớp).
- group(1): https://example.com/image.jpg (URL ảnh).


### 2) Xử lý thẻ <img> trong HTML
Regex:
``` r'<img\s+[^>]*src="([^"]+)"[^>]*>' ```

-Giải thích:
``` <img\s+[^>]*src="([^"]+)"[^>]*>: ```

- ```<img ...> ```: Tìm thẻ <img>.
- ```src="([^"]+)" ```: Nhóm 1 — Bắt URL hình ảnh trong thuộc tính src.
- Ví dụ, nếu chuỗi là:
``` <img src="https://example.com/image.jpg" alt="Example"> ```

- group(0): <img src="https://example.com/image.jpg" alt="Example"> (toàn bộ thẻ).
- group(1): https://example.com/image.jpg (URL trong src).

### Ý nghĩa của full_tag và src_url
``` full_tag = match.group(0) ```
- Lưu toàn bộ thẻ HTML hoặc đoạn CSS chứa URL hình ảnh. Ví dụ:
- <img src="https://example.com/image.jpg" alt="Example"> 
- url('https://example.com/image.jpg')

``` src_url = match.group(1) ```

- Lưu URL của hình ảnh được tìm thấy. Ví dụ:
- https://example.com/image.jpg.

## re.sub()
```
content = re.sub(
    r"url\('([^']+)'\)", 
    lambda m: replace_image(login_params, m, db_name_local), 
    content
)
```

# Phân tích các thành phần:
# 1. re.sub():

- re.sub() là một hàm trong module re (biểu thức chính quy) của Python, dùng để thay thế tất cả các chuỗi con khớp với một biểu thức chính quy trong chuỗi gốc bằng một giá trị thay thế.
- Cấu trúc của hàm re.sub() là:

```re.sub(pattern, repl, string)```

- pattern: Biểu thức chính quy dùng để tìm các chuỗi con cần thay thế.
- repl: Giá trị thay thế, có thể là một chuỗi hoặc một hàm (như ở đây là một hàm lambda).
- string: Chuỗi cần thực hiện thay thế.

# 2. r"url\('([^']+)'\)":

- Đây là biểu thức chính quy được sử dụng để tìm kiếm các chuỗi có dạng url('...').
- Giải thích biểu thức chính quy:
    - url\(': Tìm chuỗi "url('" (có dấu nháy đơn) trong chuỗi văn bản.
    - ([^']+): Đây là nhóm (group) số 1, tìm mọi ký tự ngoại trừ dấu nháy đơn ('), ít nhất một ký tự. Phần này sẽ khớp với URL bên trong dấu nháy đơn.
    - '\): Tìm chuỗi đóng của ')'.
- Biểu thức này sẽ khớp với các chuỗi có dạng url('https://example.com') hoặc bất kỳ URL nào ở dạng url('...').

# 3. lambda m: replace_image(login_params, m, db_name_local):

- Đây là một hàm lambda (hàm vô danh) sẽ được gọi mỗi khi một chuỗi con khớp với biểu thức chính quy được tìm thấy.
- Hàm này nhận đối số m, là đối tượng Match mà re.sub() tạo ra khi tìm thấy một chuỗi con khớp.
- Hàm lambda sẽ gọi hàm replace_image(login_params, m, db_name_local) và trả về giá trị của nó, cái này sẽ thay thế chuỗi con khớp trong content.

# 4. replace_image(login_params, m, db_name_local):

- Đây là một hàm (có thể do bạn tự định nghĩa) sẽ xử lý chuỗi con được tìm thấy và trả về giá trị thay thế.
- Hàm này nhận ba tham số:
    - login_params: Có thể là thông tin đăng nhập hoặc tham số cấu hình cần thiết để thay thế URL.
    - m: Đối tượng Match chứa thông tin về chuỗi con khớp (ví dụ, URL trong url('...')).
    - db_name_local: Có thể là tên cơ sở dữ liệu hoặc một tham số khác dùng trong hàm replace_image để thay đổi URL hoặc thực hiện thay thế.

**LAMBDA FUNCTION**
# What is Lambda

- lambda là một cú pháp đặc biệt trong Python để tạo ra một hàm ẩn danh (không có tên). Hàm lambda có thể nhận vào bất kỳ số lượng tham số và trả về một giá trị duy nhất.

- Cú pháp:
    ``` lambda arguments: expression ```

- arguments: Danh sách các tham số mà hàm lambda nhận vào (có thể có một hoặc nhiều tham số, hoặc không có tham số nào).
- expression: Biểu thức mà hàm sẽ tính toán và trả về. Chú ý rằng expression phải trả về một giá trị duy nhất.

- Trong Odoo, sử dụng ```lambda``` thường được dùng để viết các hàm ngắn gọn mà không cần khai báo một hàm đầy đủ. 

# Ví dụ cơ bản:
1. Hàm lambda không tham số:
```python
greet = lambda: "Hello, world!"
print(greet())  # Output: Hello, world! 
```
2. Hàm lambda với một tham số:
```python
square = lambda x: x * x
print(square(5))  # Output: 25
```
3. Hàm lambda với nhiều tham số:
```python
add = lambda x, y: x + y
print(add(3, 4))  # Output: 7
```

### Giải thích lambda m: replace_image(login_params, m, db_name_local):
- lambda: Đây là một cách khai báo một hàm ẩn danh (không tên), giúp bạn tạo ra các hàm ngắn mà không cần phải dùng def.
- m: Đây là đối số đầu vào của hàm lambda. Trong trường hợp này, nó sẽ nhận vào đối tượng match mà được truyền từ phương thức re.sub() (hoặc một phương thức tương tự).
- replace_image(login_params, m, db_name_local): Đây là phần thực thi của hàm lambda. Nó sẽ gọi hàm replace_image với ba đối số:
- login_params: Thông tin đăng nhập người dùng.
- m: Đối số match được truyền từ biểu thức re.sub() (là kết quả của việc khớp với một biểu thức chính quy).
- db_name_local: Tên cơ sở dữ liệu mà bạn đang làm việc với.


# FUNCTION IN PROJECT NOTE
# 1. _clean_content(self, content)
- xử lý và làm sạch nội dung văn bản đầu vào, chủ yếu là để chuẩn hóa các ký tự đặc biệt, định dạng HTML, và sửa chữa các lỗi phổ biến trong chuỗi. 

### 1.1.Giải mã các thực thể HTML
```bash
content = html.unescape(content)
```
- Chuyển đổi các thực thể HTML (như &amp;, &lt;, &gt;) thành các ký tự tương ứng (&, <, >).
- Ví dụ: "&amp;" sẽ được chuyển thành "&".

### 1.2. Thay thế ký tự xuống dòng thoát (\n) bằng ký tự xuống dòng thực sự
```bash
content = content.replace('\\n', '\n')
```
- Chuyển đổi chuỗi thoát \n thành ký tự xuống dòng thực (newline).
- Ví dụ: "Hello\\nWorld" sẽ trở thành "Hello\nWorld".

### 1.3. Sửa các URL của ảnh
```bash
content = re.sub(r"url\(\\+'([^)]+)\\+'\)", r"url('\1')", content)
```
- Dùng Regular Expression (Regex) để sửa các URL ảnh bị thoát ký tự không đúng.
- Ví dụ:
```"url(\\+'https://example.com/image.png\\+')".```
- Sẽ được chuyển thành ```"url('https://example.com/image.png')".```

### 1.4. Chuẩn hóa các dòng trống
```bash
content = re.sub(r'\n\s*\n', '\n', content)
```
- Loại bỏ các dòng trống liên tiếp (dòng chứa toàn khoảng trắng hoặc nhiều dòng mới liên tiếp).
```bash
Line 1


Line 2
```

Sẽ thành:

```bash
Line 1
Line 2
```

### 1.5. Loại bỏ khoảng trắng thừa
```python
content = content.strip()
```

- Xóa khoảng trắng đầu và cuối chuỗi.
- Ví dụ: " Hello World " sẽ trở thành "Hello World".

### 1.6. Xử lý các ký tự thoát dấu nháy đơn (\')
```python
content = content.replace("\\'", "'")
```
- Chuyển đổi các dấu nháy đơn thoát (\') thành dấu nháy đơn thông thường (').
- Ví dụ: ```"It\\'s fine"``` sẽ trở thành ```"It's fine"```

