from openerp import http, _
from openerp.http import request
import datetime

class StockBarcodeController(http.Controller):

    @http.route('/proc_barcode/scan_from_main_menu', type='json', auth='user')
    def main_menu(self, barcode, **kw):
        if barcode:
            product = request.env['product.product'].search([('barcode', '=', barcode)], limit=1)
            parentid = request.env['stock.location'].search([('name', '=', 'WH')], limit=1)
            location = request.env['stock.location'].search([('name', '=', 'Stock'),('location_id', '=', parentid.id)], limit=1)
            if product:
                print "datetime.datetime.utcnow().date()0",datetime.datetime.utcnow().date()
                picking = request.env['procurement.order'].create({
                        'name': product.name,
                        'product_id': product.id,
                        'product_uom':product.uom_id.id,
                        'product_qty':product.product_qty,
                        'product_barcode': product.barcode,
                        'location_id': location.id,
                         'proc_date': datetime.datetime.utcnow().date()

                })
            else:
                return True

            action_picking_form = request.env.ref('proc_barcode.proc_action_form')
            action_picking_form = action_picking_form.read()[0]
            action_picking_form['res_id'] = picking.id
            return {'action': action_picking_form}