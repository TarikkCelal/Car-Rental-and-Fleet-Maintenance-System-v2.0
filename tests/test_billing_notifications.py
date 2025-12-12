import pytest
from crfms.domain.values import Money
from crfms.domain.rental import Invoice, RentalAgreement, Reservation, InvoiceStatus
from crfms.domain.users import Customer


@pytest.fixture
def pending_invoice(db, clock, customer, vehicle, location, vehicle_class):
    """
    Creates a pending invoice linked to a rental agreement/reservation.
    This avoids repeating the full rental workflow setup in every test.
    """
    reservation = Reservation(
        customer=customer,
        vehicle_class=vehicle_class,
        pickup_location=location,
        return_location=location,
        pickup_time=clock.now(),
        return_time=clock.now(),
        deposit_amount=Money(0)
    )
    
    agreement = RentalAgreement(
        reservation=reservation,
        vehicle=vehicle,
        pickup_time=clock.now(),
        start_odometer=vehicle.odometer,
        start_fuel_level=vehicle.fuel_level,
        due_time=clock.now()
    )
    
    invoice = Invoice(
        rental_agreement=agreement,
        total_amount=Money(100)
    )
    db.invoices[invoice.id] = invoice
    return invoice


# --- Tests ---

def test_payment_success_flow(accounting_service, pending_invoice, notifier, payment_adapter):
    " Verifies that when the payment adapter succeess, the invoice is paid and a success notification is sent."

    payment_adapter.should_succeed = True
    accounting_service.finalize_payment(pending_invoice)
    
    assert pending_invoice.status == InvoiceStatus.PAID
    assert len(notifier.sent_messages) == 1
    recipient_email, message = notifier.sent_messages[0]
    assert recipient_email == pending_invoice.rental_agreement.reservation.customer.email
    assert "successful" in message

def test_payment_failure_with_monkeypatch(accounting_service, pending_invoice, notifier, monkeypatch):
    """
    Verifies that when the payment adapter fails,
    the invoice is failed and a failure notification is sent.
    """
    def mock_finalize_payment_fail(customer, amount):
        raise Exception("Simulated Payment Gateway Error")
    
    monkeypatch.setattr(
        accounting_service.payment_port, 
        "finalize_payment", 
        mock_finalize_payment_fail
    )
    
    accounting_service.finalize_payment(pending_invoice)
    
    assert pending_invoice.status == InvoiceStatus.FAILED
    assert len(notifier.sent_messages) == 1
    recipient_email, message = notifier.sent_messages[0]
    assert "failed" in message

def test_deposit_authorization_failure(accounting_service, customer, monkeypatch):
    def mock_auth_fail(cust, amt):
        raise ValueError("Insufficient Funds")
        
    monkeypatch.setattr(
        accounting_service.payment_port, 
        "authorize_deposit", 
        mock_auth_fail
    )

    with pytest.raises(ValueError, match="Insufficient Funds"):
        accounting_service.capture_deposit(customer, Money(50))