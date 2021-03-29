# encoding: utf-8

import grpc
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Struct

from protos import kubespawner_pb2
from protos import kubespawner_pb2_grpc


def run():
    channel = grpc.insecure_channel('localhost:50051')
    stub = kubespawner_pb2_grpc.KubeSpawnerServicesStub(channel)

    try:

        response = stub.CreateDeploymentFromFile(kubespawner_pb2.File(namespace="common", content="{'apiVersion': 'apps/v1', 'kind': 'Deployment', 'metadata': {'name': 'nginx-deployment', 'labels': {'app': 'nginx'}}, 'spec': {'replicas': 2, 'selector': {'matchLabels': {'app': 'nginx'}}, 'template': {'metadata': {'labels': {'app': 'nginx'}}, 'spec': {'containers': [{'name': 'nginx', 'image': 'nginx:1.15.4', 'ports': [{'containerPort': 80}]}]}}}}"))
    except grpc.RpcError as e:
        # ouch!
        # lets print the gRPC error message
        # which is "Length of `Name` cannot be more than 10 characters"
        print(e.details(), e)
        # lets access the error code, which is `INVALID_ARGUMENT`
        # `type` of `status_code` is `grpc.StatusCode`
        status_code = e.code()
        # should print `INVALID_ARGUMENT`
        print(status_code.name)
        # should print `(3, 'invalid argument')`
        print(status_code.value)
        # want to do some specific action based on the error?
        if grpc.StatusCode.INVALID_ARGUMENT == status_code:
            # do your stuff here
            pass
    else:
        print(json_format.MessageToJson(response, preserving_proto_field_name=True,
                                        including_default_value_fields=True,
                                        ))


if __name__ == '__main__':
    run()