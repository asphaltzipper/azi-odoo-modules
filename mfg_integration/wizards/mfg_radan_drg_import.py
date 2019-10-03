# -*- coding: utf-8 -*-

from lxml import etree
import base64
import cStringIO
from PIL import Image, ImageChops

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class MfgRadanDrgFile(models.TransientModel):
    _name = 'mfg.radan.drg.file'
    _description = 'Radan Drawing File Upload'

    _sql_constraints = [('filename_import_id_uniq', 'unique (filename, import_id)', """File name must be unique."""), ]

    data_file = fields.Binary(
        string='Radan Drawing File',
        required=True,
        help='Must be a Radan .drg file type')

    filename = fields.Char(
        string="Filename")


class MfgRadanDrgImport(models.TransientModel):
    _name = 'mfg.radan.drg.import'
    _description = 'Import Multiple Radan Drawings'

    drg_file_ids = fields.Many2many(comodel_name="ir.attachment", string="Documents")
    import_files = fields.Char("Upload")

    def trim_image(self, image):
        data = base64.b64decode(image)
        file_input = cStringIO.StringIO(data)
        im = Image.open(file_input)

        # trim the image
        bg = Image.new(im.mode, im.size, im.getpixel((0, 0)))
        diff = ImageChops.difference(im, bg)
        bbox = diff.getbbox()
        if bbox:
            im = im.crop(bbox)

        # resize the image
        height = 90
        w_ratio = float(im.size[0]) / float(im.size[1])
        im = im.resize((int(w_ratio*height), height), Image.ANTIALIAS)

        buf = cStringIO.StringIO()
        im.save(buf, format="PNG")
        img_str = base64.b64encode(buf.getvalue())
        return img_str

    @api.multi
    def action_import(self):
        """Load manufacturing work data from the uploaded Radan files."""

        # radan compound document namespace for .drg files
        ns = "{http://www.radan.com/ns/rcd}"
        ns_any = ".//" + ns
        ns_abs = "/" + ns

        product_obj = self.env['product.product']
        work_header_obj = self.env['mfg.work.header']
        work_detail_obj = self.env['mfg.work.detail']

        for drg in self.drg_file_ids:

            # Decode the file data
            data = base64.b64decode(drg.datas)
            file_input = cStringIO.StringIO(data)

            try:
                tree = etree.parse(file_input)
                root = tree.getroot()
            except Exception:
                raise UserError(_("Not a valid file!"))
            assert root.tag == "{http://www.radan.com/ns/rcd}RadanCompoundDocument", "Not a valid file!"

            e_material = tree.find(ns_any + "Material")
            e_sheet_x = tree.find(ns_any + "SheetX")
            e_sheet_y = tree.find(ns_any + "SheetY")
            e_thickness = tree.find(ns_any + "Thickness")
            e_utilization = tree.find(ns_any + "Utilization")
            e_runtime_s = tree.find(ns_any + "RunTimeS")
            e_number_sheets = tree.find(ns_any + "NumberSheets")

            sheet_count = e_number_sheets is not None and int(e_number_sheets.text) or 1

            header = work_header_obj.create({
                'name': drg.name,
                'file_name': drg.name,
                'state': 'imported',
                'work_user_id': self.env.user.id,
                'total_hours': 0.0,
                'misc_hours': 0.0,
                'material': e_material is not None and e_material.text or False,
                'thickness': e_thickness is not None and e_thickness.text or False,
                'sheet_x': e_sheet_x is not None and float(e_sheet_x.text) or 0.0,
                'sheet_y': e_sheet_y is not None and float(e_sheet_y.text) or 0.0,
                'utilization': e_utilization is not None and float(e_utilization.text[0:-1]) or 0.0,
                'runtime_s': e_runtime_s is not None and float(e_runtime_s.text.split()[0]) or 0.0,
                'number_sheets': sheet_count,
            })

            e_thumbnail = tree.find(ns_any + "Thumbnail")
            image = e_thumbnail is not None and e_thumbnail.text or False
            image = self.trim_image(image)
            header.thumbnail = image

            # get part details and create work records
            parts_data = []
            parts = tree.find(ns_any + "Parts")
            if parts is not None:
                for part in parts:
                    parts_data.append({
                        'file_name': part.find(".//" + ns + "Attr[@name='File name']").attrib['value'],
                        'num_off': part.find(".//" + ns + "NumOff").text,
                        'part_num': part.attrib['num'],
                        'bbox_x': part.find(".//" + ns + "BoundingBoxX").text,
                        'bbox_y': part.find(".//" + ns + "BoundingBoxY").text,
                    })
            else:
                symbols = tree.find(ns_any + "QuotationInfo" + ns_abs + "Info[@name='Contained Symbols']")
                for symbol in symbols:
                    parts_data.append({
                        'file_name': symbol.attrib['name'],
                        'num_off': int(symbol.attrib['count']),
                        'part_num': 0,
                        'bbox_x': 0.0,
                        'bbox_y': 0.0,
                    })
            for p in parts_data:
                product = product_obj.search([('mfg_code', '=', p['file_name'])])
                values = {
                    'import_mfg_code': p['file_name'],
                    'import_production_code': False,
                    'part_num': float(p['part_num']),
                    'import_quantity': float(p['num_off']),
                    'bbox_x': float(p['bbox_x']),
                    'bbox_y': float(p['bbox_y']),
                    'header_id': header.id,
                    'product_id': product.id or False,
                    'actual_quantity': float(p['num_off']) * sheet_count,
                }
                work_detail_obj.create(values)

        return {}
