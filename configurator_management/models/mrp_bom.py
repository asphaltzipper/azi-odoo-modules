from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    @api.constrains('product_id', 'product_tmpl_id', 'bom_line_ids')
    def _check_product_recursion(self):
        for bom in self:
                if bom.bom_line_ids.filtered(
                    lambda x: x.product_id == bom.product_id
                ):
                    raise ValidationError(_(
                        "BoM Loop Error: component product %s same as parent product.",
                        bom.display_name
                    ))

    @api.constrains('product_id', 'config_ok')
    def _check_product_required(self):
        # require product variant, unless this is a configurator bom
        for bom in self:
            if not bom.product_id and bom.active:
                raise ValidationError(_("Product Variant is required"))


    def button_update_config_sets(self):
        # update configuration sets from product.template attribute value products
        self.ensure_one()
        if not self.config_ok or self.product_id:
            raise ValidationError(_(
                "We can only reconfigure a BOM that is configurable, and has no "
                "product variant assigned"
            ))

        # validate attribute values and products
        # bom_product_template_attribute_value_ids
        tmpl_values = self.possible_product_template_attribute_value_ids
        values = tmpl_values.mapped("product_attribute_value_id")
        values_missing_products = values.filtered(
            lambda x: not x.product_id and not x.no_bom_component)
        if values_missing_products:
            error_value_names = [f"{x.attribute_id.name}/{x.name}"
                                 for x in values_missing_products]
            raise ValidationError(_(
                "The following attribute values require a related product:\n\n%s",
                "\n".join(error_value_names)
            ))
        values = values.filtered(lambda x: x.product_id)

        # enforce a one-to-one relationship between product.attribute.value and
        # product.product for values assigned to this product.template
        # i.e. each attribute value on this template must have a unique related product
        attr_products = values.mapped("product_id")
        if len(attr_products) < len(values):
            error_value_names = []
            for attr_prod in attr_products:
                dup_prod_values = values.filtered(lambda x: x.product_id==attr_prod)
                if len(dup_prod_values) > 1:
                    error_value_names.append(
                        "%s:\n- %s" % (
                            attr_prod.name,
                            "\n- ".join(dup_prod_values.mapped("name")),
                        )
                    )
            raise ValidationError(_(
                "Related Product must be unique among attribute values on a given "
                "Product Template:\n\n%s",
                "\n\n".join(error_value_names)
            ))
        product_value_map = {x.product_id.id: x for x in values if x.product_id}
        product_tmpl_value_map = {
            x.product_attribute_value_id.product_id.id: x
            for x in tmpl_values if x.product_attribute_value_id.product_id
        }

        # add or delete bom lines to match attribute value products
        # we never update product_qty on existing bom lines because the user may have
        # changed those
        lines_to_delete = self.bom_line_ids.filtered(
            lambda x: x.product_id not in attr_products)
        lines_to_delete.unlink()
        products_to_add = attr_products - self.bom_line_ids.mapped("product_id")
        for prod in products_to_add:
            value = product_value_map.get(prod.id)
            self.bom_line_ids.create({
                "bom_id": self.id,
                "product_id": prod.id,
                "product_qty": value.product_qty or 1.0,
            })

        # check for multi-value bom line configuration records
        all_configs = self.env['mrp.bom.line.configuration'].search([])
        multi_value_configs = all_configs.filtered(lambda x: len(x.value_ids) > 1)
        if multi_value_configs:
            error_message = _("Automatically assigning BOM configuration sets is not"
                              "supported when multiple attribute values have been"
                              "assigned to a BOM Line Configuration:\n\n")
            for config in multi_value_configs:
                error_message += _(
                    "%s: %s\n",
                    config.config_set_id.name,
                    config.mapped("value_ids.name")
                )
            raise ValidationError(error_message)

        # check for multi-config bom line configuration set records
        all_sets = self.env['mrp.bom.line.configuration.set'].search([])
        multi_config_sets = all_sets.filtered(lambda x: len(x.configuration_ids) > 1)
        if multi_config_sets:
            error_message = _(
                "Automatically assigning BOM Line Configuration Sets is not supported "
                "when multiple Configuration Lines have been assigned to a BOM Line "
                "Configuration Set:\n\n%s",
                "\n".join(multi_config_sets.mapped("name")),
            )
            raise ValidationError(error_message)

        # add missing config sets
        all_configs = self.env['mrp.bom.line.configuration'].search([])
        values_to_add = values - all_configs.mapped("value_ids")
        for value in values_to_add:
            self.env['mrp.bom.line.configuration.set'].create({
                "name": "%s/%s" % (value.attribute_id.name, value.name),
                "configuration_ids": [(0, 0, {
                    "value_ids": [(6, 0, [value.id])],
                })],
            })

        # clear all bom line configuration sets
        self.bom_line_ids.write({'config_set_id': False})

        # populate config fields on bom lines
        # (both the built-in and product_configurator fields)
        sequence = 1
        all_sets = self.env['mrp.bom.line.configuration.set'].search([])
        for line in self.bom_line_ids.sorted(lambda x: x.product_id.product_tmpl_id.name):
            value = product_value_map[line.product_id.id]
            config_set = all_sets.filtered(lambda x: x.configuration_ids.value_ids == value)
            tmpl_value = product_tmpl_value_map.get(line.product_id.id)
            line.write({
                "bom_product_template_attribute_value_ids": [(6, 0, [tmpl_value.id])],
                "config_set_id": config_set[:1].id,
                "sequence": sequence,
            })
            sequence += 1

        return True
