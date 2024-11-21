/** @odoo-module **/  // Định nghĩa đây là một module trong Odoo.

import { Component, onWillStart, onMounted, markup, useState } from "@odoo/owl";// Import các hàm và module cần thiết từ OWL framework trong Odoo.
import { useService } from "@web/core/utils/hooks";// Import `useService` để sử dụng các dịch vụ Odoo, ví dụ như notification.
import { registry } from "@web/core/registry";// Import `registry` để đăng ký component vào danh mục hành động.
import { _t } from "@web/core/l10n/translation";// Import `_t` để hỗ trợ dịch nội dung văn bản.
import { standardFieldProps } from "@web/views/fields/standard_field_props";// Import `standardFieldProps` để sử dụng các thuộc tính mặc định của trường.

export class Database extends Component {
  // Định nghĩa một class component có tên là `Database`.
  setup() {
    // Hàm setup được chạy khi component khởi tạo.
    this.state = useState({databases: this.props.action.params.databases,});// Tạo một state chứa danh sách cơ sở dữ liệu từ tham số truyền vào action.
    this.notification = useService("notification");// Sử dụng dịch vụ `notification` để hiển thị thông báo. 
    console.log(this);// Ghi log ra console để kiểm tra thông tin của component.
  
    onMounted(() => {
      // Thực hiện các hành động khi component được render.
      const footer = document.querySelector("footer"); // Tìm phần tử footer trong DOM.
      if (footer != null) footer.classList.add("d-none");// Ẩn footer bằng cách thêm class "d-none" nếu footer tồn tại.
      const formSheet = document.querySelector(".modal-dialog");// Tìm phần tử có class "modal-dialog" (khung hộp thoại).
      formSheet.setAttribute(
        "style",
        "max-width:600px; margin-left: auto; margin-right: auto;"// Đặt style cho khung hộp thoại với chiều rộng tối đa là 600px, căn giữa.
      );

      const self = this;// Gán `this` vào biến `self` để dùng trong callback.
      const iframe = document.getElementById("hidden_frame");// Lấy phần tử iframe có id "hidden_frame".
      iframe.addEventListener("load", async () => { // Lắng nghe sự kiện "load" của iframe.
        try {
          const iframeContent =
            iframe.contentDocument || iframe.contentWindow.document;// Lấy nội dung của iframe.

          const response = JSON.parse(iframeContent.body.textContent);// Parse nội dung từ iframe thành JSON.
          if (response.status === "success") { // Nếu trạng thái phản hồi là "success".
           
            window.location.reload(); // Tải lại trang hiện tại.
          } else if (response.message) {// Nếu phản hồi chứa thông báo lỗi.
            this.showNotification(response.message, "Error", "danger");// Hiển thị thông báo lỗi với tiêu đề "Error" và kiểu "danger".
          }
        } catch (error) {}// Bỏ qua lỗi nếu xảy ra.
      });
    });
  }

  showNotification(content, title, type) { // Hàm hiển thị thông báo.
    const notification = this.notification; // Lấy đối tượng `notification` từ dịch vụ.
    notification.add(content, {
      title: title,// Tiêu đề của thông báo.
      type: type, // Kiểu thông báo: "success", "danger", v.v.
      className: "p-4", // Định nghĩa thêm class CSS cho thông báo.
    });
  }
}

Database.template = "Blogtransfer.database";
// Gán template với ID "Blogtransfer.database" cho component `Database`.
Database.props = { ...standardFieldProps };
// Sử dụng các thuộc tính chuẩn của trường từ `standardFieldProps`.
registry.category("actions").add("Blogtransfer.database", Database);
// Đăng ký component vào danh mục "actions" với tên "Blogtransfer.database".
