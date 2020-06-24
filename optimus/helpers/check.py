"""
Helpers to check if an object match a date type
"""
import re

import pandas as pd

from optimus.helpers.core import val_to_list, one_list_to_val
# TODO: can be confused with is_type
from optimus.helpers.parser import parse_dtypes
from optimus.helpers.raiseit import RaiseIt


def has_(value, _type):
    """
    Check if a list has a element of a specific data type
    :param value: list
    :param _type: data type to check
    :return:
    """
    return any(isinstance(elem, _type) for elem in value)


def is_column_a(df, column=None, dtypes="str"):
    """
    Check if column match a list of data types
    :param df: spark or dask dataframe
    :param column: column to be compared with
    :param dtypes: types to be checked
    :return:
    """
    column = val_to_list(column)

    if len(column) > 1:
        RaiseIt.length_error(column, 1)
    # print("DTYPES", dtypes)
    data_type = tuple(val_to_list(parse_dtypes(df, dtypes)))
    column = one_list_to_val(column)

    # Filter columns by data type
    v = df.cols.schema_dtype(column)

    if is_spark_dataframe(df):
        result = isinstance(v, data_type)
    elif is_dask_dataframe(df):
        result = v in data_type
    else:
        result = None
    return result


#
# def is_column_a(df, column, dtypes):
#     """
#     Check if column match a list of data types
#     :param df: spark
#     :param column: column to be compared with
#     :param dtypes: types to be checked
#     :return:
#     """
#     column = val_to_list(column)
#
#     if len(column) > 1:
#         RaiseIt.length_error(column, 1)
#
#     data_type = tuple(val_to_list(parse_spark_dtypes(df, dtypes)))
#     column = one_list_to_val(column)
#
#     # Filter columns by data type
#     return isinstance(df.schema[column].dataType, data_type)
# def is_cudf_series(value):
#     return cudf.core.series.Series

def is_cudf_dataframe(value):
    from cudf.core import DataFrame as CUDFDataFrame
    return isinstance(value, CUDFDataFrame)


def is_cudf_series(value):
    import cudf
    return isinstance(value, cudf.core.series.Series)


def is_dask_cudf_dataframe(value):
    from dask_cudf.core import DataFrame as DaskCUDFDataFrame
    return isinstance(value, DaskCUDFDataFrame)


def is_dask_cudf_series(value):
    from dask_cudf.core import Series as DaskCUDFSeries
    return isinstance(value, DaskCUDFSeries)


def is_dask_dataframe(value):
    """
    Check if an object is a Dask DataFrame
    :param value:
    :return:
    """
    from dask.dataframe.core import DataFrame as DaskDataFrame
    return isinstance(value, DaskDataFrame)


def is_dask_series(value):
    """
    Check if an object is a Dask DataFrame
    :param value:
    :return:
    """
    from dask.dataframe.core import Series as DaskSeries
    return isinstance(value, DaskSeries)


def is_spark_dataframe(value):
    """
    Check if an object is a Spark DataFrame
    :param value:
    :return:
    """

    from pyspark.sql import DataFrame as SparkDataFrame
    return isinstance(value, SparkDataFrame)


def is_pandas_dataframe(value):
    """
    Check if an object is a Pandas DataFrame
    :param value:
    :return:
    """
    return isinstance(value, pd.DataFrame)


def is_pandas_series(value):
    """
    Check if an object is a Pandas DataFrame
    :param value:
    :return:
    """
    return isinstance(value, pd.Series)


def is_url(value):
    regex = re.compile(
        r'^(?:http|ftp|hdfs)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return re.match(regex, value)


def equal_function(f1, f2):
    f2 = val_to_list(f2)
    for func in f2:
        if f1.__name__ == func.__name__:
            return True
    return False
