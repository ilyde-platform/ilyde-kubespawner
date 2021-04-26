# encoding: utf-8
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
from typing import Callable, Any
from google.protobuf import any_pb2
from grpc_interceptor import ServerInterceptor
from grpc_interceptor.exceptions import GrpcException, InvalidArgument, Unknown
import grpc
import marshmallow
from kubernetes.client.rest import ApiException, ApiValueError

from protos import kubespawner_pb2

# setup logger
FORMAT = '%(asctime)s %(levelname)s %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)


def parse_api_exception(error: ApiException):
    message = error.reason
    if error.body:
        message += ":{}".format_map(error.body.message)


class ExceptionToStatusInterceptor(ServerInterceptor):
    def intercept(
        self,
        method: Callable,
        request: Any,
        context: grpc.ServicerContext,
        method_name: str,
    ) -> Any:
        """Override this method to implement a custom interceptor.
         You should call method(request, context) to invoke the
         next handler (either the RPC method implementation, or the
         next interceptor in the list).
         Args:
             method: The next interceptor, or method implementation.
             request: The RPC request, as a protobuf message.
             context: The ServicerContext pass by gRPC to the service.
             method_name: A string of the form
                 "/protobuf.package.Service/Method"
         Returns:
             This should generally return the result of
             method(request, context), which is typically the RPC
             method response, as a protobuf message. The interceptor
             is free to modify this in some way, however.
         """
        try:
            return method(request, context)
        except GrpcException as e:
            context.set_code(e.status_code)
            context.set_details(e.details)
            logger.error(e.details)
            return any_pb2.Any()

        except marshmallow.ValidationError as e:
            context.set_code(InvalidArgument.status_code)
            msg = ' '.join(["%s: %s" % (key, str(value)) for key, value in e.messages.items()])
            context.set_details(msg)
            logger.error(msg)
            return any_pb2.Any()

        except ApiException as e:
            context.set_code("KubeError")
            context.set_details(parse_api_exception(e))
            logger.error(parse_api_exception(e))
            return kubespawner_pb2.Status(
                status=e.status,
                message=parse_api_exception(e)
            )

        except ApiValueError as e:
            context.set_code("KubeError")
            context.set_details(e)
            logger.error(e)
            return kubespawner_pb2.Status(
                status=400,
                message=e
            )
        except Exception as e:
            context.set_code(Unknown.status_code)
            context.set_details(str(e))
            logger.error(str(e))
            return any_pb2.Any()
