<?xml version="1.0" encoding="utf-8"?>
<openerp>
    <data>

        <record id="view_procurement_run_wizard" model="ir.ui.view">
            <field name="name">Run Procurment(s)</field>
            <field name="model">procurement.order.run</field>
            <field name="arch" type="xml">
                <form string="Parameters">
                    <group>
                        <label string="Wizard sets selected procurement order(s) to running state."/>
                    </group>
                    <footer>
                        <button name="procurement_run" string="Run Procurement(s)" type="object"  class="oe_highlight"  />
                        or
                        <button string="Cancel" class="oe_link" special="cancel" />
                    </footer>
                </form>
            </field>
        </record>

        <record id="run_selected_procurements_action" model="ir.actions.act_window">
            <field name="name">Run Procurement(s)</field>
            <field name="type">ir.actions.act_window</field>
            <field name="res_model">procurement.order.run</field>
            <field name="src_model">procurement.order</field>
            <!--<field name="model_id" ref="model_procurement_order" />
            <field name="view_type">tree</field>-->
            <field name="view_mode">tree</field>
            <field name="target">new</field>
            <!--<field name="view_id" ref="procurement.procurement_tree_view" />
            <field name="target">new</field>
            <field name="state">code</field>
            <field name="code">action = self.run(cr, uid, context.get('active_ids',[]), context=context)</field>-->
        </record>

        <!--<act_window name="Run Procurement(s)"
            res_model="procurement_order.run"
            src_model="procurement.order"
            view_mode="tree"
            target="current"
            key2="client_action_multi"
            id="run_selected_procurements_action"/>-->

        <!--<act_window id="" />-->
        <record model="ir.values" id="run_selected_procurements_menu">
            <field name="key2">client_action_multi</field>
            <field name="model">procurement.order</field>
            <field name="name">run_selected_procurements</field>
            <field name="value" eval="'ir.actions.act_window,%d'%run_selected_procurements_action"/>
            <!--<field name="object" eval="True"/>-->
        </record>

    </data>
</openerp>
