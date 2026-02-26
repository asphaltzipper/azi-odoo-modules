import threading
import logging
from ollama import chat, pull
from ollama import ChatResponse
from odoo import models, fields, api, registry, _

_logger = logging.getLogger(__name__)


class OllamaConnector(models.Model):
    _name = 'ollama.connector'
    _inherit = ['mail.thread']
    _description = 'Ollama Connector'
    _rec_name = 'ai_model'

    system_prompt = fields.Text('System Prompt', required=True, default='You are a helpful assistant')
    ai_model = fields.Char('Model', required=True, default='llama3.2')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pulling', 'Pulling'),
        ('connected', 'Connected'),
        ('failed', 'Failed')
    ], 'Status', default='draft', readonly=True)

    def _pull_ai_model(self, db_name, res_id):
        with registry(db_name).cursor() as cr:
            env = api.Environment(cr, self.env.uid, {})
            record = env['ollama.connector'].browse(res_id)
            try:
                _logger.info(f"Starting to pull for model {record.ai_model}")
                pull(record.ai_model)
                record.write({'state': 'connected'})
                record.message_post(body=_(f"Model {record.ai_model} successfully downloaded and connected."))
            except Exception as e:
                record.write({'state': 'failed'})
                record.message_post(body=_(f"Failed to pull model {record.ai_model}: {str(e)}"))

    def action_connect(self):
        self.ensure_one()
        self.state = 'pulling'
        self.message_post(body=_(f"Started pulling model {self.ai_model} in the background."))
        thread = threading.Thread(
            target=self._pull_ai_model,
            args=(self.env.cr.dbname, self.id),
            daemon=True
        )
        thread.start()

    def action_to_draft(self):
        self.state = 'draft'

    def call_ai_model(self, user_prompt):
        messages = [
            {'role': 'system', 'content': self.system_prompt},
            {'role': 'user', 'content': user_prompt},
        ]
        response: ChatResponse = chat(model=self.ai_model, messages=messages)
        return response.message.content

