# Car Rental & Fleet Maintenance System (CRFMS)

This project is a complete, object-oriented system. It implements a **Car Rental & Fleet Maintenance System (CRFMS)** using modern Python, Clean Architecture principles, and a fully testable design.

Version 2.0 introduces persistent storage capabilities, supporting both JSON and Google Protocol Buffers, along with CLI utilities for data conversion and reporting.

---

# Core Features

* **Reservation Management:** Create, confirm, and cancel reservations.

* **Rental Workflow:** Full logic for vehicle pickup and return, including state changes (Available, Rented, Cleaning).

* **Dynamic Pricing:** A flexible pricing system built with the Strategy Pattern.

* **Penalty Calculation:** Automatically computes late fees, mileage overages, and fuel charges.

* **Fleet Maintenance:** Tracks maintenance records and blocks vehicles from rental if service is due.

* **Persistence:** Save and load the entire system state to JSON or Protocol Buffers.

* **Tools:** Command-line utilities for converting data formats and generating text reports.

---

# Architectural Design

This system is built using a Clean Architecture (Ports & Adapters) approach, emphasising a separation of concerns and adherence to SOLID principles.

**Core Layers**

* `crfms/domain:` The heart of the application. Contains all core business logic, entities (Vehicle, Reservation), Value Objects (Money, Kilometers), and Ports. It has zero dependencies on other layers.

* `crfms/services:` The orchestration layer. Coordinates domain entities to perform use cases (e.g., RentalService, AccountingService).

* `crfms/adapters:` Concrete implementations of the ports (e.g., FakePaymentAdapter).

* `crfms/persistence:` The new layer handling data storage. It contains the Protocol Buffers schema (.proto), generated code (_pb2.py), and the serialization logic for JSON and binary formats.

---

# Project Structure

    car_rental_system/
    ├── src/
    │   └── crfms/              # The main Python package
    │       ├── __init__.py
    │       ├── persistence/      # Persistence Layer (JSON & Proto)
    │       │   ├── __init__.py
    │       │   ├── crfms.proto     # Protocol Buffers Schema
    │       │   ├── crfms_pb2.py    # Generated Python code
    │       │   ├── json_io.py      # JSON serialization logic
    │       │   └── proto_io.py     # Proto serialization logic
    │       ├── domain/           # Core entities & logic
    │       ├── services/         # Use-case orchestration
    │       └── adapters/         # Ports & Adapters
    ├── tests/              # All pytest tests
    ├── converter.py        # Utility: Convert JSON <-> Proto
    ├── reporter.py         # Utility: Generate text reports
    ├── test_json_persist.py # Verification script for JSON
    ├── test_proto_persist.py # Verification script for Proto
    ├── pytest.ini          # Pytest configuration
    ├── requirements.txt    # Python dependencies
    ├── design.puml         # UML Class Diagram
    └── README.md           # This file
