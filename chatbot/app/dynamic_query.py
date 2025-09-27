import pandas as pd

def run_dynamic_query(df: pd.DataFrame, query_json: dict):
    """
    Executes the parsed JSON query on the DataFrame.
    Returns result table or KPI.
    """
    df_copy = df.copy()

    # Apply filters
    filters = query_json.get("filters") or {}
    for k, v in filters.items():
        if k in df_copy.columns:
            df_copy = df_copy[df_copy[k] == v]

    group_by = query_json.get("group_by")
    agg_column = query_json.get("column")
    aggregation = query_json.get("aggregation")

    result = df_copy

    if group_by and aggregation and agg_column:
        if aggregation.lower() in ["sum", "mean", "count", "max", "min"]:
            result = df_copy.groupby(group_by)[agg_column].agg(aggregation.lower()).reset_index()
    elif aggregation and agg_column:
        func = aggregation.lower()
        if func == "sum":
            result = df_copy[agg_column].sum()
        elif func == "mean":
            result = df_copy[agg_column].mean()
        elif func == "count":
            result = df_copy[agg_column].count()
        elif func == "max":
            result = df_copy[agg_column].max()
        elif func == "min":
            result = df_copy[agg_column].min()

    return result.to_dict(orient="records") if isinstance(result, pd.DataFrame) else {"value": result}
