AZI Stock
=========
* Adding constraint in `stock.quant` to prevent creating a new record in
  `stock.quant` when the picking type is internal and product is tracked by serial number
* Adding field in `stock.move.line`
* Adding a field and modifying the views of `stock.picking` and `stock.move`
* Modifying "Picking Operations" report to display "Completed Date"
* Create label reports for `product.product`, `product.template` and
  `stock.move`, also create paper format

Installation
============
In order to take advantage of printers with barcode font Code128 embedded, you
will need to install the font on the Odoo server. Do that by copying the file
font file (./support/code128.ttf) to someplace like this:

 cp ./support/code128.ttf ~/.local/share/fonts/

Then, run the following:

 sudo fc-cache -f -v

The font was obtained from http://www.barcodelink.net/barcode-font.php.

Font copyright Grandzebu. 2003. GNU General Public License.


Configuration
=============
* You need to enable "Show Detailed Operations" in Inventory > Configuration > Operations types

Usage
=====
* To check constraint for `stock.quant` we need to create internal picking for
  product that is tracked by serial by going to Inventory > Operations >
  Transfer
* Picking operations report: Inventory > operations > Transfer > Print
* AZI Product Labels report: Inventory > Master Data > Products or Inventory >
  Master Data > Product Variants
* New view of stock quant: Inventory > Reporting > FG Stock Valuation
* Transfer Slip report: Inventory > Reporting > Stock Moves
* AZI Location Labels report: Inventory > Master Data > Stock Shelf
