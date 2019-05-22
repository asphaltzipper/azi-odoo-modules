# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
import re


class EcmEcoCompatibility(models.Model):
    _name = 'ecm.eco.compatibility'
    _description = 'ECO Version Compatibility'

    name = fields.Char(
        string='Name',
        required=True)

    note = fields.Text(
        string='Note',
        required=True)


class EcmEcoApprovalTmpl(models.Model):
    _name = 'ecm.eco.approval.tmpl'
    _description = 'ECO Approval Template'

    name = fields.Char(
        string='Name',
        required=True)

    stage_id = fields.Many2one(
        comodel_name='ecm.eco.stage',
        required=True)

    user_ids = fields.Many2many(
        comodel_name='res.users',
        string='Users')

    approval_type = fields.Selection(
        selection=[('required', 'Required'),
                   ('optional', 'Optional')],
        string='Type',
        required=True)


class EcmEcoApproval(models.Model):
    _name = 'ecm.eco.approval'
    _description = 'ECO Approval'

    name = fields.Char(
        string='Name',
        required=True)

    eco_id = fields.Many2one(
        comodel_name='ecm.eco',
        required=True)

    stage_id = fields.Many2one(
        comodel_name='ecm.eco.stage',
        required=True)

    this_stage = fields.Boolean(
        compute='_compute_this_stage',
        readonly=True)

    allowed_user_ids = fields.Many2many(
        comodel_name='res.users',
        string='Users')

    approval_type = fields.Selection(
        selection=[('required', 'Required'),
                   ('optional', 'Optional')],
        string='Type',
        required=True)

    state = fields.Selection(
        selection=[('none', 'Pending'),
                   ('approved', 'Approved'),
                   ('rejected', 'Rejected')],
        string="Status",
        default='none',
        required=True)

    signed_user_id = fields.Many2one(
        comodel_name='res.users',
        string='User')

    signed_date = fields.Date(
        string='Date')

    @api.multi
    def button_approval_sign(self):
        self.ensure_one()
        values = {
            'approval_id': self.id,
        }
        if self._uid == 1:
            values['signed_user_id'] = self._uid
        elif self._uid not in self.allowed_user_ids.ids:
            raise UserError("You are not in the list of allowed users for this approval")
        wizard = self.env['ecm.eco.approval.sign'].create(values)
        action = self.env.ref('ecm.action_ecm_approval_sign').read()[0]
        action['res_id'] = wizard.id
        return action

    @api.depends('eco_id.stage_id', 'stage_id')
    def _compute_this_stage(self):
        for rec in self:
            if rec.eco_id.stage_id == rec.stage_id:
                rec.this_stage = True
            else:
                rec.this_stage = False


class EcmEcoStage(models.Model):
    _name = 'ecm.eco.stage'
    _description = 'ECO Stage'
    _order = 'sequence'

    name = fields.Char(
        string='Name',
        required=True)

    is_default = fields.Boolean(
        string='Default',
        required=True,
        default=False,
        help="Starting stage for new ECOs")

    is_reject = fields.Boolean(
        string='Reject',
        required=True,
        default=False,
        help="Allow ECOs to advance to this stage when they have rejected approvals")

    sequence = fields.Integer(
        string='Sequence',
        required=True,
        default=1)

    type_ids = fields.Many2many(
        comodel_name='ecm.eco.type',
        string='Types')

    approval_tmpl_ids = fields.One2many(
        comodel_name='ecm.eco.approval.tmpl',
        inverse_name='stage_id',
        string='Approvals')

    final = fields.Boolean(
        string='Final Stage',
        help="Don't allow changes to ECO when at this stage.")

    create_revs = fields.Boolean(
        string='Require Creation',
        help="Require that all new revs be created before advancing beyond this stage.")


class EcmEcoType(models.Model):
    _name = 'ecm.eco.type'
    _description = 'ECO Type'

    name = fields.Char(
        string='Name',
        required=True)

    default_stage = fields.Many2one(
        comodel_name='ecm.eco.stage',
        required=True)

    stage_ids = fields.Many2many(
        comodel_name='ecm.eco.stage',
        string='Stages')


class EcmEco(models.Model):
    _name = 'ecm.eco'
    _inherit = ['mail.thread']
    _description = 'Engineering Change Order'
    _order = 'name desc'

    def _get_default_stage_id(self):
        """ Gives default stage_id """
        type_id = self.env.context.get('default_type_id')
        if type_id:
            return self.env['ecm.eco.type'].search([('id', '=', type_id)]).default_stage.id
        return self.env['ecm.eco.stage'].search([('is_default', '=', True)], limit=1).id

    name = fields.Char(
        string='Name',
        copy=False,
        required=True,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('ecm.eco.sequence'))

    description = fields.Char(
        string='Description',
        required=True)

    notes = fields.Text(
        string='Notes',
        required=True)

    owner_id = fields.Many2one(
        comodel_name='res.users',
        string="Owner",
        required=True)

    type_id = fields.Many2one(
        comodel_name='ecm.eco.type',
        string='Type',
        required=True,
        track_visibility='onchange')

    stage_id = fields.Many2one(
        comodel_name='ecm.eco.stage',
        string="Stage",
        group_expand='_read_group_stage_ids',
        required=True,
        readonly=True,
        default=_get_default_stage_id,
        domain="[('type_ids', '=', type_id)]",
        track_visibility='onchange')

    final = fields.Boolean(
        related='stage_id.final',
        string="Final")

    approval_ids = fields.One2many(
        comodel_name='ecm.eco.approval',
        inverse_name='eco_id',
        readonly=True)

    state = fields.Selection(
        selection=[('draft', 'New'),
                   ('progress', 'Imported'),
                   ('closed', 'Done'),
                   ('cancel', 'Canceled')],
        string="Status",
        default='draft',
        required=True,
        track_visibility='onchange')

    target_date = fields.Date(
        string='Target',
        required=True,
        default=fields.Date.today())

    line_ids = fields.One2many(
        comodel_name='ecm.eco.line',
        inverse_name='eco_id')

    can_advance = fields.Boolean(
        string='Advance',
        compute='_compute_can_advance',
        store=True)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        search_domain = [('id', 'in', stages.ids)]
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    @api.depends('approval_ids', 'stage_id.create_revs')
    def _compute_can_advance(self):
        for eco in self:
            required_approvals = eco.approval_ids.filtered(lambda x: x.stage_id == x.eco_id.stage_id)
            require_new_revs = eco.stage_id.create_revs
            if not required_approvals and not require_new_revs:
                self.can_advance = True
            else:
                approved = all(x == 'approved' for x in required_approvals.mapped('state'))
                new_revs_done = all(eco.line_ids.mapped('new_product_id'))
                self.can_advance = approved and new_revs_done

    @api.model
    def validate_stage_advance(self, new_stage_id):
        self.ensure_one()
        new_stage = self.env['ecm.eco.stage'].browse(new_stage_id)

        rejected_approvals = self.approval_ids.filtered(lambda x: x.state == 'rejected')
        if rejected_approvals and new_stage.is_reject:
            # allow changing to a rejected stage if approvals have been rejected
            return

        if new_stage.sequence < self.stage_id.sequence:
            # always allow changing to an earlier stage
            return

        required_approvals = self.approval_ids.filtered(lambda x: x.stage_id == x.eco_id.stage_id)
        if not all(x == 'approved' for x in required_approvals.mapped('state')):
            raise UserError("Some approvals have not been accepted")

        if self.stage_id.create_revs and not all(self.line_ids.mapped('new_product_id')):
            raise UserError("Some new revisions have not been created")

    @api.onchange('type_id')
    def _onchange_type(self):
        if self.type_id:
            if not self.stage_id:
                self.stage_id = self.type_id.default_stage
            elif self.stage_id not in self.type_id.stage_ids:
                self.stage_id = self.type_id.default_stage

    @api.model
    def update_type_approvals(self, values):
        if self.type_id and values.get('type_id') and values['type_id'] != self.type_id.id:
            # only operate with current and future stages
            # delete unsigned future stage approvals
            # keep approvals that have already been signed (approved or rejected) on past stages
            self.approval_ids.filtered(lambda x: x.stage_id.sequence >= x.eco_id.stage_id.sequence and x.state == 'none').unlink()
            type_stage_ids = self.env['ecm.eco.type'].search([('id', '=', values['type_id'])]).stage_ids.ids
            # create new approvals
            curr_stage_seq = self.stage_id.sequence
            future_stage_ids = self.env['ecm.eco.stage'].search([('id', 'in', type_stage_ids), ('sequence', '>=', curr_stage_seq)])
            new_tmpls = self.env['ecm.eco.approval.tmpl'].search([('stage_id', 'in', future_stage_ids)])
            for tmpl in new_tmpls:
                self.approval_ids.create({
                    'eco_id': self.id,
                    'name': tmpl.name,
                    'stage_id': tmpl.stage_id,
                    'approval_type': tmpl.approval_type,
                    'allowed_user_ids': [(6, 0, tmpl.user_ids.ids)]
                })

    @api.multi
    def write(self, vals):
        self.update_type_approvals(vals)
        if self.stage_id.final:
            raise UserError("This ECO is in a final stage.  It can't be changed.")
        if self.stage_id and vals.get('stage_id') and vals['stage_id'] != self.stage_id.id:
            self.validate_stage_advance(vals['stage_id'])
        return super(EcmEco, self).write(vals)

    @api.model
    def create(self, vals):
        new_eco = super(EcmEco, self).create(vals)
        # create approvals from type-stage-approval-templates
        tmpls = new_eco.type_id.stage_ids.mapped('approval_tmpl_ids')
        for tmpl in tmpls:
            new_eco.approval_ids.create({
                'eco_id': new_eco.id,
                'name': tmpl.name,
                'stage_id': tmpl.stage_id.id,
                'approval_type': tmpl.approval_type,
                'allowed_user_ids': [(6, 0, tmpl.user_ids.ids)]
            })
        return new_eco

    @api.multi
    def action_create_revisions(self):
        self.ensure_one()
        if not self.stage_id.create_revs:
            raise UserError("Can't create new revisions while the ECO is in stage {}".format(self.stage_id.name))
        for line in self.line_ids.filtered(lambda x: not x.new_product_id):
            new_prod = line.new_product_id.search([('default_code', '=', line.new_code)])
            if new_prod:
                line.new_product_id = new_prod
            else:
                values = {'default_code': line.new_code}
                line.new_product_id = line.product_id.browse(line.product_id.button_revise(values))


class EcmEcoLine(models.Model):
    _name = 'ecm.eco.line'
    _order = 'product_id'

    eco_id = fields.Many2one(
        comodel_name='ecm.eco',
        string="ECO",
        required=True,
        ondelete='cascade',
        readonly=True)

    eco_state = fields.Selection(
        string='State',
        related='eco_id.state',
        readonly=True)

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        ondelete='set null')

    new_rev = fields.Char(
        string='New Rev',
        required=True)

    new_code = fields.Char(
        string='New Code',
        compute='_compute_new_code',
        readonly=True)

    new_product_id = fields.Many2one(
        comodel_name='product.product',
        string='New Product',
        ondelete='set null',
        readonly=True)

    zone = fields.Char(
        string="Zone")

    description = fields.Char(
        string="Change",
        required=True)

    reason = fields.Char(
        string="Reason",
        required=True)

    notes = fields.Text(
        string="Notes")

    compatibility = fields.Many2one(
        comodel_name='ecm.eco.compatibility',
        string="Compatibility",
        required=True)

    @api.constrains('product_id')
    def _validate_product_id(self):
        category = self.product_id.categ_id
        if not category.eng_management:
            raise ValidationError("Only products marked for Engineering Management can be revised on an ECO")
        return True

    @api.constrains('product_id', 'new_rev')
    def _validate_product_code(self):
        category = self.product_id.categ_id
        if not category.eng_management:
            raise ValidationError("Only products marked for Engineering Management can be revised on an ECO")
        new_code = "{}{}{}".format(self.product_id.eng_code, category.rev_delimiter, self.new_rev)
        if not re.match(category.def_code_regex, self.new_code):
            raise ValidationError("The new revision code {} is not valid for this product's Engineering Category".format(new_code))
        if self.product_id.default_code == self.new_code:
            raise ValidationError("The new revision code is the same as the old one: {}".format(new_code))
        return True

    @api.multi
    def _compute_new_code(self):
        for line in self:
            if self.product_id:
                line.new_code = "{}{}{}".format(line.product_id.eng_code, line.product_id.categ_id.rev_delimiter, line.new_rev)
            else:
                line.new_code = False
