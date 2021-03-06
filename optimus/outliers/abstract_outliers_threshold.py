from abc import ABC, abstractmethod

from optimus.helpers.columns import parse_columns, name_col
from optimus.helpers.core import one_list_to_val


class AbstractOutlierThreshold(ABC):
    """
     This is a template class to expand the outliers methods
     Also you need to add the function to outliers.py
     """

    def __init__(self, df, col_name: str, prefix: str):
        """

        :param df: Spark Dataframe
        :param col_name: column name
        """

        self.df = df
        self.col_name = one_list_to_val(parse_columns(df, col_name))
        self.tmp_col = name_col(self.col_name, prefix)

    def select(self):
        """
        Select outliers rows using the selected column
        :return:
        """

        df = self.df

        return df.rows.select(df[self.tmp_col] > self.threshold).cols.drop(self.tmp_col)

    def drop(self):
        """
        Drop outliers rows using the selected column
        :return:
        """

        df = self.df
        return df.rows.drop(df[self.tmp_col] >= self.threshold).cols.drop(self.tmp_col)

    def count_lower_bound(self, bound: int):
        """
        Count outlier in the lower bound
        :return:
        """
        col_name = self.col_name
        return self.df.rows.select(self.df[col_name] < bound).count()

    def count_upper_bound(self, bound: int):
        """
        Count outliers in the upper bound
        :return:
        """
        col_name = self.col_name
        return self.df.rows.select(self.df[col_name] >= bound).count()

    def count(self):
        """
        Count the outliers rows using the selected column
        :return:
        """
        return self.select().rows.count(compute=False)

    def non_outliers_count(self):
        """
        Count non outliers rows using the selected column
        :return:
        """
        df = self.df
        return df.rows.select(df[self.tmp_col] < self.threshold).cols.drop(self.tmp_col).rows.count(compute=False)

    @abstractmethod
    def info(self, output: str = "dict"):
        """
        Get whiskers, iqrs and outliers and non outliers count
        :return:
        """
        pass
