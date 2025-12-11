# Car Rental & Fleet Maintenance System (CRFMS)

A **complete, object-oriented system** for managing car rentals, fleet maintenance, and billing — built with **Clean Architecture** and **SOLID principles**.

---

## Overview

**CRFMS** is designed to support the full lifecycle of a car rental operation, including:

- **Customers:** Create and manage reservations.  
- **Branch Agents:** Handle vehicle pickups and returns, record odometer/fuel data, and assess charges.  
- **Fleet Managers:** Enforce maintenance holds based on vehicle odometer or time thresholds.

It accurately calculates:
- Rental charges  
- Late fees  
- Mileage overage  
- Fuel refill penalties  

The system is **fully testable** thanks to an injectable `Clock`, allowing time-based logic to be verified easily.

---

## Core Design & Architecture

This project follows **Clean Architecture (Ports & Adapters)** and **SOLID** design principles.

### Layers

#### Domain (`crfms/domain`)
Contains the **core business logic**, **entities**, and **value objects**:
- Entities: `Vehicle`, `Reservation`, etc.
- Value Objects: `Money`, `Kilometers`, etc.
- No dependencies on other layers.

#### Services (`crfms/services`)
Implements the **application layer**, orchestrating domain entities to perform use cases:
- `RentalService`
- `AccountingService`
- `MaintenanceService`
- `ReservationService`

#### Adapters (`crfms/adapters`)
Concrete implementations of the interfaces (ports) defined in the domain:
- `FakePaymentAdapter` → simulates payment success/failure.  
- `InMemoryNotificationAdapter` → records sent notifications (great for testing).

### Design Patterns

- **Strategy Pattern:**  
  `PricingPolicy` uses strategies like `BaseDailyRateRule`, enabling new pricing rules without touching existing code.

- **Dependency Inversion:**  
  Adapters implement interfaces defined by the domain layer.

---

## Project Structure

```bash
car_rental_system/
├── crfms/
│   ├── adapters/           # Implementations of ports
│   │   ├── notifications.py
│   │   └── payments.py
│   ├── domain/             # Core business logic and entities
│   │   ├── fleet.py
│   │   ├── pricing.py
│   │   ├── rental.py
│   │   ├── users.py
│   │   └── values.py
│   └── services/           # Use-case orchestration layer
│       ├── accounting.py
│       ├── database.py
│       ├── inventory.py
│       ├── maintenance.py
│       ├── rental.py
│       └── reservation.py
├── tests/
│   └── test_rental_workflow.py
├── design.puml             # UML class diagram
├── requirements.txt        # Dependencies
└── README.md               # This file
