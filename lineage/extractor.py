import sqlglot
from sqlglot import exp

def extract_lineage(sql_script, target_table=None):
    results = []
    statements = sqlglot.parse(sql_script)
    for stmt in statements:
        lineage = extract(stmt.sql(), target_table)
        if lineage:
            results.append(lineage)
    return results


def extract(sql, target_table_to_find):

    parsed = sqlglot.parse_one(sql)

    target_table = None
    source_tables = set()
    cte_sources = set()
    column_lineage = []

    target_table = normalize_table_name(find_target(parsed))

    if target_table_to_find and target_table != target_table_to_find:
        return None

    for table in parsed.find_all(exp.Table):
        source_tables.add(normalize_table_name(table.name))

    for cte in parsed.find_all(exp.CTE):
        cte_sources.add(cte.alias)

    if target_table in source_tables:
        source_tables.remove(target_table)

    source_tables = source_tables - cte_sources

    alias_map = {}

    for table in parsed.find_all(exp.Table):
        if table.alias:
            alias_map[table.alias] = table.name

    select = parsed.find(exp.Select)

    if select:
        for projection in select.expressions:

            if isinstance(projection, exp.Alias):

                target_column = projection.alias

                source_columns = []
                for col in projection.find_all(exp.Column):
                    source_columns.append(
                        f"{alias_map.get(col.table, col.table)}.{col.name}" if col.table else col.name
                    )

                column_lineage.append(
                    {
                        "target_column": target_column,
                        "source_columns": source_columns,
                    }
                )

            elif isinstance(projection, exp.Column):

                column_lineage.append(
                    {
                        "target_column": projection.name,
                        "source_columns": [
                            f"{alias_map.get(projection.table, projection.table)}.{projection.name}"
                            if projection.table
                            else projection.name
                        ],
                    }
                )

    return {
        "target_table": target_table,
        "source_tables": sorted(list(source_tables)),
        "cte_sources": sorted(list(cte_sources)),
        "column_lineage": column_lineage,
    }

def find_target(parsed):
    if isinstance(parsed, exp.Insert):
        target_table = parsed.this.name

    if isinstance(parsed, exp.Create):
        target_table = parsed.this.name

    if isinstance(parsed, exp.Update):
        target_table = parsed.this.name

    if isinstance(parsed, exp.Delete):
        target_table = parsed.this.name

    if isinstance(parsed, exp.Merge):
        target_table = parsed.this.name

    return target_table

def normalize_table_name(name):
    return name.split(".")[-1].lower()

if __name__ == "__main__":
    # sql = """
    # with cte as (
    # select 
    #     o.customer_id,
    #     o.amount,
    #     o.quantity
    # from orders o
    # join customers c 
    # on o.customer_id = c.id
    # ),
    # cte1 as (
    # select cf.customer_name, cf.customer_address, c.amount, c.quantity,c.customer_id 
    # from customers_info cf right join cte c 
    # on cf.customer_id = c.customer_id
    # )
    # create table sales_summary
    # SELECT 
    #     c.customer_id,
    #     SUM(c.amount) AS revenue,
    #     SUM(c.quantity) AS total_quantity,
    #     SUM(c.amount) / NULLIF(SUM(c.quantity), 0) AS avg_price
    # FROM cte1 c
    # GROUP BY c.customer_id
    # """

    # sql = """
    # with cte1 as (
    # select cf.customer_name, cf.customer_address, c.amount, c.quantity,c.customer_id 
    # from customers_info cf 
    # right join (
    # select 
    #     o.customer_id,
    #     o.amount,
    #     o.quantity
    # from orders o
    # join customers c 
    # on o.customer_id = c.id
    # ) c 
    # on cf.customer_id = c.customer_id
    # )
    # create table sales_summary
    # SELECT 
    #     c.customer_id,
    #     SUM(c.amount) AS revenue,
    #     SUM(c.quantity) AS total_quantity,
    #     SUM(c.amount) / NULLIF(SUM(c.quantity), 0) AS avg_price
    # FROM cte1 c
    # GROUP BY c.customer_id
    # """

    sql = """
    with cte1 as (
    select cf.customer_name, cf.customer_address, c.amount, c.quantity,c.customer_id 
    from customers_info cf 
    right join (
    select 
        customer_id,
        amount,
        quantity
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

    # sql = """
        # Merge into sales_summary s
        # using (
        #     with cte as (
        #         select 
        #             o.customer_id,
        #             o.amount,
        #             o.quantity
        #             from orders o
        #             join customers c 
        #             on o.customer_id = c.id
        #     ),
        # cte1 as (
        #     select cf.customer_name, cf.customer_address, c.amount, c.quantity,c.customer_id 
        #     from customers_info cf right join cte c 
        #     on cf.customer_id = c.customer_id
        # )
        # SELECT 
        #     c.customer_id,
        #     SUM(c.amount) AS revenue,
        #     SUM(c.quantity) AS total_quantity,
        #     SUM(c.amount) / NULLIF(SUM(c.quantity), 0) AS avg_price
        # FROM cte1 c
        # GROUP BY c.customer_id
        # ) src
        # on s.customer_id = src.customer_id
        # when matched then 
        #     update set s.revenue = src.revenue, s.total_quantity = src.total_quantity, s.avg_price = src.avg_price
        # when not matched then 
        #     insert (customer_id, revenue, total_quantity, avg_price) values (src.customer_id, src.revenue, src.total_quantity, src.avg_price)"""

    result = extract_lineage(sql)

    print(result)