from typing import List, Tuple
from ..domain.ports import Notification
from ..domain.users import Customer

class InMemoryNotificationAdapter(Notification):
    """ Notification port. """
    
    def __init__(self):
        self.sent_messages: List[Tuple[str, str]] = []

    def send(self, customer: Customer, message: str):
        """ Send method for the Notification port. """
        print(f"--- NOTIFICATION ---")
        print(f"To: {customer.email}")
        print(f"Message: {message}")
        print(f"----------------------")
        
        self.sent_messages.append((customer.email, message))
        
    def clear(self):
        self.sent_messages = []