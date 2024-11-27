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


