
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

- group(0): <imgs src="https://example.com/image.jpg" alt="Example"> (toàn bộ thẻ).
- group(1): https://example.com/image.jpg (URL trong src).

### Ý nghĩa của full_tag và src_url
``` full_tag = match.group(0) ```
- Lưu toàn bộ thẻ HTML hoặc đoạn CSS chứa URL hình ảnh. Ví dụ:
- <img src="https://example.com/image.jpg" alt="Example"> 
- url('https://example.com/image.jpg')

``` src_url = match.group(1) ```

- Lưu URL của hình ảnh được tìm thấy. Ví dụ:
- https://example.com/image.jpg.

**LAMBDA FUNCTION**
# lambda m: replace_image(login_params, m, db_name_local)
