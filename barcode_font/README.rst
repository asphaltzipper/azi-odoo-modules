Barcode Font
============
Provides various tools for encoding strings to be used with barcode fonts.  This is helpful when printing small, dense barcodes.  Using a font will produce much better print quality than using a raster image of the barcode.


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
* No specific configuration required.


Usage
=====
To be used by backend code
