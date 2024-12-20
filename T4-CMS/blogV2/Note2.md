
# Model ir.cron
Model ir.cron trong Odoo được sử dụng để định nghĩa và quản lý các tác vụ theo lịch (Scheduled Actions). Nó cho phép bạn tự động hóa các tác vụ nhất định trong hệ thống bằng cách lên lịch để chúng chạy theo khoảng thời gian xác định. Đây là một tính năng mạnh mẽ để giảm công việc thủ công và đảm bảo các quy trình được thực hiện đều đặn.

### Các chức năng chính của ir.cron:
1. Tự động hóa tác vụ:
Cho phép chạy các hàm hoặc quy trình trong module mà không cần sự can thiệp của người dùng.

2. Định nghĩa lịch trình:
Bạn có thể thiết lập thời gian bắt đầu, tần suất lặp lại (hàng ngày, hàng tuần, hàng tháng, hoặc theo phút).

3. Quản lý trạng thái tác vụ:
Theo dõi trạng thái tác vụ (chạy thành công, lỗi, hoặc đang xử lý).

4. Chạy tác vụ nền (Background Tasks):
ir.cron thường được sử dụng để thực hiện các tác vụ lớn không yêu cầu trả kết quả ngay lập tức, như gửi email hàng loạt, tính toán báo cáo, đồng bộ dữ liệu, hoặc cập nhật thông tin từ hệ thống bên ngoài.

### Ví dụ ứng dụng của ir.cron:
- Gửi email định kỳ: Gửi thông báo hoặc báo cáo theo lịch.
- Cập nhật tồn kho: Tự động kiểm tra và đồng bộ số lượng hàng hóa trong kho.
- Xóa dữ liệu tạm thời: Xóa dữ liệu không cần thiết hoặc quá hạn trong cơ sở dữ liệu.
- Đồng bộ dữ liệu API: Tự động lấy hoặc gửi dữ liệu đến hệ thống khác qua API.

### Cách tạo Scheduled Action với ir.cron:
1. Qua giao diện người dùng:
- Vào Settings > Technical > Automation > Scheduled Actions.
- Tạo mới một hành động với tên, mô tả, thời gian lặp lại, và phương thức (Python function).

2. Qua code Python: Bạn có thể định nghĩa trong module của mình bằng cách thêm bản ghi vào model ir.cron. Ví dụ:
```python
from odoo import fields, models

class MyModule(models.Model):
    _name = 'my.module'

    def my_scheduled_task(self):
            """
            Hàm này thực hiện công việc cần chạy tự động.
            Thêm logic xử lý của bạn vào đây, ví dụ: gửi email, cập nhật dữ liệu, hoặc đồng bộ API.
            """
            # Ví dụ: log một thông báo
            self.env['ir.logging'].create({
                'name': 'Scheduled Task',
                'type': 'server',
                'message': 'This is my scheduled task running automatically.',
                'level': 'info',
            })

def create_scheduled_action(cr, registry):
    """
    Hàm này được gọi khi cài đặt module. Nó sẽ tạo một bản ghi 'ir.cron',
    định nghĩa một tác vụ tự động hóa (Scheduled Action).
    """
    # Khởi tạo môi trường với quyền siêu người dùng (SUPERUSER_ID)
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Tạo một tác vụ tự động (Scheduled Action)
    env['ir.cron'].create({
        'name': 'My Scheduled Task',  # Tên hiển thị của tác vụ
        'model_id': env.ref('your_module.model_my_module').id,  # ID của model sẽ thực thi
        'state': 'code',  # Trạng thái "code" nghĩa là chạy đoạn mã Python trong 'code'
        'code': 'env["my.module"].my_scheduled_task()',  # Mã Python sẽ được chạy
        'interval_number': 1,  # Khoảng thời gian lặp lại (ví dụ: 1 giờ)
        'interval_type': 'hours',  # Đơn vị thời gian: giờ
        'active': True,  # Bật tác vụ này
    })


```

### Lưu ý:
- Cần cấu hình Odoo Scheduler (odoo-bin - workers) hoặc cron job của hệ thống để đảm bảo các tác vụ được thực thi đúng theo lịch.
- Khi sử dụng, hãy kiểm tra hiệu suất để tránh các tác vụ chạy quá nhiều gây tải hệ thống.
