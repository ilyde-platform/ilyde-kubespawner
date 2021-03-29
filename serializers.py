# encoding: utf-8
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
