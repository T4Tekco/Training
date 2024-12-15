from odoo import models, fields, api  # Missing comma between fields and api
from datetime import datetime 
import logging  

_logger = logging.getLogger(__name__)  

class AttachmentMapping(models.Model):     
    _name = 'attachment.mapping'     
    _description = 'Attachment Mapping'

    local_attachment_id = fields.Many2one(
        'ir.attachment',
        string='Local Attachment',
        required=True,
        ondelete='cascade'
    )

    server_id = fields.Many2one(
        'server',
        string='Server',
        required=True,
        ondelete='cascade'
    )
      
    server_attachment_id = fields.Char(         
        string='Server Attachment',         
        required=True     
    )      

    server_attachment_path = fields.Char(         
        string='Server Attachment Path',         
        required=True     
    )

