from collections import defaultdict
from odoo import api, models


class ReportMrpBomHistory(models.AbstractModel):
    _name = "report.mrp_bom_history.report_bom_history"
    _description = "BOM History Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('mrp_bom_history.report_bom_history')
        product_children = defaultdict(list)
        history_lines = self.env['mrp.bom.history.line'].search([('production_id', 'in', docids)])
        history_lines_dict = history_lines.read(['id', 'parent_product_id', 'product_id', 'product_qty', 'product_uom_id'])
        for line in history_lines_dict:
            parent_id = line['parent_product_id']
            product_children[parent_id].append(line)

        def build_product_hierarchy(parent_product_id, level=0, exist=None):
            if exist is None:
                exist = set()
            result = []
            for product_child in product_children.get(parent_product_id, []):
                if product_child['id'] in exist:
                    continue
                exist.add(product_child['id'])
                product_child_data = product_child.copy()
                product_child_data['level'] = level
                result.append(product_child_data)
                result.extend(build_product_hierarchy(product_child['product_id'], level + 1, exist))
            return result

        all_parents = set(line['parent_product_id'] for line in history_lines_dict)
        all_children = set(line['product_id'] for line in history_lines_dict)
        root_parents = all_parents - all_children
        hierarchy = []
        exist = set()
        for root in root_parents:
            hierarchy.extend(build_product_hierarchy(root, 0, exist))
        docs = {
            'lines': hierarchy,
        }
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docs,
        }
        return docargs
