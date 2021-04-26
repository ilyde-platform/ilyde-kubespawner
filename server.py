#
# Copyright (c) 2020-2021 Hopenly srl.
#
# This file is part of Ilyde.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import logging
from concurrent import futures

import yaml
import grpc
from grpc_health.v1 import health, health_pb2_grpc

from protos import kubespawner_pb2, kubespawner_pb2_grpc
from kubernetes import client, config
from interceptors import ExceptionToStatusInterceptor
from serializers import protobuf_to_dict, ResourceType, FileSerializer, ServiceSerializer,\
    ResourceSerializer
from google.protobuf.struct_pb2 import Struct
from config import CLUSTER_ENVIRONMENT


# setup logger
FORMAT = '%(asctime)s %(levelname)s %(message)s'
logging.basicConfig(level=logging.NOTSET, format=FORMAT)
logger = logging.getLogger(__name__)


class KubeSpawnerServicer(kubespawner_pb2_grpc.KubeSpawnerServicesServicer):
    """The KubeSpawner service definition.
    This service creates, deletes and handles kubernetes resources
    """

    def __init__(self):
        # load kubernetes config
        if CLUSTER_ENVIRONMENT == "internal":
            config.load_incluster_config()
        else:
            config.load_kube_config()

        super(KubeSpawnerServicer).__init__()

    def CreateDeploymentFromFile(self, request, context):
        """creates deployment from file definitions yaml
        """
        # parameters from the request
        data = FileSerializer().load(protobuf_to_dict(request))
        file = data['content']
        namespace = data['namespace']

        deployment = yaml.safe_load(file)
        api_client = client.AppsV1Api()

        api_client.create_namespaced_deployment(
            body=deployment,
            namespace=namespace
        )

        return kubespawner_pb2.Status(
            status=200,
            message="Deployment successfully created"
        )

    def CreateIngressFromFile(self, request, context):
        """
            Creates an ingress from file definition yaml
            using Traefik as ingress Controller
        """
        # parameters from the request
        data = FileSerializer().load(protobuf_to_dict(request))
        file = data['content']
        namespace = data['namespace']

        ingress = yaml.safe_load(file)
        api_client = client.CustomObjectsApi()
        # create the resource
        api_client.create_namespaced_custom_object(
            group="traefik.containo.us",
            version="v1alpha1",
            namespace=namespace,
            plural="ingressroutes",
            body=ingress,
        )

        return kubespawner_pb2.Status(
            status=200,
            message="Ingress successfully created"
        )

    def CreateServiceFromFile(self, request, context):
        """
            Creates a service from file definition yaml
        """
        # parameters from the request
        data = FileSerializer().load(protobuf_to_dict(request))
        file = data['content']
        namespace = data['namespace']

        service = yaml.safe_load(file)
        api_client = client.CoreV1Api()
        # create the resource
        api_client.create_namespaced_service(
            namespace=namespace,
            body=service,
        )
        return kubespawner_pb2.Status(
            status=200,
            message="Service successfully created"
        )

    def CreateService(self, request, context):
        """Creates a service
        """
        # parameters from the request
        data = ServiceSerializer().load(protobuf_to_dict(request))
        namespace = data['namespace']
        name = data['name']
        selector = data['selector']
        port = data['port']
        target = data['target']

        api_client = client.CoreV1Api()
        body = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(
                name=name
            ),
            spec=client.V1ServiceSpec(
                selector=yaml.safe_load(selector),
                ports=[client.V1ServicePort(
                    port=int(port),
                    target_port=int(target)
                )]
            )
        )

        response = api_client.create_namespaced_service(
            namespace=namespace,
            body=body
        )

        return kubespawner_pb2.Status(
            status=200,
            message="Service successfully created"
        )

    def DeleteDeployment(self, request, context):
        """Deletes a Deployment resource
        """
        # parameters from the request
        data = ResourceSerializer().load(protobuf_to_dict(request))
        namespace = data['namespace']
        name = data['name']
        type = data['type']

        if type is not ResourceType.DEPLOYMENT:
            return kubespawner_pb2.Status(
                status=400,
                message="It is not a deployment resource"
            )

        api_instance = client.AppsV1Api()
        response = api_instance.delete_namespaced_deployment(
            name=name,
            namespace=namespace,
            body=client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=5)
        )

        return kubespawner_pb2.Status(
            status=200,
            message="Deployment successfully deleted"
        )

    def DeleteService(self, request, context):
        """Deletes a Service resource
        """
        # parameters from the request
        data = ResourceSerializer().load(protobuf_to_dict(request))
        namespace = data['namespace']
        name = data['name']
        type = data['type']

        if type is not ResourceType.SERVICE:
            return kubespawner_pb2.Status(
                status=400,
                message="It is not a service resource"
            )

        api_instance = client.CoreV1Api()
        api_instance.delete_namespaced_service(
            name=name,
            namespace=namespace,
            body=client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=5))

        return kubespawner_pb2.Status(
            status=200,
            message="Service successfully deleted"
        )

    def DeleteIngress(self, request, context):
        """Deletes an Ingress Custom traefik resource
        """
        # parameters from the request
        data = ResourceSerializer().load(protobuf_to_dict(request))
        namespace = data['namespace']
        name = data['name']
        type = data['type']

        if type is not ResourceType.INGRESS:
            return kubespawner_pb2.Status(
                status=400,
                message="It is not an ingress resource"
            )

        api_instance = client.CustomObjectsApi()
        api_instance.delete_namespaced_custom_object(
            name=name,
            group="traefik.containo.us",
            version="v1alpha1",
            namespace=namespace,
            plural="ingressroutes",
            body=client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=5))

        return kubespawner_pb2.Status(
            status=200,
            message="Ingress successfully deleted"
        )

    def GetResourceStatus(self, request, context):
        """Get resource's status
        """
        # parameters from the request
        data = ResourceSerializer().load(protobuf_to_dict(request))
        namespace = data['namespace']
        name = data['name']
        resource_type = data['type']

        if resource_type is ResourceType.DEPLOYMENT:
            api_instance = client.AppsV1Api()
            response = api_instance.read_namespaced_deployment_status(
                name=name,
                namespace=namespace
            )
            response = response.status
            payload = {
                "available_replicas": response.available_replicas,
                "collision_count": response.collision_count,
                "replicas": response.replicas,
                "unavailable_replicas": response.unavailable_replicas,
                "updated_replicas": response.updated_replicas
            }

        elif resource_type is ResourceType.JOB:
            api_instance = client.BatchV1Api()
            response = api_instance.read_namespaced_job_status(
                name=name,
                namespace=namespace
            )
            response = response.status
            start_time = response.start_time.strftime("%Y-%m-%dT%H:%M:%S") if response.start_time else ""
            completion_time = response.completion_time.strftime("%Y-%m-%dT%H:%M:%S") if response.completion_time else ""
            # extract completion time
            for condition in response.conditions:
                if condition.type == "Failed":
                    completion_time = condition.last_transition_time.strftime("%Y-%m-%dT%H:%M:%S")

            payload = {
                "active": response.active,
                "completion_time": completion_time,
                "failed": response.failed,
                "start_time": start_time,
                "succeeded": response.succeeded
            }

        elif resource_type is ResourceType.CRONJOB:
            api_instance = client.BatchV1beta1Api()
            response = api_instance.read_namespaced_cron_job(
                name=name,
                namespace=namespace
            )
            last_schedule_time = response.last_schedule_time.strftime("%Y-%m-%dT%H:%M:%S")\
                if response.last_schedule_time else ""

            response = response.status
            active = response.active if response.active else []
            payload = {
                "active": len(active),
                "last_schedule_time": last_schedule_time,
            }
        else:
            payload = {"Error": "Invalid resource requested"}

        s = Struct()
        s.update(payload)

        return s

    def CreateJobFromFile(self, request, context):
        """create job from file definitions yaml
        """
        # parameters from the request
        data = FileSerializer().load(protobuf_to_dict(request))
        file = data['content']
        namespace = data['namespace']

        job = yaml.safe_load(file)
        api_instance = client.BatchV1Api()
        response = api_instance.create_namespaced_job(
            body=job,
            namespace=namespace
        )

        return kubespawner_pb2.Status(
            status=200,
            message="Job successfully created"
        )

    def CreateCronJobFromFile(self, request, context):
        """create cronjob from file definitions yaml
        """
        # parameters from the request
        data = FileSerializer().load(protobuf_to_dict(request))
        file = data['content']
        namespace = data['namespace']

        job = yaml.safe_load(file)
        api_instance = client.BatchV1beta1Api()
        api_instance.create_namespaced_cron_job(
            body=job,
            namespace=namespace
        )

        return kubespawner_pb2.Status(
            status=200,
            message="Job successfully created"
        )

    def CreatePVCFromFile(self, request, context):
        """create persistence volume claim from file definitions yaml
        """
        # parameters from the request
        data = FileSerializer().load(protobuf_to_dict(request))
        file = data['content']
        namespace = data['namespace']

        pvc = yaml.safe_load(file)
        api_instance = client.CoreV1Api()
        api_instance.create_namespaced_persistent_volume_claim(
            body=pvc,
            namespace=namespace
        )

        return kubespawner_pb2.Status(
            status=200,
            message="Pvc successfully created"
        )

    def DeleteJob(self, request, context):
        """Delete Job resource
        """
        # parameters from the request
        data = ResourceSerializer().load(protobuf_to_dict(request))
        namespace = data['namespace']
        name = data['name']
        type = data['type']

        if type is not ResourceType.JOB:
            return kubespawner_pb2.Status(
                status=400,
                message="It is not a job resource"
            )

        api_instance = client.BatchV1Api()
        response = api_instance.delete_namespaced_job(
            name=name,
            namespace=namespace,
            body=client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=5))

        return kubespawner_pb2.Status(
            status=200,
            message="Job successfully deleted"
        )

    def DeleteCronJob(self, request, context):
        """Delete cronJob resource
        """
        # parameters from the request
        data = ResourceSerializer().load(protobuf_to_dict(request))
        namespace = data['namespace']
        name = data['name']
        type = data['type']

        if type is not ResourceType.CRONJOB:
            return kubespawner_pb2.Status(
                status=400,
                message="It is not a cronjob resource"
            )

        api_instance = client.BatchV1beta1Api()
        api_instance.delete_namespaced_cron_job(
            name=name,
            namespace=namespace,
            body=client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=5))

        return kubespawner_pb2.Status(
            status=200,
            message="Job successfully deleted"
        )

    def DeletePVC(self, request, context):
        """Delete PVC resource
        """
        # parameters from the request
        data = ResourceSerializer().load(protobuf_to_dict(request))
        namespace = data['namespace']
        name = data['name']
        type = data['type']

        if type is not ResourceType.PVC:
            return kubespawner_pb2.Status(
                status=400,
                message="It is not a pvc resource"
            )

        api_instance = client.CoreV1Api()
        response = api_instance.delete_namespaced_persistent_volume_claim(
            name=name,
            namespace=namespace,
            body=client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=5))

        return kubespawner_pb2.Status(
            status=200,
            message="Pvc successfully deleted"
        )


def create_server(server_address):
    server = grpc.server(futures.ThreadPoolExecutor())
    kubespawner_pb2_grpc.add_KubeSpawnerServicesServicer_to_server(KubeSpawnerServicer(), server)

    health_servicer = health.HealthServicer(
        experimental_non_blocking=True,
        experimental_thread_pool=futures.ThreadPoolExecutor(max_workers=1))
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)

    port = server.add_insecure_port(server_address)
    return server, port


def serve():
    server, port = create_server("[::]:50051")
    server.start()
    logger.info("Server is running on port {} .....................".format(port))
    server.wait_for_termination()
    logger.info("Server is stopped .....................")


if __name__ == '__main__':
    logger.info("Server is starting .....................")
    serve()
