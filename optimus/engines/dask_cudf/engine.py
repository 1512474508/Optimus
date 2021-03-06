import dask
from dask.distributed import Client, get_client

from optimus.engines.dask_cudf.create import Create
from optimus.engines.base.engine import BaseEngine
from optimus.engines.base.remote import ClientActor, RemoteDummyVariable, RemoteDummyDataFrame
from optimus.engines.dask_cudf.io.load import Load
from optimus.helpers.logger import logger
from optimus.optimus import Engine
from optimus.profiler.profiler import Profiler

# import dask_cudf
Profiler.instance = None

BIG_NUMBER = 100000


class DaskCUDFEngine(BaseEngine):
    def __init__(self, session=None, address=None, n_workers=1, threads_per_worker=None, processes=False,
                 memory_limit='4GB', verbose=False, coiled_token=None, *args, **kwargs):

        """

        :param session:
        :param n_workers:
        :param threads_per_worker:
        :param memory_limit:
        :param verbose:
        :param comm:
        :param args:
        :param kwargs:
        """

        self.engine = Engine.DASK_CUDF.value

        self.verbose(verbose)

        use_remote = kwargs.get("use_remote", coiled_token is not None)

        if coiled_token:
            import coiled
            dask.config.set({"coiled.token": coiled_token})
            try:
                coiled.Cloud()
            except Exception as error:
                raise error

            idle_timeout = kwargs.get("idle_timeout", None)

            cluster = coiled.Cluster(
                name=kwargs.get("name"),
                worker_options={
                    **({"nthreads": threads_per_worker} if threads_per_worker else {}),
                    **({"memory_limit": memory_limit} if memory_limit else {})
                },
                worker_gpu=1,
                worker_class='dask_cuda.CUDAWorker',
                n_workers=n_workers,
                worker_memory='15GiB',
                backend_options={
                    "region": kwargs.get("backend_region", "us-east-1")
                },
                scheduler_options={
                    **({"idle_timeout": idle_timeout} if idle_timeout else {})
                },
                software="optimus/gpu"
            )

            self.cluster_name = cluster.name
            self.client = Client(cluster)

        elif address:
            self.client = Client(address=address)

        elif session and session != "local":
            self.client = session

        else:
            try:
                self.client = get_client()
            except ValueError:
                from dask_cuda import LocalCUDACluster
                from GPUtil import GPUtil
                n_gpus = len(GPUtil.getAvailable(order='first', limit=BIG_NUMBER))

                if n_workers > n_gpus:
                    logger.print(
                        f"n_workers should be equal or less than the number of GPUs. n_workers is now {n_gpus}")
                    n_workers = n_gpus
                    # n_gpus = 1
                cluster = LocalCUDACluster(n_workers=n_workers, threads_per_worker=threads_per_worker, processes=True,
                                           memory_limit=memory_limit)
                self.client = Client(cluster, *args, **kwargs)
            use_remote = False

        if use_remote:
            self.remote = self.client.submit(ClientActor, Engine.DASK_CUDF.value, actor=True).result(10)

        else:
            self.remote = False

        Profiler.instance = Profiler()
        self.profiler = Profiler.instance

    @property
    def create(self):
        if self.remote:
            return RemoteDummyVariable(self, "_create")

        else:
            return Create(self)

    @property
    def load(self):
        if self.remote:
            return RemoteDummyVariable(self, "_load")

        else:
            return Load(self)
            
    def dataframe(self, cdf, n_partitions=1, *args, **kwargs):
        import dask_cudf
        from optimus.engines.dask_cudf.dataframe import DaskCUDFDataFrame
        return DaskCUDFDataFrame(dask_cudf.from_cudf(cdf, npartitions=n_partitions, *args, **kwargs))

    def remote_run(self, callback, *args, **kwargs):
        if not self.remote:
            raise

        if kwargs.get("client_timeout"):
            client_timeout = kwargs.get("client_timeout")
            del kwargs["client_timeout"]

        else:
            client_timeout = 600

        result = self.remote.submit(callback, *args, **kwargs).result(client_timeout)
        if isinstance(result, dict):
            if result.get("status") == "error" and result.get("error"):
                raise Exception(result.get("error"))
            elif result.get("dummy"):
                if result.get("dataframe"):
                    return RemoteDummyDataFrame(self, result.get("dummy"))
                else:
                    return RemoteDummyVariable(self, result.get("dummy"))
        return result

    def remote_submit(self, callback, *args, **kwargs):
        if not self.remote:
            raise

        return self.remote.submit(callback, *args, **kwargs)
