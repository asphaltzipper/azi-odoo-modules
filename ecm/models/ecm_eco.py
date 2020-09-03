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
    _order = 'sequence, signed_date'

    name = fields.Char(
        string='Name',
        required=True)

    eco_id = fields.Many2one(
        comodel_name='ecm.eco',
        required=True,
        ondelete='cascade')

    stage_id = fields.Many2one(
        comodel_name='ecm.eco.stage',
        required=True)

    sequence = fields.Integer(
        related='stage_id.sequence',
        store=True,
        readonly=True)

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

    _sql_constraints = [('name_uniq', 'unique (name)', "ECO Number Already Used")]

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
        string='Notes')

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

    rev_line_ids = fields.One2many(
        comodel_name='ecm.eco.rev.line',
        inverse_name='eco_id')

    intro_line_ids = fields.One2many(
        comodel_name='ecm.eco.intro.line',
        inverse_name='eco_id')

    obsolete_line_ids = fields.One2many(
        comodel_name='ecm.eco.obsolete.line',
        inverse_name='eco_id')

    can_advance = fields.Boolean(
        string='Advance',
        compute='_compute_can_advance',
        store=False,
        help="Can advance to the next stage")

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        search_domain = [('id', 'in', stages.ids)]
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    @api.depends('stage_id', 'approval_ids.state', 'stage_id.create_revs')
    def _compute_can_advance(self):
        for eco in self:
            required_approvals = eco.approval_ids.filtered(lambda x: x.stage_id == x.eco_id.stage_id)
            require_new_revs = eco.stage_id.create_revs
            final_stages = eco.stage_id.search([('final', '=', True)])
            if eco.stage_id in final_stages:
                eco.can_advance = False
                return
            if not required_approvals and not require_new_revs:
                eco.can_advance = True
            else:
                approved = all(x == 'approved' for x in required_approvals.mapped('state'))
                new_revs_done = all(eco.rev_line_ids.mapped('new_product_id'))
                eco.can_advance = approved and new_revs_done

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.rev_line_ids.filtered(lambda x: x.new_product_id and x.new_product_id != x.product_id):
                raise UserError("Can't delete because one or more product lines have already been revised")
        return super(EcmEco, self).unlink()

    @api.model
    def validate_stage_advance(self, new_stage_id):
        self.ensure_one()

        new_stage = self.env['ecm.eco.stage'].browse(new_stage_id)

        if self.stage_id.is_reject and new_stage.sequence < self.stage_id.sequence:
            # allow backing down from rejected stage
            return
        elif self.stage_id.final:
            raise UserError("This ECO is in a final stage.  It can't be changed.")

        if new_stage.is_reject and any(self.rev_line_ids.mapped('new_product_id')):
            raise UserError("ECOs can't be rejected after new revisions have been created")

        rejected_approvals = self.approval_ids.filtered(lambda x: x.state == 'rejected')
        if rejected_approvals and new_stage.is_reject:
            # allow changing to a rejected stage if approvals have been rejected
            return

        if new_stage.sequence < self.stage_id.sequence:
            # allow changing to an earlier stage
            return

        required_approvals = self.approval_ids.filtered(lambda x: x.stage_id == x.eco_id.stage_id)
        if not all(x == 'approved' for x in required_approvals.mapped('state')):
            raise UserError("Some approvals have not been accepted")

        if self.stage_id.create_revs and not all(self.rev_line_ids.mapped('new_product_id')):
            raise UserError("Some new revisions have not been created")

        if self.stage_id.create_revs and not all(self.obsolete_line_ids.mapped('product_id.deprecated')):
            raise UserError("Some obsolete items have not been deprecated")

    @api.onchange('type_id')
    def _onchange_type(self):
        if self.type_id:
            if not self.stage_id:
                self.stage_id = self.type_id.default_stage
            elif self.stage_id not in self.type_id.stage_ids:
                self.stage_id = self.type_id.default_stage

    @api.model
    def _create_pending_approvals(self, type_id=None):
        self.ensure_one()
        type_id = type_id or self.type_id.id
        type_stage_ids = self.env['ecm.eco.type'].search([('id', '=', type_id)]).stage_ids.ids
        curr_stage_seq = self.stage_id.sequence
        future_stage_ids = self.env['ecm.eco.stage'].search([
            ('id', 'in', type_stage_ids),
            ('sequence', '>=', curr_stage_seq)])
        new_tmpls = self.env['ecm.eco.approval.tmpl'].search([('stage_id', 'in', future_stage_ids.ids)])
        for tmpl in new_tmpls:
            self.approval_ids.create({
                'eco_id': self.id,
                'name': tmpl.name,
                'stage_id': tmpl.stage_id.id,
                'approval_type': tmpl.approval_type,
                'allowed_user_ids': [(6, 0, tmpl.user_ids.ids)]
            })

    @api.model
    def update_pending_approvals(self, new_type_id=None):
        self.ensure_one()
        # only operate with current and future stages
        # delete unsigned future stage approvals
        # keep approvals that have already been signed (approved or rejected) on past stages
        type_id = new_type_id or self.type_id.id
        self.approval_ids.filtered(
            lambda x: x.stage_id.sequence >= x.eco_id.stage_id.sequence and x.state == 'none'
        ).unlink()

        # create new approvals
        self._create_pending_approvals(self, type_id)

    @api.multi
    def write(self, vals):
        # if eco type is changing, update approvals list
        if self.type_id and vals.get('type_id') and vals['type_id'] != self.type_id.id:
            self.update_pending_approvals(vals['type_id'])
        # if stage is changing, validate stage advance
        if self.stage_id and vals.get('stage_id') and vals['stage_id'] != self.stage_id.id:
            self.validate_stage_advance(vals['stage_id'])
        return super(EcmEco, self).write(vals)

    @api.model
    def create(self, vals):
        new_eco = super(EcmEco, self).create(vals)
        # create approvals from type-stage-approval-templates
        new_eco._create_pending_approvals()
        return new_eco

    def action_create_revisions(self):
        self.ensure_one()
        if not self.stage_id.create_revs:
            raise UserError("Can't create new revisions while the ECO is in stage {}".format(self.stage_id.name))
        for line in self.rev_line_ids.filtered(lambda x: not x.new_product_id):
            new_code = line.new_code
            new_prod = self.env['product.product'].search([('default_code', '=', line.new_code)])
            if new_prod:
                line.new_product_id = new_prod
            else:
                values = {'default_code': line.new_code}
                new_prod = line.product_id.button_revise(values)
                line.new_product_id = new_prod
        for obsolete in self.obsolete_line_ids:
            obsolete.product_id.deprecated = True
            obsolete.product_id.warning = True
            obsolete.product_id.warning_message = obsolete.reason


class EcmEcoRevLine(models.Model):
    _name = 'ecm.eco.rev.line'
    _description = 'Revised ECO Product'
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

    target_date = fields.Date(
        string='Date',
        related='eco_id.target_date',
        readonly=True)

    owner_id = fields.Many2one(
        comodel_name='res.users',
        string="Owner",
        related='eco_id.owner_id',
        readonly=True)

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        ondelete='set null',
        domain=[('deprecated', '=', False)])

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

    new_exists = fields.Boolean(
        string='Exists',
        readonly=True,
        compute='_compute_new_exists')

    old_onhand = fields.Float(
        related='product_id.qty_available',
        readonly=True,
        string="Qty Old")

    new_onhand = fields.Float(
        related='new_product_id.qty_available',
        readonly=True,
        string="Qty New")

    obsolete_move_ids = fields.One2many(
        comodel_name='stock.move',
        inverse_name='product_id',
        string='Old Orders',
        compute='_compute_obsolete_move_ids')

    has_obsolete_moves = fields.Boolean(
        string='Orders',
        compute='_compute_obsolete_move_ids')

    image_small = fields.Binary(
        related='new_product_id.image_small',
        string='Image',
        readonly=True)

    final_docs = fields.Boolean(
        string='Final Docs',
        compute='_compute_final_docs',
        readonly=True,
        help="New product has documents attached")

    eco_docs = fields.Boolean(
        string='ECO Docs',
        compute='_compute_eco_docs',
        readonly=True,
        help="Line has documents attached in this ECO")

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

    doc_ids = fields.One2many(
        comodel_name='ir.attachment',
        string='Documents',
        readonly=True,
        compute='_compute_doc_ids')

    @api.constrains('product_id')
    def _validate_product_management(self):
        if not all(self.mapped('product_id.categ_id.eng_management')):
            raise ValidationError("Only products marked for Engineering Management can be revised on an ECO")
        return True

    @api.constrains('product_id')
    def _validate_product_unique(self):
        for rec in self:
            domain = [('id', '!=', rec.id), ('product_id', '=', rec.product_id.id)]
            other_line = rec.search(domain, limit=1)
            if other_line:
                raise ValidationError("Product has already been revised on ECO %s:\n%s" % (other_line.eco_id.name, rec.product_id.display_name))
        return True

    @api.constrains('product_id', 'new_rev')
    def _validate_product_code(self):
        for rec in self:
            category = rec.product_id.categ_id
            new_code = "{}{}{}".format(rec.product_id.eng_code, category.rev_delimiter, rec.new_rev)
            if not re.match(category.def_code_regex, rec.new_code):
                raise ValidationError("The new revision code {} is not valid for "
                                      "this product's Engineering Category".format(new_code))
            if rec.new_rev != category.default_rev and rec.new_rev <= rec.product_id.eng_rev:
                raise ValidationError("The new revision code must be greater than the old one: {}".format(new_code))
        return True

    @api.depends('product_id', 'new_rev')
    def _compute_new_code(self):
        for line in self:
            if line.product_id:
                line.new_code = "{}{}{}".format(
                    line.product_id.eng_code,
                    line.product_id.categ_id.rev_delimiter,
                    line.new_rev)
            else:
                line.new_code = False

    @api.depends('new_product_id')
    def _compute_new_exists(self):
        for line in self:
            if line.new_product_id:
                line.new_exists = True
            else:
                line.new_exists = False

    @api.depends('new_product_id')
    def _compute_final_docs(self):
        for line in self:
            domain = [
                ('res_field', '=', False),
                '|',
                '&',
                ('res_model', '=', 'product.product'),
                ('res_id', '=', line.new_product_id.id),
                '&',
                ('res_model', '=', 'product.template'),
                ('res_id', '=', line.new_product_id.product_tmpl_id.id),
            ]
            line.final_docs = self.env['ir.attachment'].search(domain, count=True)

    @api.depends('product_id', 'new_rev')
    def _compute_eco_docs(self):
        for line in self:
            domain = [
                ('res_model', '=', 'ecm.eco.rev.line'),
                ('res_id', '=', line.id),
            ]
            line.eco_docs = self.env['ir.attachment'].search(domain, count=True)

    @api.depends('product_id', 'new_rev')
    def _compute_doc_ids(self):
        for line in self:
            doc_domain = [
                ('res_model', '=', 'ecm.eco.rev.line'),
                ('res_id', '=', line.id),
            ]
            line.doc_ids = self.env['ir.attachment'].search(doc_domain)

    @api.depends('product_id')
    def _compute_obsolete_move_ids(self):
        for line in self:
            line.obsolete_move_ids = line.product_id.stock_move_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
            line.has_obsolete_moves = bool(len(line.obsolete_move_ids))

    @api.multi
    def attach_document(self, file_name, file_data):
        self.env['ir.attachment'].create({
            'name': file_name,
            'datas': file_data,
            'datas_fname': file_name,
            'res_model': 'ecm.eco.rev.line',
            'res_id': self.id,
        })


class EcmEcoIntroLine(models.Model):
    _name = 'ecm.eco.intro.line'
    _description = 'Introduced ECO Product'
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

    target_date = fields.Date(
        string='Date',
        related='eco_id.target_date',
        readonly=True)

    owner_id = fields.Many2one(
        comodel_name='res.users',
        string="Owner",
        related='eco_id.owner_id',
        readonly=True)

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        ondelete='set null')

    product_onhand = fields.Float(
        related='product_id.qty_available',
        readonly=True)

    image_small = fields.Binary(
        related='product_id.image_small',
        string='Image',
        readonly=True)

    final_docs = fields.Boolean(
        string='Final Docs',
        compute='_compute_final_docs',
        readonly=True,
        help="New product has documents attached")

    notes = fields.Text(
        string="Notes")

    @api.constrains('product_id')
    def _validate_product_management(self):
        if not all(self.mapped('product_id.categ_id.eng_management')):
            raise ValidationError("Only products marked for Engineering Management can be introduced on an ECO")
        return True

    @api.constrains('product_id')
    def _validate_product_unique(self):
        for rec in self:
            domain = [('id', '!=', rec.id), ('product_id', '=', rec.product_id.id)]
            other_line = rec.search(domain, limit=1)
            if other_line:
                raise ValidationError("Product has already been introduced on ECO %s:\n%s" % (other_line.eco_id.name, rec.product_id.display_name))
        return True

    @api.depends('product_id')
    def _compute_final_docs(self):
        for line in self:
            domain = [
                ('res_field', '=', False),
                '|',
                '&',
                ('res_model', '=', 'product.product'),
                ('res_id', '=', line.product_id.id),
                '&',
                ('res_model', '=', 'product.template'),
                ('res_id', '=', line.product_id.product_tmpl_id.id),
            ]
            line.final_docs = self.env['ir.attachment'].search(domain, count=True)


class EcmEcoObsoleteLine(models.Model):
    _name = 'ecm.eco.obsolete.line'
    _description = 'Obsolete ECO Product'
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

    target_date = fields.Date(
        string='Date',
        related='eco_id.target_date',
        readonly=True)

    owner_id = fields.Many2one(
        comodel_name='res.users',
        string="Owner",
        related='eco_id.owner_id',
        readonly=True)

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        ondelete='set null')

    product_onhand = fields.Float(
        related='product_id.qty_available',
        readonly=True)

    deprecated = fields.Boolean(
        related='product_id.deprecated',
        readonly=True,
        string='Obsolete',
        help="Showing current obsolete status of the part.  If the product is "
             "on this list, it will get set to obsolete automatically as the "
             "ECO is advanced.")

    reason = fields.Text(
        string="Reason",
        required=True,
        help="Explanation or reason that this product will be obsolete")

    @api.constrains('product_id')
    def _validate_product_id(self):
        if not all(self.mapped('product_id.categ_id.eng_management')):
            raise ValidationError("Only products marked for Engineering Management can be deprecated on an ECO")
        return True
