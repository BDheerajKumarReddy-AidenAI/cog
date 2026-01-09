from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime


class SalesData(Base):
    __tablename__ = "sales_data"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    region = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("ProductData", back_populates="sales")
    customer = relationship("CustomerData", back_populates="sales")


class CustomerData(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    segment = Column(String(50), nullable=False, index=True)  # Enterprise, SMB, Consumer
    region = Column(String(100), nullable=False, index=True)
    joined_date = Column(Date, nullable=False)
    lifetime_value = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    sales = relationship("SalesData", back_populates="customer")


class ProductData(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100), nullable=False)
    unit_cost = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sales = relationship("SalesData", back_populates="product")


# Database schema description for the LLM system prompt
DATABASE_SCHEMA = """
DATABASE SCHEMA:

Table: sales_data
- id: INTEGER (Primary Key)
- date: DATE (Sale date)
- product_id: INTEGER (Foreign Key to products.id)
- customer_id: INTEGER (Foreign Key to customers.id)
- quantity: INTEGER (Units sold)
- unit_price: FLOAT (Price per unit)
- total_amount: FLOAT (Total sale amount)
- region: VARCHAR(100) (Sales region: North, South, East, West)
- created_at: DATETIME

Table: customers
- id: INTEGER (Primary Key)
- name: VARCHAR(200) (Customer name)
- email: VARCHAR(200) (Unique email)
- segment: VARCHAR(50) (Customer segment: Enterprise, SMB, Consumer)
- region: VARCHAR(100) (Customer region)
- joined_date: DATE (Customer join date)
- lifetime_value: FLOAT (Total customer lifetime value)
- created_at: DATETIME

Table: products
- id: INTEGER (Primary Key)
- name: VARCHAR(200) (Product name)
- category: VARCHAR(100) (Product category: Electronics, Furniture, Office Supplies)
- subcategory: VARCHAR(100) (Product subcategory)
- unit_cost: FLOAT (Cost per unit)
- unit_price: FLOAT (Selling price per unit)
- created_at: DATETIME

RELATIONSHIPS:
- sales_data.product_id -> products.id
- sales_data.customer_id -> customers.id

SAMPLE QUERIES:
- Total sales by region: SELECT region, SUM(total_amount) FROM sales_data GROUP BY region
- Monthly sales trend: SELECT DATE_TRUNC('month', date) as month, SUM(total_amount) FROM sales_data GROUP BY month ORDER BY month
- Top customers: SELECT c.name, SUM(s.total_amount) as total FROM customers c JOIN sales_data s ON c.id = s.customer_id GROUP BY c.id, c.name ORDER BY total DESC
- Product performance: SELECT p.name, p.category, SUM(s.quantity) as units_sold, SUM(s.total_amount) as revenue FROM products p JOIN sales_data s ON p.id = s.product_id GROUP BY p.id, p.name, p.category
"""
