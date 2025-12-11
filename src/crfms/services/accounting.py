from .database import Database
from ..domain.ports import Payment, Notification
from ..domain.rental import Invoice, BillingPayment, BillingPaymentStatus, InvoiceStatus
from ..domain.users import Customer
from ..domain.values import Money

class AccountingService:
    """ Service for capturing depositsand finalizing payments."""
    def __init__(self, db: Database, payment_port: Payment, notifier: Notification):
        self.db = db
        self.payment_port = payment_port
        self.notifier = notifier

    def capture_deposit(self, customer: Customer, amount: Money):
        """ Attempts to pre-authorize a deposit. """
        try:
            self.payment_port.authorize_deposit(customer, amount)
        except Exception as e:
            print(f"Deposit authorization failed for {customer.email}: {e}")
            raise

    def finalize_payment(self, invoice: Invoice):
        """ Attempts to finalize payment for an invoice. """
        customer = invoice.rental_agreement.reservation.customer
        amount = invoice.total_amount
        
        try:
            tx_id = self.payment_port.finalize_payment(customer, amount)
            invoice.status = InvoiceStatus.PAID
            status = BillingPaymentStatus.SUCCESS
            msg = f"Your payment for invoice {invoice.id} was successful."
            
        except Exception as e:
            invoice.status = InvoiceStatus.FAILED
            status = BillingPaymentStatus.FAILURE
            tx_id = None
            msg = f"Payment failed for invoice {invoice.id}. Please update your billing."
            
        payment = BillingPayment(
            invoice=invoice,
            amount_charged=amount,
            status=status,
            transaction_id=tx_id
        )
        self.db.payments[payment.id] = payment
        
        self.notifier.send(customer, msg)