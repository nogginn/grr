#!/usr/bin/env python
#
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


"""This is the main cron program to perform various housekeeping tasks."""



import re
import sys

from grr.client import conf

# Support bt storage
from grr.lib import registry
from grr.lib import mongo_data_store

from grr.lib.aff4_objects import cronjobs


def main(unused_argv):
  # Initialise everything
  registry.Init()

  cronjobs.RunAllCronJobs()

if __name__ == "__main__":
  conf.StartMain(main)