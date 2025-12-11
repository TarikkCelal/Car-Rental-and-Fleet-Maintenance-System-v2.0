from dataclasses import dataclass, field
from uuid import UUID, uuid4
from .fleet import Location

# Entities

@dataclass
class Customer:
    """ Customer entity."""
    first_name: str
    last_name: str
    email: str
    id: UUID = field(default_factory=uuid4)

@dataclass
class BranchAgent:
    """ Branch agent entity. """
    first_name: str
    last_name: str
    location: Location
    id: UUID = field(default_factory=uuid4)