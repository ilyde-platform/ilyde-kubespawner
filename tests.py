# encoding: utf-8
import json
import unittest
import logging

import grpc
import yaml

from protos import kubespawner_pb2_grpc, kubespawner_pb2

import server

# setup logger
FORMAT = '%(asctime)s %(levelname)s %(message)s'
logging.basicConfig(level=logging.NOTSET, format=FORMAT)
logger = logging.getLogger(__name__)


class KubespawnerServicerTest(unittest.TestCase):

    def setUp(self):
        self._server, port = server.create_server('[::]:0')
        self._server.start()
        self._channel = grpc.insecure_channel('localhost:%d' % port)

    def tearDown(self):
        self._channel.close()
        self._server.stop(None)

    def test_create_deployment(self):
        logger.info("test create deployment from file")
        stub = kubespawner_pb2_grpc.KubeSpawnerServicesStub(self._channel)
        with open("examples/deployment.json") as f:
            data = json.load(f)
            response = stub.CreateDeploymentFromFile(kubespawner_pb2.File(namespace="default",
                                                                          content=json.dumps(data)))
            self.assertEqual(response.status, 200)

    def test_create_pvc(self):
        logger.info("test create pvc from file")
        stub = kubespawner_pb2_grpc.KubeSpawnerServicesStub(self._channel)
        with open("examples/pvc.yml") as f:
            data = yaml.safe_load(f)
            response = stub.CreatePVCFromFile(
                kubespawner_pb2.File(namespace="default", content=yaml.dump(data)))
            self.assertEqual(response.status, 200)


if __name__ == '__main__':
    logger.info("tests KubeSpawnerServicer")
    unittest.main(verbosity=2)
