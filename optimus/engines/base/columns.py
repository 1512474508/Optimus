import string
from abc import abstractmethod, ABC
from enum import Enum

import numpy as np

from optimus.helpers.columns import parse_columns, check_column_numbers, prepare_columns
from optimus.helpers.constants import RELATIVE_ERROR
from optimus.helpers.converter import format_dict
# This implementation works for Spark, Dask, dask_cudf
from optimus.helpers.core import val_to_list
from optimus.helpers.raiseit import RaiseIt


class BaseColumns(ABC):
    """Base class for all Cols implementations"""

    def __init__(self, df):
        self.df = df

    @staticmethod
    @abstractmethod
    def append(*args, **kwargs):
        pass

    @staticmethod
    @abstractmethod
    def select(columns="*", regex=None, data_type=None, invert=False, accepts_missing_cols=False) -> str:
        pass

    @staticmethod
    @abstractmethod
    def copy(input_cols, output_cols=None, columns=None):
        pass

    @staticmethod
    @abstractmethod
    def to_timestamp(input_cols, date_format=None, output_cols=None):
        pass

    @staticmethod
    @abstractmethod
    def apply_expr(input_cols, func=None, args=None, filter_col_by_dtypes=None, output_cols=None,
                   meta=None):
        pass

    @staticmethod
    @abstractmethod
    def apply(input_cols, func=None, func_return_type=None, args=None, func_type=None, when=None,
              filter_col_by_dtypes=None, output_cols=None, skip_output_cols_processing=False,
              meta="apply"):
        pass

    @staticmethod
    @abstractmethod
    def apply_by_dtypes(columns, func, func_return_type, args=None, func_type=None, data_type=None):
        pass

    @staticmethod
    @abstractmethod
    def set(output_col, value=None):
        pass

    @staticmethod
    @abstractmethod
    def slice(input_cols, output_cols, start, stop, step):
        pass

    @staticmethod
    @abstractmethod
    def extract(input_cols, output_cols, regex):
        pass

    @staticmethod
    @abstractmethod
    def rename(*args, **kwargs) -> Enum:
        pass

    def parse_profiler_dtypes(self, col_data_type):
        """
        Parse a spark data type to a profiler data type
        :return:
        """
        df = self.df
        columns = {}
        for k, v in col_data_type.items():
            # Initialize values to 0
            result_default = {data_type: 0 for data_type in df.constants.DTYPES_TO_PROFILER.keys()}
            for k1, v1 in v.items():
                # print(k1, v1)
                for k2, v2 in df.constants.DTYPES_TO_PROFILER.items():
                    # print(k1 ,k2)
                    if k1 in df.constants.DTYPES_TO_PROFILER[k2]:
                        result_default[k2] = result_default[k2] + v1
            columns[k] = result_default
        # print("AAAA",columns)
        return columns

    @staticmethod
    @abstractmethod
    def cast(input_cols=None, dtype=None, output_cols=None, columns=None):
        pass

    @staticmethod
    @abstractmethod
    def astype(*args, **kwargs):
        pass

    @staticmethod
    @abstractmethod
    def count_mismatch(columns_mismatch: dict = None):
        pass

    def round(self, input_cols, decimals=1, output_cols=None):
        """

        :param input_cols:
        :param decimals:
        :param output_cols:
        :return:
        """
        df = self.df
        columns = prepare_columns(df, input_cols, output_cols)
        for input_col, output_col in columns:
            df[output_col] = df[input_col].round(decimals)
        return df

    def ceil(self, input_cols, output_cols=None):
        """

        :param input_cols:
        :param output_cols:
        :return:
        """
        df = self.df
        columns = prepare_columns(df, input_cols, output_cols)
        for input_col, output_col in columns:
            df[output_col] = df[input_col].map(np.ceil)
        return df

    def floor(self, input_cols, output_cols=None):
        """

        :param input_cols:
        :param decimals:
        :param output_cols:
        :return:
        """
        df = self.df
        columns = prepare_columns(df, input_cols, output_cols)
        for input_col, output_col in columns:
            df[output_col] = df[input_col].map(np.floor)
        return df

    def patterns(self, input_cols, output_cols=None, mode=0):
        """
        Replace alphanumeric and punctuation chars for canned chars. We aim to help to find string patterns
        c = Any alpha char in lower or upper case form
        l = Any alpha char in lower case
        U = Any alpha char in upper case
        * = Any alphanumeric in lower or upper case
        ! = Any punctuation

        :param input_cols:
        :param output_cols:
        :param mode:
        0: Identify lower, upper, digits. Except spaces and special chars.
        1: Identify chars, digits. Except spaces and special chars
        2: Identify Any alphanumeric. Except spaces and special chars
        3: Identify alphanumeric and special chars. Except white spaces
        :return:
        """
        df = self.df

        def split(word):
            return [char for char in word]

        alpha_lower = split(string.ascii_lowercase)
        alpha_upper = split(string.ascii_uppercase)
        digits = split(string.digits)
        punctuation = split(string.punctuation)

        if mode == 0:
            search_by = alpha_lower + alpha_upper + digits
            replace_by = ["l"] * len(alpha_lower) + ["U"] * len(alpha_upper) + ["#"] * len(digits)
        elif mode == 1:
            search_by = alpha_lower + alpha_upper + digits
            replace_by = ["c"] * len(alpha_lower) + ["c"] * len(alpha_upper) + ["#"] * len(digits)
        elif mode == 2:
            search_by = alpha_lower + alpha_upper + digits
            replace_by = ["*"] * len(alpha_lower + alpha_upper + digits)
        elif mode == 3:
            search_by = alpha_lower + alpha_upper + digits + punctuation
            replace_by = ["*"] * len(alpha_lower + alpha_upper + digits + punctuation)

        result = {}
        columns = prepare_columns(df, input_cols, output_cols)

        for input_col, output_col in columns:
            result[input_col] = df[input_col].str.replace(search_by,
                                                          replace_by).value_counts().to_pandas().to_dict()
        return result

    def groupby(self, by, agg, order="asc", *args, **kwargs):
        """
        This helper function aims to help managing columns name in the aggregation output.
        Also how to handle ordering columns because dask can order columns
        :param by:
        :param agg:
        :param args:
        :param kwargs:
        :return:
        """
        df = self.df
        compact = {}
        for col_agg in list(agg.values()):
            for col_name, _agg in col_agg.items():
                compact.setdefault(col_name, []).append(_agg)

        df = df.groupby(by=by).agg(compact).reset_index()
        df.columns = [by] + list(agg.keys())

        return df

    def join(self, df_right, *args, **kwargs):
        """

        :param df_right:
        :param args:
        :param kwargs:
        how{‘left’, ‘right’, ‘outer’, ‘inner’}, default ‘left’
        :return:
        """
        df = self.df
        col_on = kwargs.get("on")
        col_left = kwargs.get("left_on")
        col_right = kwargs.get("right_on")

        # print(col_on)

        col_index_left = None
        col_index_right = None

        if col_on:
            col_index_left = col_on
            col_index_right = col_on

        elif col_left and col_right:
            col_index_left = col_left
            col_index_right = col_right

        # print(col_index_right, col_index_left)
        df = df.set_index(col_index_left)
        df_right.set_index(col_index_right)

        # print(df.index.name)
        ## Create a index using the join column to speed up the join in big datasets
        df = df.merge(df_right, *args, **kwargs)
        return df

    def move(self, column, position, ref_col=None):
        """
        Move a column to specific position
        :param column: Column to be moved
        :param position: Column new position. Accepts 'after', 'before', 'beginning', 'end'
        :param ref_col: Column taken as reference
        :return: Spark DataFrame
        """

        df = self.df
        # Check that column is a string or a list
        column = parse_columns(df, column)
        ref_col = parse_columns(df, ref_col)

        # Get dataframe columns
        columns = df.cols.names()

        # Get source and reference column index position
        new_index = columns.index(ref_col[0])

        # Column to move
        column_to_move_index = columns.index(column[0])

        if position == 'after':
            # Check if the movement is from right to left:
            if new_index < column_to_move_index:
                new_index = new_index + 1
        elif position == 'before':  # If position if before:
            if new_index >= column_to_move_index:  # Check if the movement if from right to left:
                new_index = new_index - 1
        elif position == 'beginning':
            new_index = 0
        elif position == 'end':
            new_index = len(columns)
        else:
            RaiseIt.value_error(position, ["after", "before", "beginning", "end"])

        # Move the column to the new place
        columns.insert(new_index, columns.pop(column_to_move_index))  # insert and delete a element

        return df[columns]

    @staticmethod
    @abstractmethod
    def keep(columns=None, regex=None):
        pass

    def sort(self, columns=None, order: [str, list] = "asc"):
        """
        Sort data frames columns asc or desc
        :param order: 'asc' or 'desc' accepted
        :param columns:
        :return: Spark DataFrame
        """
        df = self.df
        if columns is None:
            _reverse = None
            if order == "asc":
                _reverse = False
            elif order == "desc":
                _reverse = True
            else:
                RaiseIt.value_error(order, ["asc", "desc"])

            columns = df.cols.names()
            columns.sort(key=lambda v: v.upper(), reverse=_reverse)

        return df.cols.select(columns)

    @staticmethod
    @abstractmethod
    def drop(columns=None, regex=None, data_type=None):
        pass

    def dtypes(self, columns="*"):
        """
        Return the column(s) data type as string
        :param columns: Columns to be processed
        :return:
        """
        df = self.df
        columns = parse_columns(df, columns)
        data_types = ({k: str(v) for k, v in dict(df.dtypes).items()})
        return format_dict({col_name: data_types[col_name] for col_name in columns})

    def schema_dtype(self, columns="*"):
        """
        Return the column(s) data type as Type
        :param columns: Columns to be processed
        :return:
        """
        df = self.df
        columns = parse_columns(df, columns)
        return format_dict({col_name: np.dtype(df[col_name]).type for col_name in columns})

    @staticmethod
    @abstractmethod
    def create_exprs(columns, funcs, *args):
        pass

    def agg_exprs(self, columns, funcs, *args):
        """
        Create and run aggregation
        :param columns:
        :param funcs:
        :param args:
        :return:
        """
        return self.exec_agg(self.create_exprs(columns, funcs, *args))

    @staticmethod
    @abstractmethod
    def exec_agg(exprs):
        pass

    def min(self, columns):
        df = self.df
        return self.agg_exprs(columns, df.functions.min)

    def max(self, columns):
        df = self.df
        return self.agg_exprs(columns, df.functions.max)

    def range(self, columns):
        df = self.df
        return self.agg_exprs(columns, df.functions.range_agg)

    def percentile(self, columns, values=None, relative_error=RELATIVE_ERROR):
        df = self.df
        # values = [str(v) for v in values]
        if values is None:
            values = [0.5]
        return self.agg_exprs(columns, df.functions.percentile_agg, df, values, relative_error)

    def median(self, columns, relative_error=RELATIVE_ERROR):
        return format_dict(self.percentile(columns, [0.5], relative_error))

    # Descriptive Analytics
    # TODO: implement double MAD http://eurekastatistics.com/using-the-median-absolute-deviation-to-find-outliers/

    def mad(self, columns, relative_error=RELATIVE_ERROR, more=None):
        df = self.df
        columns = parse_columns(df, columns, filter_by_column_dtypes=df.constants.NUMERIC_TYPES)
        check_column_numbers(columns, "*")

        result = {}
        funcs = [df.functions.mad_agg]

        return self.agg_exprs(columns, funcs, more)

    def std(self, columns):
        df = self.df
        columns = parse_columns(df, columns, filter_by_column_dtypes=df.constants.NUMERIC_TYPES)
        check_column_numbers(columns, "*")
        return self.agg_exprs(columns, df.functions.stddev)

    def kurt(self, columns):
        df = self.df

        columns = parse_columns(df, columns, filter_by_column_dtypes=df.constants.NUMERIC_TYPES)
        check_column_numbers(columns, "*")

        return self.agg_exprs(columns, df.functions.kurtosis)

    def mean(self, columns):
        df = self.df
        columns = parse_columns(df, columns, filter_by_column_dtypes=df.constants.NUMERIC_TYPES)
        check_column_numbers(columns, "*")

        return self.agg_exprs(columns, df.functions.mean)

    def skewness(self, columns):
        df = self.df
        columns = parse_columns(df, columns, filter_by_column_dtypes=df.constants.NUMERIC_TYPES)
        check_column_numbers(columns, "*")

        return self.agg_exprs(columns, df.functions.skewness)

    def sum(self, columns):
        df = self.df
        columns = parse_columns(df, columns, filter_by_column_dtypes=df.constants.NUMERIC_TYPES)
        check_column_numbers(columns, "*")

        return format_dict(self.agg_exprs(columns, df.functions.sum))

    def variance(self, columns):
        df = self.df
        columns = parse_columns(df, columns, filter_by_column_dtypes=df.constants.NUMERIC_TYPES)
        check_column_numbers(columns, "*")

        return format_dict(self.agg_exprs(columns, df.functions.variance))

    @staticmethod
    @abstractmethod
    def abs(columns):
        pass

    @staticmethod
    @abstractmethod
    def mode(columns):
        pass

    @staticmethod
    @abstractmethod
    def lower(input_cols, output_cols=None):
        pass

    @staticmethod
    @abstractmethod
    def upper(input_cols, output_cols=None):
        pass

    @staticmethod
    @abstractmethod
    def trim(input_cols, output_cols=None):
        pass

    @staticmethod
    @abstractmethod
    def reverse(input_cols, output_cols=None):
        pass

    @staticmethod
    @abstractmethod
    def remove(columns, search=None, search_by="chars", output_cols=None):
        pass

    @staticmethod
    @abstractmethod
    def remove_accents(input_cols, output_cols=None):
        pass

    @staticmethod
    @abstractmethod
    def remove_special_chars(input_cols, output_cols=None):
        pass

    @staticmethod
    @abstractmethod
    def remove_white_spaces(input_cols, output_cols=None):
        pass

    @staticmethod
    @abstractmethod
    def date_transform(input_cols, current_format=None, output_format=None, output_cols=None):
        pass

    @staticmethod
    @abstractmethod
    def years_between(input_cols, date_format=None, output_cols=None):
        pass

    @staticmethod
    @abstractmethod
    def replace(input_cols, search=None, replace_by=None, search_by="chars", output_cols=None):
        pass

    @staticmethod
    @abstractmethod
    def replace_regex(input_cols, regex=None, value=None, output_cols=None):
        pass

    @staticmethod
    @abstractmethod
    def impute(input_cols, data_type="continuous", strategy="mean", output_cols=None):
        pass

    @staticmethod
    @abstractmethod
    def fill_na(input_cols, value=None, output_cols=None):
        pass

    @staticmethod
    @abstractmethod
    def is_na(input_cols, output_cols=None):
        pass

    @staticmethod
    def count(self):
        pass

    @staticmethod
    @abstractmethod
    def count_na(columns):
        pass

    @staticmethod
    @abstractmethod
    def count_zeros(columns):
        pass

    @staticmethod
    @abstractmethod
    def count_uniques(columns, estimate=True):
        pass

    @staticmethod
    @abstractmethod
    def value_counts(columns):
        pass

    @staticmethod
    @abstractmethod
    def unique(columns):
        pass

    @staticmethod
    @abstractmethod
    def nunique(*args, **kwargs):
        pass

    @staticmethod
    @abstractmethod
    def select_by_dtypes(data_type):
        pass

    @staticmethod
    @abstractmethod
    def _math(columns, operator, new_column):
        """
        Helper to process arithmetic operation between columns. If a
        :param columns: Columns to be used to make the calculation
        :param operator: A lambda function
        :return:
        """

        # df = self
        # columns = parse_columns(df, columns, filter_by_column_dtypes=df.constants.NUMERIC_TYPES)
        # check_column_numbers(columns, "*")
        #
        # for col_name in columns:
        #     df = df.cols.cast(col_name, "float")
        #
        # if len(columns) < 2:
        #     raise Exception("Error: 2 or more columns needed")
        #
        # columns = list(map(lambda x: F.col(x), columns))
        # expr = reduce(operator, columns)
        #
        # return df.withColumn(new_column, expr)
        pass

    @staticmethod
    def add(columns, col_name="sum"):
        """
        Add two or more columns
        :param columns: '*', list of columns names or a single column name
        :param col_name:
        :return:
        """

        return BaseColumns._math(columns, lambda x, y: x + y, col_name)

    @staticmethod
    def sub(columns, col_name="sub"):
        """
        Subs two or more columns
        :param columns: '*', list of columns names or a single column name
        :param col_name:
        :return:
        """
        return BaseColumns._math(columns, lambda x, y: x - y, col_name)

    @staticmethod
    def mul(columns, col_name="mul"):
        """
        Multiply two or more columns
        :param columns: '*', list of columns names or a single column name
        :param col_name:
        :return:
        """
        return BaseColumns._math(columns, lambda x, y: x * y, col_name)

    @staticmethod
    def div(columns, col_name="div"):
        """
        Divide two or more columns
        :param columns: '*', list of columns names or a single column name
        :param col_name:
        :return:
        """
        return BaseColumns._math(columns, lambda x, y: x / y, col_name)

    @staticmethod
    @abstractmethod
    def z_score(input_cols, output_cols=None):
        pass

    @staticmethod
    @abstractmethod
    def min_max_scaler(input_cols, output_cols=None):
        pass

    @staticmethod
    @abstractmethod
    def standard_scaler(input_cols, output_cols=None):
        pass

    @staticmethod
    @abstractmethod
    def max_abs_scaler(input_cols, output_cols=None):
        pass

    @staticmethod
    @abstractmethod
    def iqr(columns, more=None, relative_error=None):
        pass

    @staticmethod
    @abstractmethod
    def nest(input_cols, shape="string", separator="", output_col=None):
        pass

    @staticmethod
    @abstractmethod
    def unnest(input_cols, separator=None, splits=None, index=None, output_cols=None, drop=False):
        pass

    @staticmethod
    @abstractmethod
    def cell(column):
        pass

    @staticmethod
    @abstractmethod
    def scatter(columns, buckets=10):
        pass

    def hist(self, columns, buckets=20):
        df = self.df
        result = self.agg_exprs(columns, df.functions.hist_agg, df, buckets, None)
        return result

    @staticmethod
    @abstractmethod
    def frequency_by_group(columns, n=10, percentage=False, total_rows=None):
        pass

    @staticmethod
    @abstractmethod
    def count_mismatch(columns_mismatch: dict = None):
        pass

    @staticmethod
    @abstractmethod
    def count_by_dtypes(columns, infer=False, str_funcs=None, int_funcs=None):
        pass

    @staticmethod
    @abstractmethod
    def frequency(columns, n=10, percentage=False, total_rows=None):
        pass

    @staticmethod
    @abstractmethod
    def correlation(input_cols, method="pearson", output="json"):
        pass

    @staticmethod
    @abstractmethod
    def boxplot(columns):
        # """
        # Output values frequency in json format
        # :param columns: Columns to be processed
        # :return:
        # """
        # df = self
        # columns = parse_columns(df, columns)
        #
        # for col_name in columns:
        #     iqr = df.cols.iqr(col_name, more=True)
        #     lb = iqr["q1"] - (iqr["iqr"] * 1.5)
        #     ub = iqr["q3"] + (iqr["iqr"] * 1.5)
        #
        #     _mean = df.cols.mean(columns)
        #
        #     query = ((F.col(col_name) < lb) | (F.col(col_name) > ub))
        #     fliers = collect_as_list(df.rows.select(query).cols.select(col_name).limit(1000))
        #     stats = [{'mean': _mean, 'med': iqr["q2"], 'q1': iqr["q1"], 'q3': iqr["q3"], 'whislo': lb, 'whishi': ub,
        #               'fliers': fliers, 'label': one_list_to_val(col_name)}]
        #
        #     return stats
        pass

    def names(self, col_names="*", by_dtypes=None, invert=False):
        columns = parse_columns(self.df, col_names, filter_by_column_dtypes=by_dtypes, invert=invert)
        return columns

    @staticmethod
    @abstractmethod
    def qcut(columns, num_buckets, handle_invalid="skip"):
        pass

    @staticmethod
    @abstractmethod
    def clip(columns, lower_bound, upper_bound):
        pass

    @staticmethod
    @abstractmethod
    def values_to_cols(input_cols):
        pass

    @staticmethod
    @abstractmethod
    def string_to_index(input_cols=None, output_cols=None, columns=None):
        pass

    @staticmethod
    @abstractmethod
    def index_to_string(input_cols=None, output_cols=None, columns=None):
        pass

    @staticmethod
    @abstractmethod
    def bucketizer(input_cols, splits, output_cols=None):
        pass

    @staticmethod
    @abstractmethod
    def set_meta(col_name, spec=None, value=None, missing=dict):
        pass

    @staticmethod
    @abstractmethod
    def get_meta(col_name, spec=None):
        pass
