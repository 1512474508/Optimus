import functools
import operator

import pandas as pd
from multipledispatch import dispatch

from optimus.engines.base.meta import Meta
from optimus.engines.base.rows import BaseRows
from optimus.helpers.columns import parse_columns
from optimus.helpers.constants import Actions
from optimus.helpers.core import val_to_list, one_list_to_val
from optimus.helpers.raiseit import RaiseIt
from optimus.infer import is_list_of_str_or_int, is_list

DataFrame = pd.DataFrame


class Rows(BaseRows):
    def __init__(self, df):
        super(Rows, self).__init__(df)

    @staticmethod
    def create_id(column="id") -> DataFrame:
        pass

    def append(self, rows):
        """

        :param rows:
        :return:
        """
        df = self.root

        if is_list(rows):
            rows = pd.DataFrame(rows)
        # Can not concatenate dataframe with not string columns names

        rows.columns = df.cols.names()
        df = pd.concat([df.reset_index(drop=True), rows.reset_index(drop=True)], axis=0)
        return self.root.new(df)

        return df_list

    @dispatch(str, str)
    def sort(self, input_cols) -> DataFrame:
        df = self.root
        input_cols = parse_columns(df, input_cols)
        return df.rows.sort([(input_cols, "desc",)])

    @dispatch(str, str)
    def sort(self, columns, order="desc") -> DataFrame:
        """
        Sort column by row
        """
        df = self.root
        columns = parse_columns(df, columns)
        return df.rows.sort([(columns, order,)])

    @dispatch(list)
    def sort(self, col_sort) -> DataFrame:
        """
        Sort rows taking into account multiple columns
        :param col_sort: column and sort type combination (col_name, "asc")
        :type col_sort: list of tuples
        """
        # If a list of columns names are given order this by desc. If you need to specify the order of every
        # column use a list of tuples (col_name, "asc")
        df = self.root

        t = []
        if is_list_of_str_or_int(col_sort):
            for col_name in col_sort:
                t.append(tuple([col_name, "desc"]))
            col_sort = t

        for cs in col_sort:
            col_name = one_list_to_val(cs[0])
            order = cs[1]

            if order != "asc" and order != "desc":
                RaiseIt.value_error(order, ["asc", "desc"])

            df.meta = Meta.preserve(df.meta, None, Actions.SORT_ROW.value, col_name)

            df = df.sort_values(col_name, ascending=True if order == "asc" else False)

        return df

    def between(self, columns, lower_bound=None, upper_bound=None, invert=False, equal=False,
                bounds=None) -> DataFrame:
        """
        Trim values at input thresholds
        :param upper_bound:
        :param lower_bound:
        :param columns: Columns to be trimmed
        :param invert:
        :param equal:
        :param bounds:
        :return:
        """
        df = self.root
        # TODO: should process string or dates
        columns = parse_columns(df.data, columns, filter_by_column_dtypes=df.constants.NUMERIC_TYPES)
        if bounds is None:
            bounds = [(lower_bound, upper_bound)]

        def _between(_col_name):

            if invert is False and equal is False:
                op1 = operator.gt
                op2 = operator.lt
                opb = operator.__and__

            elif invert is False and equal is True:
                op1 = operator.ge
                op2 = operator.le
                opb = operator.__and__

            elif invert is True and equal is False:
                op1 = operator.lt
                op2 = operator.gt
                opb = operator.__or__

            elif invert is True and equal is True:
                op1 = operator.le
                op2 = operator.ge
                opb = operator.__or__

            sub_query = []
            for bound in bounds:
                _lower_bound, _upper_bound = bound
                sub_query.append(opb(op1(df[_col_name], _lower_bound), op2(df[_col_name], _upper_bound)))
            query = functools.reduce(operator.__or__, sub_query)

            return query

        # df = self
        for col_name in columns:
            df = df.rows.select(_between(col_name))
        df.meta = Meta.preserve(df.meta, None, Actions.DROP_ROW.value, df.cols.names())
        return self.root.new(df)

    def drop_by_dtypes(self, input_cols, data_type=None):
        df = self.root
        return df

    def drop_duplicates(self, subset=None) -> DataFrame:
        """
        Drop duplicates values in a dataframe
        :param subset: List of columns to make the comparison, this only  will consider this subset of columns,
        :return: Return a new DataFrame with duplicate rows removed
        :return:
        """
        df = self.root
        dfd = df.data
        subset = parse_columns(df, subset)
        subset = val_to_list(subset)
        dfd = dfd.drop_duplicates(subset=subset)

        return self.root.new(dfd)

    def limit(self, count) -> DataFrame:
        """
        Limit the number of rows
        :param count:
        :return:
        """
        dfd = self.root.data
        return self.root.new(dfd[:count - 1])


    @staticmethod
    def unnest(input_cols) -> DataFrame:
        df = self
        return df
