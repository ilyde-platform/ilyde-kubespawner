# encoding: utf-8
import os

# set the environment where we run kubespawner
# internal: for inside a kubernetes cluster
# external: for outside the cluster
CLUSTER_ENVIRONMENT = os.environ.get("CLUSTER_ENVIRONMENT") or "external"
