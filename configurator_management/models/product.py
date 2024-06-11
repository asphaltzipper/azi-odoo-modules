from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def copy(self, default=None):
        if not default:
            default = {}
        res = super(ProductTemplate, self).copy(default=default)

        # copy active boms
        if self.config_ok:
            old_boms = self.env['mrp.bom'].search([
                ('product_tmpl_id', '=', self.id),
                ('product_id', '=', False),
            ])
            for bom in old_boms:
                defaults = {
                    'product_tmpl_id': res.id,
                }
                bom.copy(default=defaults)

        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'

    config_code = fields.Char(
        string="Config Code",
        compute='_get_config_code',
    )

    @api.model
    def _get_config_code(self):
        for prod in self:
            if prod.config_ok:
                # independent_attrs = prod.config_step_line_ids.filtered(lambda x: x.name != 'Depends').mapped(
                #     'attribute_line_ids.attribute_id').sorted(key=lambda x: x.name)
                # variant = prod.attribute_value_ids.get_variant_code(independent_attrs)
                variant = prod.attribute_value_ids.get_variant_code()
                code = "%s (%s)" % (prod.name, variant)
            else:
                code = prod.name
            prod.config_code = code

    def name_get(self):
        def _name_get(d):
            myname = d.get('name', '')
            code = self._context.get('display_default_code', True) and d.get('default_code', False) or False
            if code:
                myname = '[%s] %s' % (code, myname)
            return d['id'], myname

        result = super(ProductProduct, self).name_get()
        config_ok_ids = self.filtered(lambda x: x.config_ok).ids
        if config_ok_ids:
            for i in range(len(result) - 1):
                if result[i][0] in config_ok_ids:
                    prod = self.browse(result[i][0])
                    independent_attrs = prod.config_step_line_ids.filtered(lambda x: x.name != 'Depends').mapped(
                        'attribute_line_ids.attribute_id').sorted(key=lambda x: x.name)
                    variant = prod.product_template_attribute_value_ids._variant_name(independent_attrs)
                    name = "%s (%s)" % (prod.name, variant)
                    mydict = {
                        'id': prod.id,
                        'name': name,
                        'default_code': prod.default_code,
                    }
                    new_res = _name_get(mydict)
                    result[i] = new_res
        return result
