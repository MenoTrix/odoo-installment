from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class Payment(models.Model):
    _inherit = "account.payment"
    installment_id = fields.Many2one("installment.installment")


class Installment(models.Model):
    _name = "installment.installment"
    _description = "Customer Installment"

    name = fields.Char(string="Name", readonly=True)
    reference = fields.Char(string="Reference")
    state = fields.Selection(
        [("draft", "Draft"), ("open", "Open"), ("paid", "Paid")],
        string="State",
        default="draft",
    )
    date = fields.Date(string="Date", default=fields.Date.today())
    customer = fields.Many2one("res.partner", string="Customer", required=True)
    journal = fields.Many2one("account.journal", string="Journal", required=True)
    account = fields.Many2one("account.account", string="Account", required=True)
    analytic_account = fields.Many2one(
        "account.analytic.account", string="Analytic Account"
    )
    analytic_tags = fields.Many2many("account.analytic.tag", string="Analytic Tags")
    # product = fields.Many2one("product.product", string="Product", required=True)
    amount = fields.Float(string="Amount", required=True, digits="Account")
    notes = fields.Text(string="Notes")
    paid = fields.Float()

    payment_id = fields.One2many(
        "account.payment", "installment_id", string="Payment", readonly="1"
    )

    def unlink(self):
        for record in self:
            if record.state not in ["draft", "open"]:
                raise UserError(
                    "You can only delete installments in the 'draft' state."
                )
        return super().unlink()

    def write(self, vals):
        for record in self:
            if record.state not in ["draft", "open"]:
                raise UserError("You can only edit installments in the 'draft' state.")
        return super(Installment, self).write(vals)

    # ********************************************************************

    @api.constrains("paid")
    def _check_paid(self):
        if self.paid == self.amount:
            self.state = "paid"

    # 3 Buttons
    def settle_installment(self):
        self.paid = self.amount

    def action_open(self):
        invoice_vals = {
            "journal_id": self.journal.id,
            "partner_id": self.account.id,
            "invoice_date": self.date,
            "ref": self.reference,
            "date": self.date,
        }
        try:
            invoice = self.env["account.move"].sudo().create(invoice_vals)
            self.name = invoice.name
            self.state = "open"
        except UserError as e:
            raise UserError(f"Error while opening invoice: {e}")


class InstallmentPaymentWizard(models.TransientModel):
    _name = "installment.payment.wizard"
    _description = "Installment Payment Wizard"

    installment_id = fields.Many2one("installment.installment", string="Installment")
    installment_paid = fields.Float(
        related="installment_id.paid", string="Installment Paid"
    )
    payment_amount = fields.Float(
        string="Payment Amount", required=True, digits="Product Price"
    )
    payment_method = fields.Many2one("account.payment.method", string="Payment Method")
    notes = fields.Text(string="Notes")
    date = fields.Date()

    def confirm_payment(self):
        installment_id = self.env["installment.installment"].search(
            [("id", "=", self.installment_id.id)]
        )

        if installment_id.amount < (self.payment_amount + installment_id.paid):
            raise UserError("The Payment Can't exceed the price of the unit ")

        if installment_id:
            self.env["account.payment"].create(
                {
                    "payment_method_line_id": self.payment_method.id,
                    "installment_id": self.installment_id.id,
                    "journal_id": self.installment_id.journal.id,
                    "partner_id": self.installment_id.customer.id,
                    "date": self.date,
                    "amount": self.payment_amount,
                    "ref": self.installment_id.reference,
                }
            )

            installment_id.paid = installment_id.paid + self.payment_amount
            print(installment_id)
