# Unit Telemetry Views Implementation Guide (OPS, HRS, GPS, DTC, SYS)

This document details how to implement Pivot, Chart, Tree, and Search views for all unit telemetry topics (**OPS**, **HRS**, **GPS**, **DTC**, and **SYS**) using Odoo SQL View models (`_auto = False`).

---

## Architecture Overview

Each telemetry topic serves a distinct functional purpose with different attributes, data types, and reporting needs:

| Topic | Description | Key Fields & Measures | Primary Views |
|---|---|---|---|
| **OPS** | Operational sensor readings | RPM, Load %, Belt Pres, Clutch Pres, Clutch State, Coolant Temp, Hyd Temp, Gear Temp, Voltages | Pivot, Graph (Line), Tree, Search |
| **HRS** | Machine Hour tracking | Engine Hours (`hrs`) | Pivot, Graph (Line), Tree |
| **GPS** | Fleet Geolocation | Latitude, Longitude, Accuracy (hpa), Satellites, Google Maps URL | Tree (Clickable URL), Pivot, Search |
| **DTC** | Diagnostic Trouble Codes | SPN, FMI, Source Addr, Occurrences (`oc`), Fault Label | Pivot, Graph (Bar), Tree, Search |
| **SYS** | Modem & System Health | Battery, Fast Send, Mode, RSRP, RSRQ, RSSNR, ZPWR | Pivot, Graph (Line), Tree, Search |

---

## 1. Python Models (`models/unit_telemetry_report.py`)

You can define all 4 new SQL view models alongside the existing `unit.telemetry.report` in `custom_addons/unit_telemetry/models/unit_telemetry_report.py`:

```python
# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools


# =========================================================================
# 1. SYS: System Health Report (Existing)
# =========================================================================
class UnitTelemetryReport(models.Model):
    _name = 'unit.telemetry.report'
    _description = 'Unit Telemetry System Report'
    _auto = False
    _order = 'tx_date desc'

    lot_id = fields.Many2one('stock.lot', 'Serial', readonly=True)
    msg_id = fields.Many2one('mqtt.message.history', 'Message Id', readonly=True)
    tx_date = fields.Datetime('Date', readonly=True)
    batt = fields.Float('Battery Voltage (V)', readonly=True)
    fast_send = fields.Integer('Fast Send Mode', readonly=True)
    mode = fields.Char('Network Mode', readonly=True)
    rsrp = fields.Integer('RSRP', readonly=True)
    rsrq = fields.Integer('RSRQ', readonly=True)
    rssnr = fields.Integer('RSSNR', readonly=True)
    zpwr = fields.Float('Zipper Voltage (V)', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(""" 
            CREATE OR REPLACE VIEW %s AS (
                WITH sys AS (
                    SELECT
                        utr.lot_id,
                        utr.msg_id,
                        utr.read_time,
                        uto.name AS topic_name,
                        MAX(float_value) FILTER (WHERE uty.name = 'batt') AS batt,
                        MAX(integer_value) FILTER (WHERE uty.name = 'fast_send') AS fast_send,
                        MAX(char_value) FILTER (WHERE uty.name = 'mode') AS mode,
                        MAX(integer_value) FILTER (WHERE uty.name = 'rsrp') AS rsrp,
                        MAX(integer_value) FILTER (WHERE uty.name = 'rsrq') AS rsrq,
                        MAX(integer_value) FILTER (WHERE uty.name = 'rssnr') AS rssnr,
                        MAX(float_value) FILTER (WHERE uty.name = 'zpwr') AS zpwr
                    FROM unit_telemetry_reading utr
                    LEFT JOIN unit_telemetry_topic uto ON uto.id = utr.topic_id
                    LEFT JOIN unit_telemetry_type uty ON uty.id = utr.type_id
                    WHERE uto.name = 'sys'
                    GROUP BY utr.lot_id, utr.msg_id, utr.read_time, uto.name
                )
                SELECT 
                    sys.msg_id AS id,
                    sys.lot_id,
                    sys.msg_id,
                    CASE 
                        WHEN sys.read_time > '2050-01-01' THEN mmh.timestamp 
                        ELSE sys.read_time 
                    END AS tx_date,
                    sys.batt,
                    sys.fast_send,
                    sys.mode,
                    sys.rsrp,
                    sys.rsrq,
                    sys.rssnr,
                    sys.zpwr
                FROM sys
                LEFT JOIN mqtt_message_history mmh ON mmh.id = sys.msg_id
            )
        """ % (self._table,))


# =========================================================================
# 2. OPS: Operational Data Report
# =========================================================================
class UnitTelemetryOpsReport(models.Model):
    _name = 'unit.telemetry.ops.report'
    _description = 'Unit Telemetry Operational Report'
    _auto = False
    _order = 'tx_date desc'

    lot_id = fields.Many2one('stock.lot', string='Serial', readonly=True)
    msg_id = fields.Many2one('mqtt.message.history', string='Message Id', readonly=True)
    tx_date = fields.Datetime(string='Date', readonly=True)
    b_pres = fields.Float(string='Belt Tension Pres (psi)', readonly=True)
    c_hrs = fields.Float(string='Clutch Engaged Hrs', readonly=True)
    c_pres = fields.Float(string='Clutch Pres (psi)', readonly=True)
    c_state = fields.Boolean(string='Clutch Engaged', readonly=True)
    c_tmp = fields.Float(string='Coolant Temp (°F)', readonly=True)
    estp = fields.Integer(string='E-Stop Bits', readonly=True)
    g_tmp = fields.Float(string='Gear Oil Temp (°F)', readonly=True)
    h_state = fields.Boolean(string='Hatch Open', readonly=True)
    h_tmp = fields.Float(string='Hydraulic Temp (°F)', readonly=True)
    load = fields.Float(string='Engine Load (%)', readonly=True)
    m_pres = fields.Float(string='Manifold Pres (psi)', readonly=True)
    rpm = fields.Float(string='Engine RPM', readonly=True)
    spd = fields.Float(string='Wheel Speed', readonly=True)
    v_chg = fields.Float(string='Charging Volt (V)', readonly=True)
    v_crk = fields.Float(string='Cranking Volt (V)', readonly=True)
    v_rst = fields.Float(string='Resting Volt (V)', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                WITH ops AS (
                    SELECT
                        utr.lot_id,
                        utr.msg_id,
                        utr.read_time,
                        uto.name AS topic_name,
                        MAX(float_value) FILTER (WHERE uty.name = 'b_pres') AS b_pres,
                        MAX(float_value) FILTER (WHERE uty.name = 'c_hrs') AS c_hrs,
                        MAX(float_value) FILTER (WHERE uty.name = 'c_pres') AS c_pres,
                        BOOL_OR(bool_value) FILTER (WHERE uty.name = 'c_state') AS c_state,
                        MAX(float_value) FILTER (WHERE uty.name = 'c_tmp') AS c_tmp,
                        MAX(integer_value) FILTER (WHERE uty.name = 'estp') AS estp,
                        MAX(float_value) FILTER (WHERE uty.name = 'g_tmp') AS g_tmp,
                        BOOL_OR(bool_value) FILTER (WHERE uty.name = 'h_state') AS h_state,
                        MAX(float_value) FILTER (WHERE uty.name = 'h_tmp') AS h_tmp,
                        MAX(float_value) FILTER (WHERE uty.name = 'load') AS load,
                        MAX(float_value) FILTER (WHERE uty.name = 'm_pres') AS m_pres,
                        MAX(float_value) FILTER (WHERE uty.name = 'rpm') AS rpm,
                        MAX(float_value) FILTER (WHERE uty.name = 'spd') AS spd,
                        MAX(float_value) FILTER (WHERE uty.name = 'v_chg') AS v_chg,
                        MAX(float_value) FILTER (WHERE uty.name = 'v_crk') AS v_crk,
                        MAX(float_value) FILTER (WHERE uty.name = 'v_rst') AS v_rst
                    FROM unit_telemetry_reading utr
                    LEFT JOIN unit_telemetry_topic uto ON uto.id = utr.topic_id
                    LEFT JOIN unit_telemetry_type uty ON uty.id = utr.type_id
                    WHERE uto.name = 'ops'
                    GROUP BY utr.lot_id, utr.msg_id, utr.read_time, uto.name
                )
                SELECT
                    ops.msg_id AS id,
                    ops.lot_id,
                    ops.msg_id,
                    CASE 
                        WHEN ops.read_time > '2050-01-01' THEN mmh.timestamp 
                        ELSE ops.read_time 
                    END AS tx_date,
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
                FROM ops
                LEFT JOIN mqtt_message_history mmh ON mmh.id = ops.msg_id
            )
        """ % (self._table,))


# =========================================================================
# 3. HRS: Engine Hours Report
# =========================================================================
class UnitTelemetryHrsReport(models.Model):
    _name = 'unit.telemetry.hrs.report'
    _description = 'Unit Telemetry Hour Report'
    _auto = False
    _order = 'tx_date desc'

    lot_id = fields.Many2one('stock.lot', string='Serial', readonly=True)
    msg_id = fields.Many2one('mqtt.message.history', string='Message Id', readonly=True)
    tx_date = fields.Datetime(string='Date', readonly=True)
    hrs = fields.Float(string='Hours', readonly=True, group_operator='max')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
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
                    hrs.hrs
                FROM hrs
                LEFT JOIN mqtt_message_history mmh ON mmh.id = hrs.msg_id
            )
        """ % (self._table,))


# =========================================================================
# 4. GPS: Fleet Location Report
# =========================================================================
class UnitTelemetryGpsReport(models.Model):
    _name = 'unit.telemetry.gps.report'
    _description = 'Unit Telemetry GPS Report'
    _auto = False
    _order = 'tx_date desc'

    lot_id = fields.Many2one('stock.lot', string='Serial', readonly=True)
    msg_id = fields.Many2one('mqtt.message.history', string='Message Id', readonly=True)
    tx_date = fields.Datetime(string='Date', readonly=True)
    lat = fields.Float(string='Latitude', digits=(10, 6), readonly=True)
    long = fields.Float(string='Longitude', digits=(10, 6), readonly=True)
    hpa = fields.Float(string='Accuracy (hpa)', readonly=True)
    sats = fields.Integer(string='Satellites', readonly=True)
    coord_str = fields.Char(string='Coordinates', readonly=True)
    map_link = fields.Char(string='Google Maps Link', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
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
        """ % (self._table,))


# =========================================================================
# 5. DTC: Diagnostic Trouble Codes Report
# =========================================================================
class UnitTelemetryDtcReport(models.Model):
    _name = 'unit.telemetry.dtc.report'
    _description = 'Unit Telemetry DTC Report'
    _auto = False
    _order = 'tx_date desc'

    lot_id = fields.Many2one('stock.lot', string='Serial', readonly=True)
    msg_id = fields.Many2one('mqtt.message.history', string='Message Id', readonly=True)
    tx_date = fields.Datetime(string='Date', readonly=True)
    spn = fields.Integer(string='SPN', readonly=True)
    fmi = fields.Integer(string='FMI', readonly=True)
    addr = fields.Integer(string='Source Address', readonly=True)
    oc = fields.Integer(string='Occurrences', readonly=True, group_operator='sum')
    fault_code = fields.Char(string='Fault Code', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                WITH dtc AS (
                    SELECT
                        utr.lot_id,
                        utr.msg_id,
                        uto.name AS topic_name,
                        MAX(integer_value) FILTER (WHERE uty.name = 'spn') AS spn,
                        MAX(integer_value) FILTER (WHERE uty.name = 'fmi') AS fmi,
                        MAX(integer_value) FILTER (WHERE uty.name = 'addr') AS addr,
                        MAX(integer_value) FILTER (WHERE uty.name = 'oc') AS oc
                    FROM unit_telemetry_reading utr
                    LEFT JOIN unit_telemetry_topic uto ON uto.id = utr.topic_id
                    LEFT JOIN unit_telemetry_type uty ON uty.id = utr.type_id
                    WHERE uto.name = 'dtc'
                    GROUP BY utr.lot_id, utr.msg_id, uto.name
                )
                SELECT
                    dtc.msg_id AS id,
                    dtc.lot_id,
                    dtc.msg_id,
                    mmh.timestamp AS tx_date,
                    dtc.spn,
                    dtc.fmi,
                    dtc.addr,
                    dtc.oc,
                    'SPN ' || dtc.spn || ' / FMI ' || dtc.fmi AS fault_code
                FROM dtc
                LEFT JOIN mqtt_message_history mmh ON mmh.id = dtc.msg_id
                WHERE dtc.spn IS NOT NULL AND dtc.spn != 0
            )
        """ % (self._table,))
```

---

## 2. Views and Menus (`views/unit_telemetry_report_views.xml`)

Replace or extend `custom_addons/unit_telemetry/views/unit_telemetry_report_views.xml` to define the Pivot, Graph, Tree, Search views, and an organized submenu under **Inventory**:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <!-- ================================================================= -->
    <!-- Root Menu for Telemetry Reports                                    -->
    <!-- ================================================================= -->
    <menuitem id="menu_unit_telemetry_reports_root"
              name="Telemetry Reports"
              parent="stock.menu_stock_inventory_control"
              sequence="35"/>

    <!-- ================================================================= -->
    <!-- 1. OPS (Operational Data) Views                                   -->
    <!-- ================================================================= -->
    <record id="view_unit_telemetry_ops_report_tree" model="ir.ui.view">
        <field name="name">unit.telemetry.ops.report.tree</field>
        <field name="model">unit.telemetry.ops.report</field>
        <field name="arch" type="xml">
            <tree create="false" edit="false" delete="false">
                <field name="tx_date"/>
                <field name="lot_id"/>
                <field name="c_state" widget="boolean_toggle"/>
                <field name="rpm"/>
                <field name="load"/>
                <field name="spd"/>
                <field name="b_pres"/>
                <field name="c_pres"/>
                <field name="c_tmp"/>
                <field name="h_tmp"/>
                <field name="g_tmp"/>
                <field name="v_chg"/>
            </tree>
        </field>
    </record>

    <record id="view_unit_telemetry_ops_report_pivot" model="ir.ui.view">
        <field name="name">unit.telemetry.ops.report.pivot</field>
        <field name="model">unit.telemetry.ops.report</field>
        <field name="arch" type="xml">
            <pivot string="Operational Telemetry Pivot" display_quantity="true">
                <field name="tx_date" type="row" interval="day"/>
                <field name="lot_id" type="col"/>
                <field name="rpm" type="measure"/>
                <field name="load" type="measure"/>
                <field name="c_tmp" type="measure"/>
                <field name="h_tmp" type="measure"/>
                <field name="g_tmp" type="measure"/>
                <field name="c_pres" type="measure"/>
                <field name="b_pres" type="measure"/>
            </pivot>
        </field>
    </record>

    <record id="view_unit_telemetry_ops_report_graph" model="ir.ui.view">
        <field name="name">unit.telemetry.ops.report.graph</field>
        <field name="model">unit.telemetry.ops.report</field>
        <field name="arch" type="xml">
            <graph string="Operational Trends" type="line" sample="1">
                <field name="tx_date" interval="day"/>
                <field name="lot_id"/>
                <field name="rpm" type="measure"/>
            </graph>
        </field>
    </record>

    <record id="view_unit_telemetry_ops_report_search" model="ir.ui.view">
        <field name="name">unit.telemetry.ops.report.search</field>
        <field name="model">unit.telemetry.ops.report</field>
        <field name="arch" type="xml">
            <search string="Search Operations">
                <field name="lot_id"/>
                <field name="tx_date"/>
                <filter string="Clutch Engaged" name="filter_clutch_on" domain="[('c_state', '=', True)]"/>
                <filter string="Engine Running (RPM > 500)" name="filter_running" domain="[('rpm', '>', 500)]"/>
                <filter string="Hatch Open" name="filter_hatch_open" domain="[('h_state', '=', True)]"/>
                <group expand="0" string="Group By">
                    <filter string="Serial" name="group_lot" context="{'group_by': 'lot_id'}"/>
                    <filter string="Date (Day)" name="group_date_day" context="{'group_by': 'tx_date:day'}"/>
                    <filter string="Clutch State" name="group_clutch" context="{'group_by': 'c_state'}"/>
                </group>
            </search>
        </field>
    </record>

    <record id="action_unit_telemetry_ops_report" model="ir.actions.act_window">
        <field name="name">Operations (OPS)</field>
        <field name="res_model">unit.telemetry.ops.report</field>
        <field name="view_mode">pivot,graph,tree</field>
        <field name="search_view_id" ref="view_unit_telemetry_ops_report_search"/>
        <field name="context">{}</field>
    </record>

    <menuitem id="menu_unit_telemetry_ops_report"
              name="Operations (OPS)"
              parent="menu_unit_telemetry_reports_root"
              action="action_unit_telemetry_ops_report"
              sequence="10"/>

    <!-- ================================================================= -->
    <!-- 2. HRS (Engine Hours) Views                                       -->
    <!-- ================================================================= -->
    <record id="view_unit_telemetry_hrs_report_tree" model="ir.ui.view">
        <field name="name">unit.telemetry.hrs.report.tree</field>
        <field name="model">unit.telemetry.hrs.report</field>
        <field name="arch" type="xml">
            <tree create="false" edit="false" delete="false">
                <field name="tx_date"/>
                <field name="lot_id"/>
                <field name="hrs"/>
            </tree>
        </field>
    </record>

    <record id="view_unit_telemetry_hrs_report_pivot" model="ir.ui.view">
        <field name="name">unit.telemetry.hrs.report.pivot</field>
        <field name="model">unit.telemetry.hrs.report</field>
        <field name="arch" type="xml">
            <pivot string="Hours Pivot" display_quantity="false">
                <field name="tx_date" type="row" interval="day"/>
                <field name="lot_id" type="col"/>
                <field name="hrs" type="measure"/>
            </pivot>
        </field>
    </record>

    <record id="view_unit_telemetry_hrs_report_graph" model="ir.ui.view">
        <field name="name">unit.telemetry.hrs.report.graph</field>
        <field name="model">unit.telemetry.hrs.report</field>
        <field name="arch" type="xml">
            <graph string="Machine Hours" type="line" sample="1">
                <field name="tx_date" interval="day"/>
                <field name="lot_id"/>
                <field name="hrs" type="measure"/>
            </graph>
        </field>
    </record>

    <record id="view_unit_telemetry_hrs_report_search" model="ir.ui.view">
        <field name="name">unit.telemetry.hrs.report.search</field>
        <field name="model">unit.telemetry.hrs.report</field>
        <field name="arch" type="xml">
            <search string="Search Hours">
                <field name="lot_id"/>
                <field name="tx_date"/>
                <group expand="0" string="Group By">
                    <filter string="Serial" name="group_lot" context="{'group_by': 'lot_id'}"/>
                    <filter string="Date (Day)" name="group_date_day" context="{'group_by': 'tx_date:day'}"/>
                    <filter string="Date (Month)" name="group_date_month" context="{'group_by': 'tx_date:month'}"/>
                </group>
            </search>
        </field>
    </record>

    <record id="action_unit_telemetry_hrs_report" model="ir.actions.act_window">
        <field name="name">Engine Hours (HRS)</field>
        <field name="res_model">unit.telemetry.hrs.report</field>
        <field name="view_mode">pivot,graph,tree</field>
        <field name="search_view_id" ref="view_unit_telemetry_hrs_report_search"/>
    </record>

    <menuitem id="menu_unit_telemetry_hrs_report"
              name="Engine Hours (HRS)"
              parent="menu_unit_telemetry_reports_root"
              action="action_unit_telemetry_hrs_report"
              sequence="20"/>

    <!-- ================================================================= -->
    <!-- 3. GPS (Location) Views                                           -->
    <!-- ================================================================= -->
    <record id="view_unit_telemetry_gps_report_tree" model="ir.ui.view">
        <field name="name">unit.telemetry.gps.report.tree</field>
        <field name="model">unit.telemetry.gps.report</field>
        <field name="arch" type="xml">
            <tree create="false" edit="false" delete="false">
                <field name="tx_date"/>
                <field name="lot_id"/>
                <field name="coord_str"/>
                <field name="sats"/>
                <field name="hpa"/>
                <field name="map_link" widget="url" text="Open in Google Maps"/>
            </tree>
        </field>
    </record>

    <record id="view_unit_telemetry_gps_report_pivot" model="ir.ui.view">
        <field name="name">unit.telemetry.gps.report.pivot</field>
        <field name="model">unit.telemetry.gps.report</field>
        <field name="arch" type="xml">
            <pivot string="GPS Fix Pivot" display_quantity="true">
                <field name="tx_date" type="row" interval="day"/>
                <field name="lot_id" type="col"/>
                <field name="sats" type="measure"/>
                <field name="hpa" type="measure"/>
            </pivot>
        </field>
    </record>

    <record id="view_unit_telemetry_gps_report_search" model="ir.ui.view">
        <field name="name">unit.telemetry.gps.report.search</field>
        <field name="model">unit.telemetry.gps.report</field>
        <field name="arch" type="xml">
            <search string="Search GPS">
                <field name="lot_id"/>
                <field name="tx_date"/>
                <group expand="0" string="Group By">
                    <filter string="Serial" name="group_lot" context="{'group_by': 'lot_id'}"/>
                    <filter string="Date (Day)" name="group_date_day" context="{'group_by': 'tx_date:day'}"/>
                </group>
            </search>
        </field>
    </record>

    <record id="action_unit_telemetry_gps_report" model="ir.actions.act_window">
        <field name="name">GPS Tracking</field>
        <field name="res_model">unit.telemetry.gps.report</field>
        <field name="view_mode">tree,pivot</field>
        <field name="search_view_id" ref="view_unit_telemetry_gps_report_search"/>
    </record>

    <menuitem id="menu_unit_telemetry_gps_report"
              name="GPS Tracking"
              parent="menu_unit_telemetry_reports_root"
              action="action_unit_telemetry_gps_report"
              sequence="30"/>

    <!-- ================================================================= -->
    <!-- 4. DTC (Diagnostic Trouble Codes) Views                           -->
    <!-- ================================================================= -->
    <record id="view_unit_telemetry_dtc_report_tree" model="ir.ui.view">
        <field name="name">unit.telemetry.dtc.report.tree</field>
        <field name="model">unit.telemetry.dtc.report</field>
        <field name="arch" type="xml">
            <tree create="false" edit="false" delete="false" decoration-danger="oc &gt; 1">
                <field name="tx_date"/>
                <field name="lot_id"/>
                <field name="spn"/>
                <field name="fmi"/>
                <field name="addr"/>
                <field name="oc"/>
                <field name="fault_code"/>
            </tree>
        </field>
    </record>

    <record id="view_unit_telemetry_dtc_report_pivot" model="ir.ui.view">
        <field name="name">unit.telemetry.dtc.report.pivot</field>
        <field name="model">unit.telemetry.dtc.report</field>
        <field name="arch" type="xml">
            <pivot string="DTC Fault Pivot" display_quantity="true">
                <field name="spn" type="row"/>
                <field name="fmi" type="row"/>
                <field name="lot_id" type="col"/>
                <field name="oc" type="measure"/>
            </pivot>
        </field>
    </record>

    <record id="view_unit_telemetry_dtc_report_graph" model="ir.ui.view">
        <field name="name">unit.telemetry.dtc.report.graph</field>
        <field name="model">unit.telemetry.dtc.report</field>
        <field name="arch" type="xml">
            <graph string="Fault Code Frequency" type="bar" sample="1">
                <field name="fault_code"/>
                <field name="oc" type="measure"/>
            </graph>
        </field>
    </record>

    <record id="view_unit_telemetry_dtc_report_search" model="ir.ui.view">
        <field name="name">unit.telemetry.dtc.report.search</field>
        <field name="model">unit.telemetry.dtc.report</field>
        <field name="arch" type="xml">
            <search string="Search DTCs">
                <field name="lot_id"/>
                <field name="spn"/>
                <field name="fmi"/>
                <field name="addr"/>
                <group expand="0" string="Group By">
                    <filter string="SPN" name="group_spn" context="{'group_by': 'spn'}"/>
                    <filter string="Serial" name="group_lot" context="{'group_by': 'lot_id'}"/>
                    <filter string="Source Address" name="group_addr" context="{'group_by': 'addr'}"/>
                    <filter string="Date (Day)" name="group_date_day" context="{'group_by': 'tx_date:day'}"/>
                </group>
            </search>
        </field>
    </record>

    <record id="action_unit_telemetry_dtc_report" model="ir.actions.act_window">
        <field name="name">Diagnostic Codes (DTC)</field>
        <field name="res_model">unit.telemetry.dtc.report</field>
        <field name="view_mode">pivot,graph,tree</field>
        <field name="search_view_id" ref="view_unit_telemetry_dtc_report_search"/>
    </record>

    <menuitem id="menu_unit_telemetry_dtc_report"
              name="Fault Codes (DTC)"
              parent="menu_unit_telemetry_reports_root"
              action="action_unit_telemetry_dtc_report"
              sequence="40"/>

    <!-- ================================================================= -->
    <!-- 5. SYS (System Health) - Updated Menu Placement                   -->
    <!-- ================================================================= -->
    <record id="view_unit_telemetry_report_tree" model="ir.ui.view">
        <field name="name">view.unit.telemetry.report.tree</field>
        <field name="model">unit.telemetry.report</field>
        <field name="arch" type="xml">
            <tree create="false" edit="false" delete="false">
                <field name="tx_date"/>
                <field name="lot_id"/>
                <field name="batt"/>
                <field name="fast_send"/>
                <field name="mode"/>
                <field name="rsrp"/>
                <field name="rsrq"/>
                <field name="rssnr"/>
                <field name="zpwr"/>
            </tree>
        </field>
    </record>

    <record id="view_unit_telemetry_report_pivot" model="ir.ui.view">
        <field name="name">view.unit.telemetry.report.pivot</field>
        <field name="model">unit.telemetry.report</field>
        <field name="arch" type="xml">
            <pivot string="System Health Pivot" display_quantity="true">
                <field name="tx_date" type="row" interval="day"/>
                <field name="lot_id" type="col"/>
                <field name="batt" type="measure"/>
                <field name="rsrp" type="measure"/>
                <field name="rsrq" type="measure"/>
                <field name="rssnr" type="measure"/>
                <field name="zpwr" type="measure"/>
            </pivot>
        </field>
    </record>

    <record id="view_unit_telemetry_report_graph" model="ir.ui.view">
        <field name="name">view.unit.telemetry.report.graph</field>
        <field name="model">unit.telemetry.report</field>
        <field name="arch" type="xml">
            <graph string="Modem Battery Trends" type="line" sample="1">
                <field name="tx_date" interval="day"/>
                <field name="lot_id"/>
                <field name="batt" type="measure"/>
            </graph>
        </field>
    </record>

    <record id="view_unit_telemetry_report_search" model="ir.ui.view">
        <field name="name">view.unit.telemetry.report.search</field>
        <field name="model">unit.telemetry.report</field>
        <field name="arch" type="xml">
            <search string="Search System Health">
                <field name="lot_id"/>
                <field name="tx_date"/>
                <field name="mode"/>
                <group expand="0" string="Group By">
                    <filter string="Serial" name="groupby_lot" context="{'group_by': 'lot_id'}"/>
                    <filter string="Date" name="groupby_date" context="{'group_by': 'tx_date:day'}"/>
                    <filter string="Network Mode" name="groupby_mode" context="{'group_by': 'mode'}"/>
                </group>
            </search>
        </field>
    </record>

    <record id="unit_telemetry_report_action" model="ir.actions.act_window">
        <field name="name">System Health (SYS)</field>
        <field name="res_model">unit.telemetry.report</field>
        <field name="search_view_id" ref="view_unit_telemetry_report_search"/>
        <field name="view_mode">pivot,graph,tree</field>
    </record>

    <menuitem id="unit_telemetry_report_menu"
              name="System Health (SYS)"
              parent="menu_unit_telemetry_reports_root"
              action="unit_telemetry_report_action"
              sequence="50"/>

</odoo>
```

---

## 3. Security Access Rights (`security/ir.model.access.csv`)

Add read access for the new reporting models to `custom_addons/unit_telemetry/security/ir.model.access.csv`:

```csv
access_unit_telemetry_ops_report,access_unit_telemetry_ops_report,model_unit_telemetry_ops_report,stock.group_stock_user,1,0,0,0
access_unit_telemetry_hrs_report,access_unit_telemetry_hrs_report,model_unit_telemetry_hrs_report,stock.group_stock_user,1,0,0,0
access_unit_telemetry_gps_report,access_unit_telemetry_gps_report,model_unit_telemetry_gps_report,stock.group_stock_user,1,0,0,0
access_unit_telemetry_dtc_report,access_unit_telemetry_dtc_report,model_unit_telemetry_dtc_report,stock.group_stock_user,1,0,0,0
```

---

## 4. Bug Fixes & Data Cleanups

In your testing notes, you diagnosed two specific issues with the existing setup. Here are the recommended fixes:

### A. Boolean Data Type Misalignment
In `custom_addons/unit_telemetry/data/unit_telemetry_data.xml`:
Lines 159 and 189 set `<field name="data_type">boolean</field>` for `c_state` and `h_state`, whereas `unit.telemetry.type.data_type` Selection uses `'bool'`.

**Fix in XML:**
Change `boolean` to `bool` in `data/unit_telemetry_data.xml`:
```xml
<!-- Operational Data Types -->
<record id="unit_telemetry_type_c_state" model="unit.telemetry.type">
    <field name="description">Clutch Engaged</field>
    <field name="data_type">bool</field>
    <field name="name">c_state</field>
    <field name="topic_id" ref="unit_telemetry.unit_telemetry_topic_ops"/>
</record>
...
<record id="unit_telemetry_type_h_state" model="unit.telemetry.type">
    <field name="description">Hatch Open</field>
    <field name="data_type">bool</field>
    <field name="name">h_state</field>
    <field name="topic_id" ref="unit_telemetry.unit_telemetry_topic_ops"/>
</record>
```

Also in `views/unit_telemetry_views.xml` (line 142), adjust:
```xml
- <field name="bool_value" attrs="{'invisible': [('data_type', '!=', 'boolean')]}"/>
+ <field name="bool_value" attrs="{'invisible': [('data_type', '!=', 'bool')]}"/>
```

**SQL Fix for Existing Records in Database:**
```sql
UPDATE unit_telemetry_type SET data_type = 'bool' WHERE data_type = 'boolean';

UPDATE unit_telemetry_reading 
SET value = 'True', bool_value = TRUE 
WHERE id IN (
    SELECT utr.id
    FROM unit_telemetry_reading utr
    JOIN unit_telemetry_type uty ON uty.id = utr.topic_id
    JOIN mqtt_message_history mmh ON mmh.id = utr.msg_id
    WHERE uty.name = 'c_state'
      AND (utr.value = 'False' OR utr.bool_value IS NOT TRUE)
      AND mmh.payload::json->>'c_state' = '1'
);
```

### B. Cellular Modem Date Errors (> Year 2050 / 2080)
The SQL views defined above incorporate the date fallback directly:
```sql
CASE 
    WHEN utr.read_time > '2050-01-01' THEN mmh.timestamp 
    ELSE utr.read_time 
END AS tx_date
```
This ensures your reports, pivots, and charts are automatically protected even if future messages arrive with bad modem dates.

To clean up the historical records in `unit_telemetry_reading`:
```sql
UPDATE unit_telemetry_reading
SET read_time = mqtt_message_history.timestamp
FROM mqtt_message_history
WHERE mqtt_message_history.id = unit_telemetry_reading.msg_id
  AND unit_telemetry_reading.read_time > '2050-01-01';
```

---

## 5. Upgrade Instructions

Once you apply the code changes above, upgrade the module to create the SQL views, register security access, and load the new menus:

```bash
python odoo/odoo-bin -c odoo.conf -d <db_name> -u unit_telemetry --stop-after-init
```
