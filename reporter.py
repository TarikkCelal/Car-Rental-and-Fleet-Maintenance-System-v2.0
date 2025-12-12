import argparse
import sys
import os
from collections import defaultdict

# Ensure src is in pythonpath
sys.path.append(os.path.join(os.getcwd(), 'src'))

from crfms.persistence.json_io import load_from_json
from crfms.persistence.proto_io import load_from_proto
from crfms.domain.rental import InvoiceStatus

def main():
    parser = argparse.ArgumentParser(description="CRFMS Reporting Tool")
    parser.add_argument("input_file", help="Path to snapshot file")
    parser.add_argument("--format", choices=["json", "proto"], default="json", help="Format of input file (default: json)")
    
    args = parser.parse_args()
    
    print(f"Loading data from {args.input_file} ({args.format})...")
    
    try:
        if args.format == "json":
            db = load_from_json(args.input_file)
        else:
            db = load_from_proto(args.input_file)
    except Exception as e:
        print(f"Error loading file: {e}")
        sys.exit(1)
        
    print(" CRFMS SYSTEM REPORT ")
    
    # Metric 1: Total Vehicles per Class
    print("\n1. Vehicles per Class:")
    class_counts = defaultdict(int)
    for v in db.vehicles.values():
        class_counts[v.vehicle_class.name] += 1
        
    if not class_counts:
        print(" (No vehicles found) ")
    for name, count in class_counts.items():
        print(f"   - {name}: {count}")

    # Metric 2: Active vs Completed Rentals
    active_count = 0
    completed_count = 0
    
    for ra in db.rental_agreements.values():
        if ra.return_time is None:
            active_count += 1
        else:
            completed_count += 1
            
    print("\n2. Rental Statistics:")
    print(f"   - Active Rentals: {active_count}")
    print(f"   - Completed Rentals: {completed_count}")
    
    # Metric 3: Total Revenue (from Paid Invoices)
    total_revenue = 0.0
    pending_revenue = 0.0
    for inv in db.invoices.values():
        if inv.status == InvoiceStatus.PAID:
            total_revenue += inv.total_amount.value
        elif inv.status == InvoiceStatus.PENDING:
            pending_revenue += inv.total_amount.value
            
    print(f"\n3. Financial Overview:")
    print(f"   - Total Revenue (Paid):    ${total_revenue:,.2f}")
    print(f"   - Pending Revenue:         ${pending_revenue:,.2f}")

    # Metric 4: Top Customers
    print("\n4. Top Customers by Spending:")
    cust_spending = defaultdict(float)
    for inv in db.invoices.values():
        if inv.status == InvoiceStatus.PAID:
            c = inv.rental_agreement.reservation.customer
            cust_spending[c.email] += inv.total_amount.value
            
    sorted_cust = sorted(cust_spending.items(), key=lambda x: x[1], reverse=True)[:3]
    
    if not sorted_cust:
        print(" (No spending data) ")
    for i, (email, spent) in enumerate(sorted_cust, 1):
        print(f"   {i}. {email}: ${spent:,.2f}")

if __name__ == "__main__":
    main()