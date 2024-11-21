from odoo.http import request
from odoo import models, fields, api, _  # Nhập các mô-đun cần thiết từ Odoo
from odoo.exceptions import UserError  # Nhập ngoại lệ UserError để xử lý lỗi
import requests  # Nhập thư viện requests để thực hiện các yêu cầu HTTP
import logging  # Nhập thư viện logging để ghi lại thông tin và lỗi
import json
_logger = logging.getLogger(__name__)  # Tạo logger để ghi lại thông tin

# Định nghĩa class cho Server

class TagMapping(models.Model):
    _name = 'tag.mapping'  # Định nghĩa tên model là 'server'
    _description = 'server tag'  # Mô tả ngắn về model

    name = fields.Char(string="Local Blog Tag", required=True) #Gán nhãn hiển thị cho trường trong giao diện người dùng là "Local Blog Tag".
    local_tag_id = fields.Many2one('blog.tag', ondelete='cascade', string='Local Blog Tag')#Là một trường quan hệ kiểu Many2one, liên kết với model blog.tag.
    
    server_id = fields.Many2one("server", ondelete='cascade', string="Server Id") #Là một trường quan hệ kiểu Many2one, liên kết với model server.
    server_tag_ids = fields.Many2many("server.tag", string="Server Blog Tags") # Là một trường quan hệ kiểu Many2many, liên kết với model server.tag.

    # Override phương thức write mặc định của Odoo
    def write(self, vals):
        _logger.info(vals)
        if vals.get("server_tag_ids", False):
            for server_tag in vals["server_tag_ids"]:# Duyệt qua từng thay đổi trong server_tag_ids
                local_tag_ids = []  # List chứa các command để cập nhật local_tag_ids
                if server_tag[0] == 4:# Nếu là command 4 (thêm mới)
                    # Thêm local tag vào server tag
                    local_tag_ids.append((4, self.local_tag_id.id))# self.local_tag_id.id: ID của local tag trong record hiện tại
                elif server_tag[0] == 3:# Nếu là command 3 (xóa)
                    # Xóa liên kết giữa local tag và server tag
                    local_tag_ids.append((3, self.local_tag_id.id))
                # Cập nhật bảng server.tag:
                self.env["server.tag"].browse(server_tag[1]).write(
                    {"local_tag_ids": local_tag_ids})
                
        # Gọi write() của lớp cha để thực hiện cập nhật bình thường
        new_record = super(TagMapping, self).write(vals)
        return new_record
