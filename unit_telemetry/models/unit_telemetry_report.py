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
    batt = fields.Float(
        string='Batt',
        group_operator="avg",
    )
    fast_send = fields.Integer('Fast Send')
    mode = fields.Char('Mode')
    rsrp = fields.Integer(
        string='RSRP',
        group_operator="avg",
    )
    rsrq = fields.Integer(
        string='RSRQ',
        group_operator="avg",
    )
    rssnr = fields.Integer(
        string='RSSNR',
        group_operator="avg",
    )
    zpwr = fields.Float(
        string='ZPWR',
        group_operator="avg",
    )

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
                    sys.topic_name,
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


class UnitTelemetryHrReport(models.Model):
    _name = 'unit.telemetry.hr.report'
    _description = 'Unit Telemetry Hours Report'
    _auto = False

    lot_id = fields.Many2one('stock.lot', 'Serial')
    msg_id = fields.Many2one('mqtt.message.history', 'Message Id')
    tx_date = fields.Datetime('Date')
    topic_name = fields.Char('Topic Name')
    hrs = fields.Float('Hours', group_operator='avg')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'unit_telemetry_hr_report')
        self.env.cr.execute(""" 
            CREATE OR REPLACE VIEW unit_telemetry_hr_report AS (
                WITH hrs AS (
                    SELECT
                        utr.lot_id,
                        utr.msg_id,
                        utr.read_time,
                        uto.name AS topic_name,
                        MAX(float_value) FILTER (WHERE uty.name = 'hrs') AS hrs
                    FROM unit_telemetry_reading utr
                    LEFT JOIN unit_telemetry_topic uto ON uto.id = utr.topic_id
                    LEFT JOIN unit_telemetry_type uty ON uty.id = utr.type_id
                    WHERE uto.name = 'hrs'
                    GROUP BY utr.lot_id, utr.msg_id, utr.read_time, uto.name
                )
                SELECT
                    hrs.msg_id AS id,
                    hrs.lot_id,
                    hrs.msg_id,
                    CASE 
                        WHEN hrs.read_time > '2050-01-01' THEN mmh.timestamp 
                        ELSE hrs.read_time 
                    END AS tx_date,
                    hrs.topic_name,
                    hrs.hrs
                FROM hrs
                LEFT JOIN mqtt_message_history mmh ON mmh.id = hrs.msg_id
            )"""
                            )


class UnitTelemetryGPSReport(models.Model):
    _name = 'unit.telemetry.gps.report'
    _description = 'Unit Telemetry GPS Report'
    _auto = False

    lot_id = fields.Many2one('stock.lot', 'Serial')
    msg_id = fields.Many2one('mqtt.message.history', 'Message Id')
    tx_date = fields.Datetime('Date')
    lat = fields.Float('Latitude', group_operator='avg')
    long = fields.Float('Longitude', group_operator='avg')
    hpa = fields.Float('HPA', group_operator='avg')
    sats = fields.Integer('SATS')
    coord_str = fields.Char('Coordinates')
    map_link = fields.Char('Map Link')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'unit_telemetry_gps_report')
        self.env.cr.execute(""" 
            CREATE OR REPLACE VIEW unit_telemetry_gps_report AS (
                WITH gps AS (
                    SELECT
                        utr.lot_id,
                        utr.msg_id,
                        utr.read_time,
                        uto.name AS topic_name,
                        MAX(float_value) FILTER (WHERE uty.name = 'lat') AS lat,
                        MAX(float_value) FILTER (WHERE uty.name = 'long') AS long,
                        MAX(float_value) FILTER (WHERE uty.name = 'hpa') AS hpa,
                        MAX(integer_value) FILTER (WHERE uty.name = 'sats') AS sats
                    FROM unit_telemetry_reading utr
                    LEFT JOIN unit_telemetry_topic uto ON uto.id = utr.topic_id
                    LEFT JOIN unit_telemetry_type uty ON uty.id = utr.type_id
                    WHERE uto.name = 'gps'
                    GROUP BY utr.lot_id, utr.msg_id, utr.read_time, uto.name
                )
                SELECT
                    gps.msg_id AS id,
                    gps.lot_id,
                    gps.msg_id,
                    CASE 
                        WHEN gps.read_time > '2050-01-01' THEN mmh.timestamp 
                        ELSE gps.read_time 
                    END AS tx_date,
                    gps.lat,
                    gps.long,
                    gps.hpa,
                    gps.sats,
                    TO_CHAR(gps.lat, '000D000000') || ', ' || TO_CHAR(gps.long, '000D000000') AS coord_str,
                    'https://www.google.com/maps/place/' || TO_CHAR(gps.lat, '000D000000') || ',' || TO_CHAR(gps.long, '000D000000') AS map_link
                FROM gps
                LEFT JOIN mqtt_message_history mmh ON mmh.id = gps.msg_id
            )
        """
                            )


class UnitTelemetryDtcReport(models.Model):
    _name = 'unit.telemetry.dtc.report'
    _description = 'Unit Telemetry DTC Report'
    _auto = False

    lot_id = fields.Many2one('stock.lot', 'Serial')
    msg_id = fields.Many2one('mqtt.message.history', 'Message Id')
    tx_date = fields.Datetime('Date')
    topic_name = fields.Char('Topic Name')
    spn = fields.Integer('SPN', group_operator='avg')
    fmi = fields.Integer('FMI', group_operator='avg')
    addr = fields.Integer('ADDR', group_operator='avg')
    oc = fields.Integer('OC', group_operator='avg')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'unit_telemetry_dtc_report')
        self.env.cr.execute(""" 
            CREATE OR REPLACE VIEW unit_telemetry_dtc_report AS (
                with dtc as (
                    select
                        utr.lot_id,
                        utr.msg_id,
                        utr.read_time,
                        uto.name as topic_name,
                        max(integer_value) filter (where uty.name = 'spn') as spn,
                        max(integer_value) filter (where uty.name = 'fmi') as fmi,
                        max(integer_value) filter (where uty.name = 'addr') as addr,
                        max(integer_value) filter (where uty.name = 'oc') as oc
                    from unit_telemetry_reading utr
                    left join unit_telemetry_topic uto on uto.id=utr.topic_id
                    left join unit_telemetry_type uty on uty.id=utr.type_id
                    where uto.name='dtc'
                    group by utr.lot_id, utr.msg_id, utr.read_time, uto.name
                )
                select
                    dtc.msg_id as id,
                    dtc.lot_id,
                    dtc.msg_id,
                    dtc.read_time as tx_date,
                    dtc.topic_name,
                    dtc.spn,
                    dtc.fmi,
                    dtc.addr,
                    dtc.oc
                from dtc
                left join mqtt_message_history mmh on mmh.id=dtc.msg_id
                where dtc.spn IS NOT NULL AND dtc.spn != 0
                
            )"""
                            )


class UnitTelemetryOpsReport(models.Model):
    _name = 'unit.telemetry.ops.report'
    _description = 'Unit Telemetry OPS Report'
    _auto = False

    lot_id = fields.Many2one('stock.lot', 'Serial')
    msg_id = fields.Many2one('mqtt.message.history', 'Message Id')
    tx_date = fields.Datetime('Date')
    topic_name = fields.Char('Topic Name')
    b_pres = fields.Float('B-Pres', group_operator='avg')
    c_hrs = fields.Float('C-HRs', group_operator='avg')
    c_pres = fields.Float('C-Pres', group_operator='avg')
    c_state = fields.Boolean('C-State')
    c_tmp = fields.Float('C-Temp', group_operator='avg')
    estp = fields.Integer('ESTP')
    g_tmp = fields.Float('G-Temp', group_operator='avg')
    h_state = fields.Boolean('H-State')
    h_tmp = fields.Float('H-Temp', group_operator='avg')
    load = fields.Float('Load', group_operator='avg')
    m_pres = fields.Float('M-Pres', group_operator='avg')
    rpm = fields.Float('RPM', group_operator='avg')
    spd = fields.Float('SPD', group_operator='avg')
    v_chg = fields.Float('V-Chg', group_operator='avg')
    v_crk = fields.Float('V-Crk', group_operator='avg')
    v_rst = fields.Float('V-Rst', group_operator='avg')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'unit_telemetry_ops_report')
        self.env.cr.execute(""" 
            CREATE OR REPLACE VIEW unit_telemetry_ops_report AS (
                with ops as (
                    select
                        utr.lot_id,
                        utr.msg_id,
                        utr.read_time,
                        uto.name as topic_name,
                        max(float_value) filter (where uty.name = 'b_pres') as b_pres,
                        max(float_value) filter (where uty.name = 'c_hrs') as c_hrs,
                        max(float_value) filter (where uty.name = 'c_pres') as c_pres,
                        bool_or(bool_value) filter (where uty.name = 'c_state') as c_state,
                        max(float_value) filter (where uty.name = 'c_tmp') as c_tmp,
                        max(integer_value) filter (where uty.name = 'estp') as estp,
                        max(float_value) filter (where uty.name = 'g_tmp') as g_tmp,
                        bool_or(bool_value) filter (where uty.name = 'h_state') as h_state,
                        max(float_value) filter (where uty.name = 'h_tmp') as h_tmp,
                        max(float_value) filter (where uty.name = 'load') as load,
                        max(float_value) filter (where uty.name = 'm_pres') as m_pres,
                        max(float_value) filter (where uty.name = 'rpm') as rpm,
                        max(float_value) filter (where uty.name = 'spd') as spd,
                        max(float_value) filter (where uty.name = 'v_chg') as v_chg,
                        max(float_value) filter (where uty.name = 'v_crk') as v_crk,
                        max(float_value) filter (where uty.name = 'v_rst') as v_rst
                    from unit_telemetry_reading utr
                    left join unit_telemetry_topic uto on uto.id=utr.topic_id
                    left join unit_telemetry_type uty on uty.id=utr.type_id
                    where uto.name='ops'
                    group by utr.lot_id, utr.msg_id, utr.read_time, uto.name
                )
                select
                    ops.msg_id as id,
                    ops.lot_id,
                    ops.msg_id,
                    ops.topic_name,
                    ops.read_time as tx_date,
                    ops.b_pres,
                    ops.c_hrs,
                    ops.c_pres,
                    ops.c_state,
                    ops.c_tmp,
                    ops.estp,
                    ops.g_tmp,
                    ops.h_state,
                    ops.h_tmp,
                    ops.load,
                    ops.m_pres,
                    ops.rpm,
                    ops.spd,
                    ops.v_chg,
                    ops.v_crk,
                    ops.v_rst
                from ops
                left join mqtt_message_history mmh on mmh.id=ops.msg_id
            )"""
                            )
