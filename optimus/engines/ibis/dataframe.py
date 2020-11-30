from optimus.engines.base.odataframe import BaseDataFrame


class IbisDataFrame(BaseDataFrame):

    def __init__(self, data):
        super().__init__(self, data)

    @property
    def rows(self):
        from optimus.engines.ibis.rows import Rows
        return Rows(self)

    @property
    def cols(self):
        from optimus.engines.ibis.columns import Cols
        return Cols(self)

    @property
    def functions(self):
        from optimus.engines.ibis.functions import IbisFunctions
        return IbisFunctions(self)

    @staticmethod
    def delayed(func):
        pass

    @staticmethod
    def cache():
        pass

    @staticmethod
    def compute():
        pass

    @staticmethod
    def sample(n=10, random=False):
        pass

    @staticmethod
    def pivot(index, column, values):
        pass

    @staticmethod
    def melt(id_vars, value_vars, var_name="variable", value_name="value", data_type="str"):
        pass

    @staticmethod
    def query(sql_expression):
        pass

    @staticmethod
    def partitions():
        pass

    @staticmethod
    def partitioner():
        pass

    @staticmethod
    def show():
        pass

    @staticmethod
    def debug():
        pass

    def compile(self):
        # return str(ibis.impala.compiler(self.parent.data))
        return str(self.root.data.compile())

    def to_pandas(self):
        return self.root.data.execute()
