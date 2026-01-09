"""Script to seed the PostgreSQL database with sample analytics data."""

import asyncio
from datetime import date, timedelta
from random import randint, choice, uniform
from sqlalchemy import text
from app.core.database import engine, async_session_maker, init_db
from app.models.analytics import SalesData, CustomerData, ProductData, Base

REGIONS = ["North", "South", "East", "West"]
SEGMENTS = ["Enterprise", "SMB", "Consumer"]
CATEGORIES = {
    "Electronics": ["Laptops", "Phones", "Tablets", "Accessories"],
    "Furniture": ["Desks", "Chairs", "Storage", "Tables"],
    "Office Supplies": ["Paper", "Pens", "Organizers", "Binders"],
}


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


async def seed_sales(session, products, customers):
    """Seed sales data for the past 2 years."""
    sales = []
    start_date = date.today() - timedelta(days=730)

    for day_offset in range(730):
        current_date = start_date + timedelta(days=day_offset)
        num_sales = randint(5, 20)

        for _ in range(num_sales):
            product = choice(products)
            customer = choice(customers)
            quantity = randint(1, 10)

            sale = SalesData(
                date=current_date,
                product_id=product.id,
                customer_id=customer.id,
                quantity=quantity,
                unit_price=product.unit_price,
                total_amount=round(product.unit_price * quantity, 2),
                region=choice(REGIONS),
            )
            sales.append(sale)

    session.add_all(sales)
    await session.commit()
    print(f"Seeded {len(sales)} sales records")


async def main():
    """Main function to seed all data."""
    print("Initializing database...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        print("Seeding products...")
        products = await seed_products(session)

        print("Seeding customers...")
        customers = await seed_customers(session)

        print("Seeding sales data...")
        await seed_sales(session, products, customers)

    print("Database seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())
