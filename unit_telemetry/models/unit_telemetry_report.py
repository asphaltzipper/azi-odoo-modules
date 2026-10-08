# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools


class UnitTelemetryReport(models.Model):
    _name = 'unit.telemetry.report'
    _description = 'Unit Telemetry Report'
    _auto = False

    lot_id = fields.Many2one('stock.lot', 'Serial')
    msg_id = fields.Many2one('mqtt.message.history', 'Message Id')
    tx_date = fields.Datetime('Date')
    topic_name = fields.Char('Topic Name')
    batt = fields.Float('Batt')
    fast_send = fields.Integer('Fast Send')
    mode = fields.Char('Mode')
    rsrp = fields.Integer('RSRP')
    rsrq = fields.Integer('RSRQ')
    rssnr = fields.Integer('RSSNR')
    zpwr = fields.Float('ZPWR')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'unit_telemetry_report')
        self.env.cr.execute(""" 
            CREATE VIEW unit_telemetry_report AS (
                WITH sys AS (
                    SELECT
                        utr.lot_id,
                        utr.msg_id,
                        utr.read_time,
                        uto.name as topic_name,
                        max(float_value) filter (where uty.name = 'batt') as batt,
                        max(integer_value) filter (where uty.name = 'fast_send') as fast_send,
                        max(char_value) filter (where uty.name = 'mode') as mode,
                        max(integer_value) filter (where uty.name = 'rsrp') as rsrp,
                        max(integer_value) filter (where uty.name = 'rsrq') as rsrq,
                        max(integer_value) filter (where uty.name = 'rssnr') as rssnr,
                        max(float_value) filter (where uty.name = 'zpwr') as zpwr
                    FROM unit_telemetry_reading utr
                    LEFT JOIN unit_telemetry_topic uto on uto.id=utr.topic_id
                    LEFT JOIN unit_telemetry_type uty on uty.id=utr.type_id
                    WHERE uto.name='sys'
                    GROUP BY utr.lot_id, utr.msg_id, utr.read_time, uto.name
                )
                SELECT 
                    sys.msg_id AS id,
                    sys.lot_id,
                    sys.msg_id,
                    sys.read_time AS tx_date,
                    sys.batt,
                    sys.fast_send,
                    sys.mode,
                    sys.rsrp,
                    sys.rsrq,
                    sys.rssnr,
                    sys.zpwr
                FROM sys
            )"""
        )
