import os
import tempfile

import prometheus_client
import prometheus_client.multiprocess
import prometheus_client.values


class MultiProcessRegistry(prometheus_client.CollectorRegistry):

    tmpdir = tempfile.gettempdir()

    def __init__(self):
        super().__init__()
        os.environ['PROMETHEUS_MULTIPROC_DIR'] = self.tmpdir
        prometheus_client.values.ValueClass = (
            prometheus_client.values.get_value_class())
        prometheus_client.multiprocess.MultiProcessCollector(self)

    @classmethod
    def gunicorn_child_exit(cls, server, worker):
        prometheus_client.multiprocess.mark_process_dead(worker.pid, cls.tmpdir)
