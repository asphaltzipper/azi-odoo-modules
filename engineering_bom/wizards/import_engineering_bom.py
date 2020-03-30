# -*- coding: utf-8 -*-

from lxml import etree
import base64
import io

from odoo import api, models, fields, _
from odoo.exceptions import UserError


def find_text(node, path, out_type=str, true_condition="TRUE"):
    tag = node.find(path)
    if tag is None:
        return False
    if out_type == bool:
        return tag.text.upper() == true_condition
    if out_type == str:
        return tag.text.encode('utf-8')
    return out_type(tag.text)


class EngBomImport(models.TransientModel):
    _name = 'engineering.bom.import'
    _description = 'Import Engineering BOM'

    data_file = fields.Binary(
        string='BOM Data File',
        required=True,
        help="XML file from AZI-SWCustomProperties")

    filename = fields.Char(
        string="Filename")

    batch_id = fields.Many2one(
        comodel_name='engineering.bom.batch',
        string="Engineering BOM Batch",
        readonly=True,
        required=True,
        ondelete='cascade')

    @api.model
    def default_get(self, fields):
        res = super(EngBomImport, self).default_get(fields)
        res['batch_id'] = self._context.get('active_id')
        return res

    @api.multi
    def action_import(self):
        """Load, extract and write BOM data to batch"""

        product_obj = self.env['product.product']
        comp_obj = self.env['engineering.bom.component']
        adjacency_obj = self.env['engineering.bom.adjacency']

        # Decode the file data
        data = base64.b64decode(self.data_file)
        file_input = io.BytesIO(data)

        # parse xml data
        try:
            tree = etree.parse(file_input)
            root = tree.getroot()
        except Exception:
            raise UserError(_("Not a valid file!"))
        assert root.tag == "bom_scan", "Not a valid file!"
        e_comps = root.findall("./config")
        e_adjacencies = root.findall("./adjacency")

        if not len(e_comps):
            raise UserError(_("No part data found"))

        # clear data
        self.batch_id.adjacency_ids.unlink()
        self.batch_id.comp_ids.unlink()
        self.batch_id.part_diff_ids.unlink()
        self.batch_id.bom_diff_ids.unlink()
        self.batch_id.bom_line_diff_ids.unlink()

        # create component records
        for part in e_comps:
            delimiter = '.'
            eng_code = find_text(part, "./PartNum") or ""
            eng_rev = find_text(part, "./Revision") or '-0'
            default_code = "{}{}{}".format(eng_code, delimiter, eng_rev)
            values = {
                'batch_id': self.batch_id.id,
                'name': default_code,
                'filename': find_text(part, "./filename", str),
                'config_name': find_text(part, "./configname", str),
                'image': find_text(part, "./Image", str),
                'part_num': find_text(part, "./PartNum", str),
                'part_rev': find_text(part, "./Revision", str),
                'description': find_text(part, "./Description", str),
                'material_spec': find_text(part, "./Material", str),
                'material_pn': find_text(part, "./MaterialPn", str),
                'rm_qty': find_text(part, "./ChildQty", float),
                'route_template_name': find_text(part, "./RouteTemplate", str),
                'part_type': find_text(part, "./Type", str),
                'make': find_text(part, "./Make", str),
                'coating': find_text(part, "./Coating", str),
                'finish': find_text(part, "./Finish", str),
                'uom': find_text(part, "./Uom", str),
                'alt_qty': find_text(part, "./AltQty", float),
                'cutting_length_outer': find_text(part, "./CuttingLengthOuter", float),
                'cutting_length_inner': find_text(part, "./CuttingLengthInner", float),
                'cut_out_count': find_text(part, "./CutOutCount", int),
                'bend_count': find_text(part, "./BendCount", int),
            }
            comp_obj.create(values)

        # create adjacency records
        for rel in e_adjacencies:
            domain = [
                ('batch_id', '=', self.batch_id.id),
                ('filename', '=', find_text(rel, "./pname")),
                ('config_name', '=', find_text(rel, "./pconfig")),
            ]
            parent_part = self.batch_id.comp_ids.search(domain)
            domain = [
                ('batch_id', '=', self.batch_id.id),
                ('filename', '=', find_text(rel, "./cname")),
                ('config_name', '=', find_text(rel, "./cconfig")),
            ]
            child_part = self.batch_id.comp_ids.search(domain)
            values = {
                'batch_id': self.batch_id.id,
                'parent_comp_id': parent_part.id,
                'child_comp_id': child_part.id,
                'count': find_text(rel, "./adjcount", int)
            }
            adjacency_obj.create(values)

        self.batch_id.state = 'imported'

        return {}
