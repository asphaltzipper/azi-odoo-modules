import base64
from PyPDF2 import PdfFileReader
from io import BytesIO
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class VectorKnowledge(models.Model):
    _name = 'vector.knowledge'
    _inherit = ['mail.thread']
    _description = 'Vector Data'

    name = fields.Char('Name', required=True)
    connector_id = fields.Many2one('openai.connector', string='AI Connector')
    data_type = fields.Selection([('text', 'Text'), ('pdf', 'PDF')], 'Data type', default='text')
    state = fields.Selection([('draft', 'Draft'), ('publish', 'Published')], 'Status', default='draft')
    knowledge_text = fields.Text('Knowledge Text')
    attachment = fields.Binary('Attachment')
    attachment_name = fields.Char('File Name')
    knowledge_chunk_ids = fields.One2many('vector.knowledge.chunk', 'knowledge_id', 'Chunks')

    def action_publish(self):
        self.ensure_one()
        if self.data_type == 'text' and not self.knowledge_text.split():
            raise UserError(_("Knowledge Text is required to generate embeddings."))
        if self.data_type == 'pdf':
            attachment_data = base64.b64decode(self.attachment)
            attachment = BytesIO(attachment_data)
            attachment_reader = PdfFileReader(attachment)
            for i in range(attachment_reader.numPages):
                content_per_page = attachment_reader.pages[i].extractText()
                if content_per_page:
                    embedding = self.connector_id._get_embeddings(content_per_page, self)
                    embedding_vector = '[' + ','.join(map(str, embedding)) + ']'
                    self.env.cr.execute("""
                        INSERT INTO vector_knowledge_chunk (knowledge_id, embedding, chunk_text) VALUES(%s, %s, %s) 
                    """, (self.id, embedding_vector, content_per_page))
        else:
            embedding = self.connector_id._get_embeddings(self.knowledge_text, self)
            if embedding:
                embedding_vector = '['+','.join(map(str, embedding))+']'
                self.env.cr.execute("""
                    INSERT INTO vector_knowledge_chunk (knowledge_id, embedding, chunk_text) VALUES(%s, %s, %s) 
                """, (self.id, embedding_vector, self.knowledge_text))
        self.state = 'publish'
        self.message_post(body="Knowledge published and embedding generated successfully.")


class VectorKnowledgeChunk(models.Model):
    _name = 'vector.knowledge.chunk'

    knowledge_id = fields.Many2one('vector.knowledge', 'Knowledge', ondelete='cascade')
    chunk_text = fields.Text('Chunk Text')

    def _auto_init(self):
        res = super(VectorKnowledgeChunk, self)._auto_init()
        self.env.cr.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'vector_knowledge_chunk' AND column_name = 'embedding'
        """)
        if not self.env.cr.fetchone():
            self.env.cr.execute('ALTER TABLE vector_knowledge_chunk ADD COLUMN embedding vector(1536)')
        return res
