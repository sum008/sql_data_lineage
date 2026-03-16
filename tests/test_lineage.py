import pytest
from lineage.extractor import extract_lineage


def test_simple_insert():

    sql = """
    INSERT INTO sales_summary
    SELECT customer_id, amount
    FROM orders
    """

    result = extract_lineage(sql)

    assert result["target_table"] == "sales_summary"
    assert result["source_tables"] == ["orders"]


def test_join_lineage():

    sql = """
    INSERT INTO sales_summary
    SELECT o.customer_id, o.amount
    FROM orders o
    JOIN customers c ON o.customer_id = c.id
    """

    result = extract_lineage(sql)

    assert result["target_table"] == "sales_summary"
    assert set(result["source_tables"]) == {"orders", "customers"}


def test_cte_lineage():

    sql = """
    WITH temp AS (
        SELECT * FROM orders
    )
    CREATE TABLE sales_summary AS
    SELECT customer_id FROM temp
    """

    result = extract_lineage(sql)

    assert result["target_table"] == "sales_summary"
    assert result["source_tables"] == ["orders"]


def test_nested_query():

    sql = """
    CREATE TABLE sales_summary AS
    SELECT *
    FROM (
        SELECT * FROM orders
        UNION ALL
        SELECT * FROM order_fact
    ) t
    """

    result = extract_lineage(sql)

    assert result["target_table"] == "sales_summary"
    assert set(result["source_tables"]) == {"orders", "order_fact"}


def test_merge_statement():

    sql = """
    MERGE INTO sales_summary s
    USING orders o
    ON s.customer_id = o.customer_id
    WHEN MATCHED THEN
        UPDATE SET revenue = o.amount
    """

    result = extract_lineage(sql)

    assert result["target_table"] == "sales_summary"
    assert result["source_tables"] == ["orders"]

def test_complex_nested_query():

    sql = """
    with cte1 as (
    select cf.customer_name, cf.customer_address, c.amount, c.quantity,c.customer_id 
    from customers_info cf 
    right join (
        select 
            o.customer_id,
            o.amount,
            o.quantity
        from (
            select customer_id, amount, quantity from orders where order_date >= '2024-01-01'
            union all
            select customer_id, amount, quantity from order_fact where order_date < '2024-01-01'
        ) o
        join customers c 
        on o.customer_id = c.id
    ) c 
    on cf.customer_id = c.customer_id
    )
    create table sales_summary
    SELECT 
        c.customer_id,
        SUM(c.amount) AS revenue,
        SUM(c.quantity) AS total_quantity
    FROM cte1 c
    GROUP BY c.customer_id
    """

    result = extract_lineage(sql)

    assert result["target_table"] == "sales_summary"

    assert set(result["source_tables"]) == {
        "customers_info",
        "orders",
        "order_fact",
        "customers",
    }

def test_multiple_ctes():

    sql = """
    with cte as (
    select 
        o.customer_id,
        o.amount,
        o.quantity
    from orders o
    join customers c 
    on o.customer_id = c.id
    ),
    cte1 as (
    select cf.customer_name, cf.customer_address, c.amount, c.quantity,c.customer_id 
    from customers_info cf right join cte c 
    on cf.customer_id = c.customer_id
    )
    create table sales_summary
    SELECT 
        c.customer_id,
        SUM(c.amount) AS revenue,
        SUM(c.quantity) AS total_quantity,
        SUM(c.amount) / NULLIF(SUM(c.quantity), 0) AS avg_price
    FROM cte1 c
    GROUP BY c.customer_id
    """

    result = extract_lineage(sql)

    assert result["target_table"] == "sales_summary"
    assert set(result["source_tables"]) == {
        "orders",
        "customers",
        "customers_info"
    }

def test_union_all_with_cte():

    sql = """
    with cte1 as (
    select cf.customer_name, cf.customer_address, c.amount, c.quantity,c.customer_id 
    from customers_info cf 
    right join (
    select 
        o.customer_id,
        o.amount,
        o.quantity
    from 
     (
     select customer_id, amount, quantity from orders where order_date >= '2024-01-01'
     union all
        select customer_id, amount, quantity from order_fact where order_date < '2024-01-01'
     ) o
    join customers c 
    on o.customer_id = c.id
    ) c 
    on cf.customer_id = c.customer_id
    )
    create table sales_summary
    SELECT 
        c.customer_id,
        SUM(c.amount) AS revenue,
        SUM(c.quantity) AS total_quantity,
        SUM(c.amount) / NULLIF(SUM(c.quantity), 0) AS avg_price
    FROM cte1 c
    GROUP BY c.customer_id
    """

    result = extract_lineage(sql)

    assert result["target_table"] == "sales_summary"
    assert set(result["source_tables"]) == {
        "orders",
        "order_fact",
        "customers",
        "customers_info"
    }

def test_column_lineage_simple():

    sql = """
    INSERT INTO sales_summary
    SELECT customer_id, amount
    FROM orders
    """

    result = extract_lineage(sql)

    expected_columns = [
        {
            "target_column": "customer_id",
            "source_columns": ["customer_id"]
        },
        {
            "target_column": "amount",
            "source_columns": ["amount"]
        }
    ]

    assert result["column_lineage"] == expected_columns

def test_column_lineage_alias():

    sql = """
    INSERT INTO sales_summary
    SELECT 
        customer_id AS cid,
        amount AS revenue
    FROM orders
    """

    result = extract_lineage(sql)

    expected_columns = [
        {
            "target_column": "cid",
            "source_columns": ["customer_id"]
        },
        {
            "target_column": "revenue",
            "source_columns": ["amount"]
        }
    ]

    assert result["column_lineage"] == expected_columns

def test_column_lineage_aggregation():

    sql = """
    CREATE TABLE sales_summary AS
    SELECT 
        customer_id,
        SUM(amount) AS revenue
    FROM orders
    GROUP BY customer_id
    """

    result = extract_lineage(sql)

    expected_columns = [
        {
            "target_column": "customer_id",
            "source_columns": ["customer_id"]
        },
        {
            "target_column": "revenue",
            "source_columns": ["amount"]
        }
    ]

    assert result["column_lineage"] == expected_columns

def test_column_lineage_expression():

    sql = """
    CREATE TABLE sales_summary AS
    SELECT 
        customer_id,
        amount / quantity AS avg_price
    FROM orders
    """

    result = extract_lineage(sql)

    expected_columns = [
        {
            "target_column": "customer_id",
            "source_columns": ["customer_id"]
        },
        {
            "target_column": "avg_price",
            "source_columns": ["amount", "quantity"]
        }
    ]

    assert result["column_lineage"] == expected_columns

def test_column_lineage_join():

    sql = """
    CREATE TABLE sales_summary AS
    SELECT 
        o.customer_id,
        o.amount,
        c.customer_name
    FROM orders o
    JOIN customers c 
    ON o.customer_id = c.id
    """

    result = extract_lineage(sql)

    expected_columns = [
        {
            "target_column": "customer_id",
            "source_columns": ["o.customer_id"]
        },
        {
            "target_column": "amount",
            "source_columns": ["o.amount"]
        },
        {
            "target_column": "customer_name",
            "source_columns": ["c.customer_name"]
        }
    ]

    assert result["column_lineage"] == expected_columns

def test_column_lineage_complex():

    sql = """
    CREATE TABLE sales_summary AS
    SELECT 
        customer_id,
        SUM(amount) AS revenue,
        SUM(quantity) AS total_quantity,
        SUM(amount) / NULLIF(SUM(quantity),0) AS avg_price
    FROM orders
    GROUP BY customer_id
    """

    result = extract_lineage(sql)

    assert result["target_table"] == "sales_summary"

    # check specific column lineage
    avg_price = next(
        c for c in result["column_lineage"]
        if c["target_column"] == "avg_price"
    )

    assert set(avg_price["source_columns"]) == {"amount", "quantity"}