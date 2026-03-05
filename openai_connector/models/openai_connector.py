import os
from dotenv import load_dotenv, find_dotenv
import logging
from openai import OpenAI
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

load_dotenv(find_dotenv(), override=True)


class OpenAIConnector(models.Model):
    _name = 'openai.connector'
    _inherit = ['mail.thread']
    _description = 'OpenAI Connector'
    _rec_name = 'ai_model'

    system_prompt = fields.Text('System Prompt', required=True, default='You are a helpful assistant')
    ai_model = fields.Char('Model', required=True, default='gpt-4o-mini')
    is_openai_model = fields.Boolean('Is OpenAI Model?', default=True)
    base_url = fields.Char('Base URL', help='Leave empty for OpenAI; use for Gemini or any other Model.')
    api_key_name = fields.Char('API Key Name', help='API key name exists in the .env file')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('connected', 'Connected'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ], 'Status', default='draft', readonly=True)

    def get_env_var(self):
        return os.getenv(self.api_key_name)

    def get_client(self):
        api_key = self.get_env_var()
        if self.base_url and not self.is_openai_model:
            return OpenAI(base_url=self.base_url, api_key=api_key)
        return OpenAI(api_key=api_key)

    def _check_openai_api_connection(self, client):
        try:
            client.models.list()
            self.message_post(body='Connected Successfully and the API key is valid.')
            return True
        except Exception as e:
            _logger.error(f"Connection failed: {str(e)}")
            self.message_post(body=f'Connection failed: {str(e)}')
            return False

    def action_connect(self):
        self.ensure_one()
        api_key = self.get_env_var()
        if not api_key:
            raise ValidationError(f'There is no API key with this name {self.api_key_name}')
        client = self.get_client()
        if self._check_openai_api_connection(client):
            self.state = 'connected'
        else:
            self.state = 'failed'

    def action_to_draft(self):
        self.state = 'draft'

    def call_ai_model(self, user_prompt):
        messages = [
            {'role': 'system', 'content': self.system_prompt},
            {'role': 'user', 'content': user_prompt},
        ]
        client = self.get_client()
        response = client.chat.completions.create(model=self.ai_model, messages=messages)
        return response.choices[0].message.content

