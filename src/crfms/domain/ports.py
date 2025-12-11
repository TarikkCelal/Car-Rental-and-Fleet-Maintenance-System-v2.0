from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

# This is to avoid "circular imports". It's really important dor bugfix.
if TYPE_CHECKING:
    from .users import Customer
    from .rental import Invoice
    from .values import Money

# Notification Port

class Notification(ABC):
    """ Port for sending notifications. """
    
    @abstractmethod
    def send(self, customer: 'Customer', message: str):
        """ Sends a notification to a customer. """
        pass

# Payment Port

class Payment(ABC):
    """ Defines the Port for a payment processor."""
    
    @abstractmethod
    def authorize_deposit(self, customer: 'Customer', amount: 'Money') -> str:
        """
        Authorizes a deposit on a customer's card.
        Returns a 'transaction_id'.
        """
        pass
    
    @abstractmethod
    def finalize_payment(self, customer: 'Customer', amount: 'Money') -> str:
        """
        Attempts final payment for the full rental amount.
        Returns a 'transaction_id'.
        """
        pass