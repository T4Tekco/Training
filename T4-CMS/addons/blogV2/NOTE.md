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



## [MATCH.GROUP](https://stackoverflow.com/questions/2554185/match-groups-in-python)
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
