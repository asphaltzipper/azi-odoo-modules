from odoo import fields, models, api, _
import logging


_logger = logging.getLogger(__name__)


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    # null sorts last??!!
    # the default is null??!!!
    # I thought integer fields could not be null?
    # okay, make the default one
    sequence = fields.Integer(default=1)

    def ext_explode(self, product_id, quantity, deep=False):
        """
            Explode the BOM
            Callable from OdooRPC
            Will do a full depth explode when deep=True
            Deep explode stops descending into the BOM when purchased items are encountered
        """
        product = self.env['product.product'].browse(product_id)
        # import pdb
        # pdb.set_trace()
        boms, lines = self.explode(product, quantity)

        if deep:
            comp_boms = []
            for line in lines:
                prod = line[0].product_id
                # if prod.display_name == '[X015788.-0] Wing Nut Weldment, 3/8':
                #     import pdb
                #     pdb.set_trace()
                if prod.mrp_area_ids and prod.mrp_area_ids[0].supply_method in ['manufacture', 'phantom']:
                    bom = self._bom_find(product=prod)
                    if bom:
                        comp_boms.append((bom, prod, line[1]['qty']))
            while comp_boms:
                current_bom, current_prod, current_qty = comp_boms[0]
                comp_boms = comp_boms[1:]
                _logger.info("Exploding component BOM for %s" % current_prod.display_name)
                # if current_prod.display_name == '[X015788.-0] Wing Nut Weldment, 3/8':
                #     import pdb
                #     pdb.set_trace()
                new_boms, new_lines = current_bom.explode(current_prod, current_qty)
                boms += new_boms
                lines += new_lines
                for line in new_lines:
                    prod = line[0].product_id
                    # if prod.display_name == '[X015788.-0] Wing Nut Weldment, 3/8':
                    #     import pdb
                    #     pdb.set_trace()
                    if prod.mrp_area_ids and prod.mrp_area_ids[0].supply_method in ['manufacture', 'phantom']:
                        bom = self._bom_find(product=prod)
                        if bom:
                            comp_boms.append((bom, prod, line[1]['qty']))

        boms_done = []
        for bom in boms:
            bom_row = (bom[0].id, {
                'product_id': bom[1]['product'].id,
                'parent_line_id': bom[1]['parent_line'] and bom[1]['parent_line'].id or False,
                'qty': bom[1]['qty'],
                'original_qty': bom[1]['original_qty'],
            })
            boms_done.append(bom_row)
        lines_done = []
        for line in lines:
            line_row = (line[0].id, {
                'product_id': line[1]['product'].id,
                'parent_line_id': line[1]['parent_line'] and line[1]['parent_line'].id or False,
                'qty': line[1]['qty'],
                'original_qty': line[1]['original_qty'],
            })
            lines_done.append(line_row)
        return boms_done, lines_done


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    @api.one
    @api.depends('product_id')
    def _compute_has_attachments(self):
        nbr_attach = self.env['ir.attachment'].search_count([
            '|',
            '&', ('res_model', '=', 'product.product'), ('res_id', '=', self.product_id.id),
            '&', ('res_model', '=', 'product.template'), ('res_id', '=', self.product_id.product_tmpl_id.id)])
        self.has_attachments = bool(nbr_attach)

    @api.multi
    def action_see_attachments(self):
        domain = [
            '|',
            '&', ('res_model', '=', 'product.product'), ('res_id', '=', self.product_id.id),
            '&', ('res_model', '=', 'product.template'), ('res_id', '=', self.product_id.product_tmpl_id.id)]
        attachment_view = self.env.ref('attachment_priority.view_ir_attachment_kanban')
        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': attachment_view.id,
            'views': [(attachment_view.id, 'kanban'), (False, 'form')],
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _('''<p class="o_view_nocontent_smiling_face">
                            Upload files to your product
                        </p><p>
                            Use this feature to store any files, like drawings or specifications.
                        </p>'''),
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % ('product.product', self.product_id.id)
        }
