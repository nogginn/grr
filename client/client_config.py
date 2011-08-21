#!/usr/bin/env python

# Copyright 2010 Google Inc.
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


"""Various configuration related things."""



import os

# Windows service name
SERVICE_NAME = "GRR Monitor"
SERVICE_DISPLAY_NAME = "GRR Enterprise System Monitor"

try:
  LOGFILE_PATH = "%s/system32/logfiles/GRRlog.txt" % os.environ["WINDIR"]
except KeyError:
  LOGFILE_PATH = "/tmp/GRRlog.txt"

# This is the version of this client.
NETWORK_API = 1


# Certificates: Separate CA certificates are stored here. The --camode argument
# in the client sets which one of these the client trusts. This provides
# enforced isolation of the environments.

CACERTS = {
    "TEST": """
-----BEGIN CERTIFICATE-----
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
ImKbVCFIXYW/vECT2R/v
-----END CERTIFICATE-----
"""
}