from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    serial_count = fields.Integer(compute='_compute_serial_count', string='# of Serials')
    ticket_count = fields.Integer(compute='_compute_ticket_count', string='# of Tickets')

    def _compute_serial_count(self):
        serial_data = self.env['stock.production.lot'].read_group(
            domain=[('partner_id', 'child_of', self.ids)],
            fields=['partner_id'],
            groupby=['partner_id'])
        # read to keep the child/parent relation while aggregating the read_group result in the loop
        partner_child_ids = self.read(['child_ids'])
        mapped_data = dict([(m['partner_id'][0], m['partner_id_count']) for m in serial_data])
        for partner in self:
            # let's obtain the partner id and all its child ids from the read up there
            partner_ids = list(filter(lambda r: r['id'] == partner.id, partner_child_ids))[0]
            partner_ids = [partner_ids.get('id')] + partner_ids.get('child_ids')
            # then we can sum for all the partner's child
            partner.serial_count = sum(mapped_data.get(child, 0) for child in partner_ids)

    def _compute_ticket_count(self):
        ticket_data = self.env['helpdesk.ticket'].read_group(
            domain=[('partner_id', 'child_of', self.ids)],
            fields=['partner_id'],
            groupby=['partner_id'])
        # read to keep the child/parent relation while aggregating the read_group result in the loop
        partner_child_ids = self.read(['child_ids'])
        mapped_data = dict([(m['partner_id'][0], m['partner_id_count']) for m in ticket_data])
        for partner in self:
            # let's obtain the partner id and all its child ids from the read up there
            partner_ids = list(filter(lambda r: r['id'] == partner.id, partner_child_ids))[0]
            partner_ids = [partner_ids.get('id')] + partner_ids.get('child_ids')
            # then we can sum for all the partner's child
            partner.ticket_count = sum(mapped_data.get(child, 0) for child in partner_ids)
