import re

import pandas as pd
from ibis.expr.types import TableExpr
from sklearn import preprocessing

from optimus.engines.base.commons.functions import impute, string_to_index, index_to_string
from optimus.engines.base.dataframe.columns import DataFrameBaseColumns
from optimus.helpers.columns import parse_columns, prepare_columns
from optimus.helpers.constants import Actions
from optimus.helpers.converter import format_dict
from optimus.helpers.core import val_to_list
from optimus.infer import is_str, is_tuple, is_dict

DataFrame = TableExpr


class Cols(DataFrameBaseColumns):
    def __init__(self, df):
        super(DataFrameBaseColumns, self).__init__(df)

    def _names(self):
        return list(self.root.data.columns)

    def append(self, dfs):
        """

        :param dfs:
        :return:
        """

        dfd = self.root.data
        dfd = pd.concat([dfs.data.reset_index(drop=True), dfd.reset_index(drop=True)], axis=1)
        return self.root.new(dfd)

    def dtypes(self, columns="*"):
        df = self.root
        columns = parse_columns(df, columns)
        return dict(df.data[columns].schema().items())

    def agg_exprs(self, columns, funcs, *args, compute=True, tidy=True):
        df = self.root
        columns = parse_columns(df, columns)

        funcs = val_to_list(funcs)
        all_funcs = []

        for col_name in columns:
            for func in funcs:
                all_funcs.append({func.__name__: {col_name: self.exec_agg(func(df.data[col_name], *args))}})

        result = {}
        for i in all_funcs:
            for x, y in i.items():
                result.setdefault(x, {}).update(y)

        return format_dict(result, tidy)

    @staticmethod
    def exec_agg(exprs, compute=None):
        """
        Execute an aggregation
        :param exprs: Aggreagtion function to process
        :return:
        """
        if is_dict(exprs):
            result = exprs
        else:
            result = exprs.execute()
        return result

    @staticmethod
    def to_timestamp(input_cols, date_format=None, output_cols=None):
        pass

    def impute(self, input_cols, data_type="continuous", strategy="mean", output_cols=None):
        df = self.root
        return impute(df, input_cols, data_type="continuous", strategy="mean", output_cols=None)

    @staticmethod
    def astype(*args, **kwargs):
        pass

    def apply(self, input_cols, func=None, func_return_type=None, args=None, func_type=None, when=None,
              filter_col_by_dtypes=None, output_cols=None, skip_output_cols_processing=False,
              meta_action=Actions.APPLY_COLS.value, mode="pandas", set_index=False, default=None, **kwargs):
        columns = prepare_columns(self.root, input_cols, output_cols, filter_by_column_dtypes=filter_col_by_dtypes,
                                  accepts_missing_cols=True, default=default)
        kw_columns = {}
        if args is None:
            args = (None,)
        elif not is_tuple(args, ):
            args = (args,)

        for input_col, output_col in columns:
            # print("args",args)
            kw_columns.update({output_col: func(self.root.data[input_col], *args)})
        return self.root.new(self.root.data.mutate(**kw_columns))

    @staticmethod
    def find(columns, sub, ignore_case=False):
        """
        Find the start and end position for a char or substring
        :param columns:
        :param ignore_case:
        :param sub:
        :return:
        """
        df = self
        columns = parse_columns(df, columns)
        sub = val_to_list(sub)

        def get_match_positions(_value, _separator):

            result = None
            if is_str(_value):
                # Using re.IGNORECASE in finditer not seems to work
                if ignore_case is True:
                    _separator = _separator + [s.lower() for s in _separator]
                regex = re.compile('|'.join(_separator))

                length = [[match.start(), match.end()] for match in
                          regex.finditer(_value)]
                result = length if len(length) > 0 else None
            return result

        for col_name in columns:
            # Categorical columns can not handle a list inside a list as return for example [[1,2],[6,7]].
            # That could happened if we try to split a categorical column
            # df[col_name] = df[col_name].astype("object")
            df[col_name + "__match_positions__"] = df[col_name].astype("object").apply(get_match_positions,
                                                                                       args=(sub,))
        return df

    @staticmethod
    def scatter(columns, buckets=10):
        pass

    def count_by_dtypes(self, columns, dtype):

        df = self.root
        result = {}
        df_len = len(df)
        for col_name, na_count in df.cols.count_na(columns, tidy=False)["count_na"].items():
            # for i, j in df.constants.DTYPES_DICT.items():
            #     if j == df[col_name].dtype.type:
            #         _dtype = df.constants.SHORT_DTYPES[i]

            # _dtype = df.cols.dtypes(col_name)[col_name]

            mismatches_count = df.cols.is_match(col_name, dtype).value_counts().to_dict().get(False)
            mismatches_count = 0 if mismatches_count is None else mismatches_count
            result[col_name] = {"match": df_len - na_count, "missing": na_count,
                                "mismatch": mismatches_count - na_count}
        return result

    @staticmethod
    def correlation(input_cols, method="pearson", output="json"):
        pass

    @staticmethod
    def qcut(columns, num_buckets, handle_invalid="skip"):
        pass

    def string_to_index(self, input_cols=None, output_cols=None, columns=None):
        df = self.df
        le = preprocessing.LabelEncoder()
        df = string_to_index(df, input_cols, output_cols, le)

        return df

    def index_to_string(self, input_cols=None, output_cols=None, columns=None):
        df = self.df
        le = preprocessing.LabelEncoder()
        df = index_to_string(df, input_cols, output_cols, le)

        return df
