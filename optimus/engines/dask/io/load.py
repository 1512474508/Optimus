import csv
import ntpath
import os

import dask.bag as db
import magic
import pandas as pd
from dask import dataframe as dd

import optimus.helpers.functions_spark
from optimus.helpers.core import val_to_list
from optimus.helpers.functions import prepare_path
from optimus.helpers.logger import logger
from optimus.helpers.raiseit import RaiseIt

XML_THRESHOLD = 10
JSON_THRESHOLD = 20
BYTES_SIZE = 4096


class Load:

    @staticmethod
    def json(path, multiline=False, *args, **kwargs):
        """
        Return a dask dataframe from a json file.
        :param path: path or location of the file.
        :param multiline:

        :return:
        """
        file, file_name = prepare_path(path, "json")

        try:
            # TODO: Check a better way to handle this Spark.instance.spark. Very verbose.
            df = dd.read_json(path, lines=multiline, *args, **kwargs)
            df.ext.reset()
            df.meta.set("file_name", file_name)

        except IOError as error:
            logger.print(error)
            raise
        return df

    @staticmethod
    def tsv(path, header=True, infer_schema=True, *args, **kwargs):
        """
        Return a dataframe from a tsv file.
        :param path: path or location of the file.
        :param header: tell the function whether dataset has a header row. True default.
        :param infer_schema: infers the input schema automatically from data.
        It requires one extra pass over the data. True default.

        :return:
        """

        return Load.csv(path, sep='\t', header=header, infer_schema=infer_schema, *args, **kwargs)

    @staticmethod
    def csv(path, sep=',', header=True, infer_schema=True, encoding="utf-8", null_value="None", n_rows=-1, cache=False,
            quoting=0, lineterminator=None, error_bad_lines=False, keep_default_na=False, *args, **kwargs):

        """
        Return a dataframe from a csv file. It is the same read.csv Spark function with some predefined
        params

        :param path: path or location of the file.
        :param sep: usually delimiter mark are ',' or ';'.
        :param header: tell the function whether dataset has a header row. True default.
        :param infer_schema: infers the input schema automatically from data.
        :param encoding:
        :param null_value:
        :param n_rows:
        :param quoting:
        :param lineterminator:
        :param error_bad_lines:
        :param keep_default_na:
        :param cache: If calling from a url we cache save the path to the temp file so we do not need to download the file again

        """
        if cache is False:
            prepare_path.cache_clear()

        file, file_name = prepare_path(path, "csv")
        try:
            df = dd.read_csv(file, sep=sep, header=0 if header else None, encoding=encoding,
                             quoting=quoting, lineterminator=lineterminator, error_bad_lines=error_bad_lines,
                             keep_default_na=True, na_values=None, engine="c", *args,
                             **kwargs)
            # print(len(df))
            if n_rows > -1:
                df = dd.from_pandas(df.head(n_rows), npartitions=1)
            df.ext.reset()
            df.meta.set("file_name", file_name)
        except IOError as error:
            logger.print(error)
            raise

        return df

    @staticmethod
    def parquet(path, columns=None, engine="pyarrow", *args, **kwargs):
        """
        Return a dataframe from a parquet file.
        :param path: path or location of the file. Must be string dataType
        :param columns: select the columns that will be loaded. In this way you do not need to load all the dataframe
        :param engine:
        :param args: custom argument to be passed to the spark parquet function
        :param kwargs: custom keyword arguments to be passed to the spark parquet function
        :return: Spark Dataframe
        """

        file, file_name = prepare_path(path, "parquet")

        try:
            df = dd.read_parquet(path, columns=columns, engine=engine, *args, **kwargs)
            df.ext.reset()
            df.meta.set("file_name", file_name)

        except IOError as error:
            logger.print(error)
            raise

        return df

    @staticmethod
    def zip(path, sep=',', header=True, infer_schema=True, charset="UTF-8", null_value="None", n_rows=-1, *args,
            **kwargs):
        file, file_name = prepare_path(path, "zip")

        from zipfile import ZipFile
        import dask.dataframe as dd
        import os

        wd = '/path/to/zip/files'
        file_list = os.listdir(wd)
        destdir = '/extracted/destination/'

        ddf = dd.from_pandas(pd.DataFrame())

        for f in file_list:
            with ZipFile(wd + f, "r") as zip:
                zip.extractall(destdir, None, None)
                df = dd.read_csv(zip.namelist(), usecols=['Enter', 'Columns', 'Here'], parse_dates=['Date'])
                ddf = optimus.helpers.functions_spark.append(df)

        ddf.compute()

        # print("---",path, file, file_name)
        try:
            df = dd.read_csv(file, sep=sep, header=0 if header else None, encoding=charset, na_values=null_value,
                             compression="gzip", *args,
                             **kwargs)

            if n_rows > -1:
                df = df.head(n_rows)

            df.meta.set("file_name", file_name)
        except IOError as error:
            logger.print(error)
            raise
        df.ext.reset()
        return df

    @staticmethod
    def avro(path, *args, **kwargs):
        """
        Return a dataframe from a avro file.
        :param path: path or location of the file. Must be string dataType
        :param args: custom argument to be passed to the avro function
        :param kwargs: custom keyword arguments to be passed to the avro function
        :return: Spark Dataframe
        """
        file, file_name = prepare_path(path, "avro")

        try:
            df = db.read_avro(path, *args, **kwargs).to_dataframe()
            df.ext.reset()
            df.meta.set("file_name", file_name)

        except IOError as error:
            logger.print(error)
            raise

        return df

    @staticmethod
    def excel(path, sheet_name=0, merge_sheets=False, skiprows=1, n_rows=-1, n_partitions=1, *args, **kwargs):
        """
        Return a dataframe from a excel file.
        :param path: Path or location of the file. Must be string dataType
        :param sheet_name: excel sheet name
        :param merge_sheets:
        :param args: custom argument to be passed to the excel function
        :param kwargs: custom keyword arguments to be passed to the excel function

        """
        file, file_name = prepare_path(path)
        header = None
        if merge_sheets is True:
            skiprows = -1
        else:
            header = 0
            skiprows = 0

        if n_rows == -1:
            n_rows = None
        #     pdfs = val_to_list(
        #         pd.read_excel(file, sheet_name=sheet_name, header=header, skiprows=None, *args,
        #                       **kwargs))
        # else:
        pdfs = pd.read_excel(file, sheet_name=sheet_name, header=header, skiprows=skiprows, nrows=n_rows, *args,
                             **kwargs)
        sheet_names = list(pd.read_excel(file, None).keys())

        pdf = pd.concat(val_to_list(pdfs), axis=0).reset_index(drop=True)

        df = dd.from_pandas(pdf, npartitions=n_partitions)
        df.ext.reset()
        df.meta.set("file_name", ntpath.basename(file_name))
        df.meta.set("sheet_names", sheet_names)

        return df

    @staticmethod
    def file(path, *args, **kwargs):

        full_path, file_name = prepare_path(path)

        file_ext = os.path.splitext(file_name)[1].replace(".", "")

        mime, encoding = magic.Magic(mime=True, mime_encoding=True).from_file(full_path).split(";")
        mime_info = {"mime": mime, "encoding": encoding.strip().split("=")[1], "file_ext": file_ext}

        if mime == "text/plain":

            # In some case magic get a "unknown-8bit" which can not be use to decode the file use latin-1 instead
            if mime_info["encoding"] == "unknown-8bit":
                mime_info["encoding"] = "latin-1"

            file = open(full_path, encoding=mime_info["encoding"]).read(BYTES_SIZE)

            # JSON
            # Try to infer if is a valid json
            if sum([file.count(i) for i in ['{', '}', '[', ']']]) > JSON_THRESHOLD:
                # print("sdf",file)
                mime_info["file_type"] = "json"
                df = Load.json(full_path, *args, **kwargs)

            # XML
            elif sum([file.count(i) for i in ['<', '/>']]) > XML_THRESHOLD:
                mime_info["file_type"] = "xml"

            # CSV
            else:
                try:
                    dialect = csv.Sniffer().sniff(file)
                    mime_info["file_type"] = "csv"

                    r = {"properties": {"delimiter": dialect.delimiter,
                                        "doublequote": dialect.doublequote,
                                        "escapechar": dialect.escapechar,
                                        "lineterminator": dialect.lineterminator,
                                        "quotechar": dialect.quotechar,
                                        "quoting": dialect.quoting,
                                        "skipinitialspace": dialect.skipinitialspace}}

                    mime_info.update(r)
                    df = Load.csv(full_path, encoding=mime_info["encoding"], dtype=object, **mime_info["properties"],
                                  **kwargs)
                except Exception as err:
                    print(err)
                    pass

        elif mime_info["file_ext"] == "xls" or mime_info["file_ext"] == "xlsx":
            mime_info["file_type"] = "excel"
            df = Load.excel(full_path, **kwargs)

        else:
            RaiseIt.value_error(mime_info["file_ext"], ["csv", "json", "xml", "xls", "xlsx"])

        df.meta.update("mime_info", value=mime_info)
        return df
