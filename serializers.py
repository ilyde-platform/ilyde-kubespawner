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
from typing import Callable
from enum import Enum

from marshmallow import Schema, fields
from google.protobuf import json_format
from marshmallow_enum import EnumField


def protobuf_to_dict(message):
    return json_format.MessageToDict(
        message,
        preserving_proto_field_name=True
    )


class ResourceType(Enum):
    DEPLOYMENT = 1
    INGRESS = 2
    SERVICE = 3
    POD = 4
    JOB = 5
    CRONJOB = 6
    PVC = 7


class FileSerializer(Schema):
    namespace = fields.Str(required=True)
    content = fields.Str(required=True)


class ServiceSerializer(Schema):
    namespace = fields.Str(required=True)
    name = fields.Str(required=True)
    selector = fields.Str(required=True)
    port = fields.Str(required=True)
    target = fields.Str(required=True)


class ResourceSerializer(Schema):
    namespace = fields.Str(required=True)
    name = fields.Str(required=True)
    type = EnumField(ResourceType, required=True)


class OperationStatusSerializer(Schema):
    status = fields.Integer()
    message = fields.Str()
