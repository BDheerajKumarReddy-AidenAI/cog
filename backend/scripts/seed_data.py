"""Script to seed the PostgreSQL database with highly varied analytics data."""

import asyncio
from datetime import date, timedelta
from random import randint, choice, uniform, random
from math import sin, pi
from random import gauss

from app.core.database import engine, async_session_maker
from app.models.analytics import SalesData, CustomerData, ProductData, Base

# -------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------

REGIONS = ["North", "South", "East", "West"]
SEGMENTS = ["Enterprise", "SMB", "Consumer"]

CATEGORIES = {
    "Electronics": ["Laptops", "Phones", "Tablets", "Accessories"],
    "Furniture": ["Desks", "Chairs", "Storage", "Tables"],
    "Office Supplies": ["Paper", "Pens", "Organizers", "Binders"],
}

# -------------------------------------------------------------------
# Product Seeding
# -------------------------------------------------------------------

async def seed_products(session):
    """Seed product data."""
    products = []
    product_id = 1

    for category, subcategories in CATEGORIES.items():
        for subcategory in subcategories:
            for i in range(5):
                cost = round(uniform(10, 500), 2)
                product = ProductData(
                    id=product_id,
                    name=f"{subcategory} Product {i + 1}",
                    category=category,
                    subcategory=subcategory,
                    unit_cost=cost,
                    unit_price=round(cost * uniform(1.2, 2.0), 2),
                )
                products.append(product)
                product_id += 1

    session.add_all(products)
    await session.commit()
    print(f"Seeded {len(products)} products")
    return products

# -------------------------------------------------------------------
# Customer Seeding
# -------------------------------------------------------------------

async def seed_customers(session):
    """Seed customer data."""
    customers = []
    first_names = ["John", "Jane", "Bob", "Alice", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

    for i in range(100):
        first = choice(first_names)
        last = choice(last_names)

        customer = CustomerData(
            id=i + 1,
            name=f"{first} {last}",
            email=f"{first.lower()}.{last.lower()}{i}@example.com",
            segment=choice(SEGMENTS),
            region=choice(REGIONS),
            joined_date=date.today() - timedelta(days=randint(30, 730)),
            lifetime_value=round(uniform(100, 50000), 2),
        )
        customers.append(customer)

    session.add_all(customers)
    await session.commit()
    print(f"Seeded {len(customers)} customers")
    return customers

# -------------------------------------------------------------------
# Sales Seeding (HIGH VARIANCE + SPIKES)
# -------------------------------------------------------------------

async def seed_sales(session, products, customers):
    """Seed sales data with spikes, lows, seasonality, and growth."""
    sales = []
    start_date = date.today() - timedelta(days=730)

    REGION_MULTIPLIER = {
        "North": 1.25,
        "West": 1.15,
        "South": 1.0,
        "East": 0.8,
    }

    SEGMENT_QTY_MULTIPLIER = {
        "Enterprise": (6, 14),
        "SMB": (2, 7),
        "Consumer": (1, 4),
    }

    CATEGORY_DEMAND = {
        "Electronics": 0.9,
        "Furniture": 0.7,
        "Office Supplies": 1.4,
    }

    SPIKE_PROBABILITY = 0.06   # ~6% spike days
    CRASH_PROBABILITY = 0.04  # ~4% low days

    for day_offset in range(730):
        current_date = start_date + timedelta(days=day_offset)

        # ---- Seasonality ----
        seasonal_factor = 1 + 0.4 * sin(2 * pi * day_offset / 365)

        # ---- Year-over-year growth ----
        growth_factor = 1.2 if day_offset > 365 else 1.0

        # ---- Base daily volume ----
        base_sales = 12 * seasonal_factor * growth_factor
        num_sales = gauss(base_sales, 4)

        # ---- Spike days ----
        if random() < SPIKE_PROBABILITY:
            num_sales *= uniform(2.0, 3.5)

        # ---- Crash days ----
        elif random() < CRASH_PROBABILITY:
            num_sales *= uniform(0.15, 0.45)

        num_sales = max(2, int(num_sales))

        for _ in range(num_sales):
            product = choice(products)
            customer = choice(customers)

            qty_min, qty_max = SEGMENT_QTY_MULTIPLIER[customer.segment]
            quantity = randint(qty_min, qty_max)

            demand_factor = CATEGORY_DEMAND[product.category]
            region_factor = REGION_MULTIPLIER[customer.region]

            adjusted_qty = max(
                1,
                int(quantity * demand_factor * region_factor)
            )

            sale = SalesData(
                date=current_date,
                product_id=product.id,
                customer_id=customer.id,
                quantity=adjusted_qty,
                unit_price=product.unit_price,
                total_amount=round(product.unit_price * adjusted_qty, 2),
                region=customer.region,
            )
            sales.append(sale)

    session.add_all(sales)
    await session.commit()
    print(f"Seeded {len(sales)} HIGH-VARIANCE sales records")

# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

async def main():
    """Main function to seed all data."""
    print("Initializing database...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        products = await seed_products(session)
        customers = await seed_customers(session)
        await seed_sales(session, products, customers)

    print("Database seeding complete!")

if __name__ == "__main__":
    asyncio.run(main())
