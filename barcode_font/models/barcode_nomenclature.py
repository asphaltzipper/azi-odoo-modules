from odoo import models


class BarcodeNomenclature(models.Model):
    _inherit = 'barcode.nomenclature'

    def get_code128_encoding(self, base_string):
        """ Computes and adds check character
            Adds start and stop characters
            Based on code from https://stackoverflow.com/q/52710760/5987
        """
        def list_join(seq):
            return [x for sub in seq for x in sub]
        code128B_mapping = dict((chr(c), [98, c + 64] if c < 32 else [c - 32]) for c in range(128))
        code128C_mapping = dict(
            [(u'%02d' % i, [i]) for i in range(100)] + [(u'%d' % i, [100, 16 + i]) for i in range(10)])
        code128_chars = u''.join(chr(c) for c in [212] + list(range(33, 126 + 1)) + list(range(200, 211 + 1)))

        if base_string.isdigit() and len(base_string) >= 2:
            # use Code 128C, pairs of digits
            codes = [105] + list_join(
                code128C_mapping[base_string[i:i + 2]] for i in range(0, len(base_string), 2))
        else:
            # use Code 128B and shift for Code 128A
            codes = [104] + list_join(code128B_mapping[c] for c in base_string)
        check_digit = (codes[0] + sum(i * x for i, x in enumerate(codes))) % 103
        codes.append(check_digit)
        codes.append(106)  # stop code
        return u''.join(code128_chars[x] for x in codes)
