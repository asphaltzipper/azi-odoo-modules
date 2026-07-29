import requests
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


# some Hologram documentation is hidden here:
# https://github.com/hologram-io/rest-api-docs/blob/master/apiary.apib


class MqttClient(models.Model):
    _name = 'mqtt.client'
    _description = 'MQTT SIM Client'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _sql_constraints = [('name_uniq', 'unique (name)', """Client ICCID must be unique."""), ]

    name = fields.Char(
        string='ICCID',
        help="ICCID from the SIM card",
        copy=False,
    )
    serial_ids = fields.One2many(
        comodel_name='mqtt.client.serial',
        inverse_name='client_id',
        string='Serial Numbers',
    )
    current_lot_id = fields.Many2one(
        comodel_name='stock.lot',
        compute='_compute_current_lot_id',
    )
    history_ids = fields.One2many(
        comodel_name='mqtt.message.history',
        inverse_name='client_id',
        string='Signal History',
    )
    incoming_message_count = fields.Integer(
        string="Incoming Message Count",
        compute="_compute_message_count",
    )
    outgoing_message_count = fields.Integer(
        string="Outgoing Message Count",
        compute="_compute_message_count",
    )

    state = fields.Selection(
        selection=[
            ('unallocated', 'Unallocated / Not Added'),
            ('live', 'Active / Live'),
            ('pause', 'Paused / Inactive'),
            ('dead', 'Dead')
        ],
        string='Hologram State',
        required=True,
        default='unallocated',
    )
    hologram_name = fields.Char(
        string='Hologram Name',
        readonly=True,
        copy=False,
    )
    hologram_device_id = fields.Integer(
        string='Hologram Device ID',
        readonly=True,
        copy=False,
    )
    hologram_link_id = fields.Integer(
        string='Hologram Link ID',
        readonly=True,
        copy=False,
    )
    hologram_plan = fields.Char(
        string='Data Plan',
        readonly=True,
    )
    hologram_sync_date = fields.Datetime(
        string='Last Sync Date',
        readonly=True,
    )

    @api.depends('serial_ids', 'serial_ids.sequence')
    def _compute_current_lot_id(self):
        for rec in self:
            if rec.serial_ids:
                rec.current_lot_id = rec.serial_ids[0].lot_id
            else:
                rec.current_lot_id = False

    @api.depends('history_ids.direction', 'history_ids.client_id')
    def _compute_message_count(self):
        for rec in self:
            rec.outgoing_message_count = len([
                res for res in rec.history_ids if res.direction == 'outgoing'
            ])
            rec.incoming_message_count = len([
                res for res in rec.history_ids if res.direction == 'incoming'
            ])

    def action_review_incoming_history(self):
        self.ensure_one()
        action = self.sudo().env.ref('mqtt_integration.action_mqtt_incoming_message').read()[0]
        action.update({
            'domain': [
                ('client_id', '=', self.id),
                ('direction', '=', 'incoming'),
            ],
            'context': {
                'default_client_id': self.id,
                'default_direction': 'incoming'
            }
        })
        return action

    def action_review_outgoing_history(self):
        self.ensure_one()
        action = self.sudo().env.ref('mqtt_integration.action_mqtt_outgoing_message').read()[0]
        action.update({
            'domain': [
                ('client_id', '=', self.id),
                ('direction', '=', 'outgoing'),
            ],
            'context': {
                'default_client_id': self.id,
                'default_direction': 'outgoing'
            }
        })
        return action

    def _get_api_auth(self):
        api_key = self.env['ir.config_parameter'].sudo().get_param('hologram.api_key')
        if not api_key:
            raise UserError(
                _('Hologram API Key is not configured. Please set it in Settings.'))
        return ('apikey', api_key)

    def _get_org_id(self):
        org_id = self.env['ir.config_parameter'].sudo().get_param('hologram.org_id')
        if not org_id:
            raise UserError(
                _('Hologram Organization ID is not configured. Please set it in Settings.'))
        return org_id

    def _get_default_plan(self):
        plan_id = self.env['ir.config_parameter'].sudo().get_param(
            'hologram.default_plan')
        if not plan_id:
            raise UserError(
                _('Hologram Default Plan is not configured. Please set it in Settings.'))
        return plan_id

    def _get_plan_info(self):
        plans_data = self._hologram_api_request('GET', '/plans')
        default_plan_id = self._get_default_plan()
        default_plan = {}
        for plan in plans_data.get('data', []):
            if plan.get('id') == default_plan_id:
                default_plan = plan
        if not default_plan:
            raise UserError(
                _('Hologram Default Plan is not configured. Please set it in Settings.'))
        zone = next(iter(list(
            default_plan.get('tiers', {}).get('BASE', {}).get('zones', {}).keys())),
                    None)
        if not zone:
            raise UserError(_("Failed to get zone from default plan"))
        return (default_plan_id, zone)

    def _hologram_api_request(self, method, endpoint, params=None, json_data=None):
        base_url = "https://dashboard.hologram.io/api/1"
        auth = self._get_api_auth()
        url = f"{base_url}{endpoint}"

        if not params:
            params = {}
        if 'orgid' not in params:
            try:
                params['orgid'] = self._get_org_id()
            except Exception:
                pass

        try:
            resp = requests.request(method, url, auth=auth, params=params,
                                    json=json_data, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            error_body = getattr(e.response, 'text', 'No response body')
            raise UserError(_("Hologram API Error: %s\nResponse: %s") % (e, error_body))

    def action_fetch_status(self):
        """Fetch status from Hologram API"""
        for sim in self:
            if not sim.name:
                continue

            data = sim._hologram_api_request('GET', '/devices')
            devices = data.get('data', [])

            sim_link = None
            sim_device = None

            for device in devices:
                cellular_links = device.get('links', {}).get('cellular', [])

                for link in cellular_links:
                    if link.get('sim') == sim.name or link.get('iccid') == sim.name:
                        sim_link = link
                        sim_device = device
                        break
                if sim_link:
                    break

            if sim_link:
                sim.hologram_link_id = sim_link.get('id')
                sim.hologram_name = sim_device.get('name')
                sim.hologram_device_id = sim_device.get(
                    'id') if sim_device else sim_link.get('device_id')
                state = sim_link.get('state', '').lower()
                sim.state = state if state in ['live', 'pause',
                                               'dead'] else 'unallocated'
                sim.hologram_plan = sim_link.get('plan', '')
                sim.hologram_sync_date = fields.Datetime.now()
            else:
                # If not found
                sim.state = 'unallocated'
                sim.hologram_device_id = 0
                sim.hologram_link_id = 0
                sim.hologram_sync_date = False


        return True

    def action_add_sims(self):
        """Add / Activate new SIM explicitly"""
        plan_id, zone = self._get_plan_info()
        iccids = self.mapped("name")
        json_data = {
            "sims": iccids,
            "plan": plan_id,
            "zone": zone,
            "orgid": self._get_org_id(),
        }
        res = self._hologram_api_request(
            'POST',
            '/links/cellular/bulkclaim',
            json_data=json_data,
        )
        for sim in self:
            sim.message_post(body=_("SIM Add attempt result: %s") % res)
        self.action_fetch_status()

    def action_activate_sim(self):
        for sim in self:
            if not sim.hologram_link_id:
                sim.action_fetch_status()
            if not sim.hologram_link_id:
                raise UserError(
                    _("SIM not found in Hologram account. Please Add it first."))

            endpoint = f"/links/cellular/{sim.hologram_link_id}/state"
            json_data = {"state": "live"}
            res = sim._hologram_api_request('POST', endpoint, json_data=json_data)
            sim.message_post(body=_("SIM Activated: %s") % res)
            sim.action_fetch_status()

    def action_deactivate_sim(self):
        for sim in self:
            if not sim.hologram_link_id:
                raise UserError(_("SIM link ID unknown."))
            endpoint = f"/links/cellular/{sim.hologram_link_id}/state"
            json_data = {"state": "pause"}
            res = sim._hologram_api_request('POST', endpoint, json_data=json_data)
            sim.message_post(body=_("SIM Deactivated/Paused: %s") % res)
            sim.action_fetch_status()

    @api.model
    def cron_sync_sims(self):
        sims = self.search([('name', '!=', False)])
        for sim in sims:
            try:
                sim.action_fetch_status()
                # Commit to save progress in case of crash on next
                self.env.cr.commit()
            except Exception as e:
                _logger.error("Failed to sync Hologram SIM %s: %s", sim.name, e)
