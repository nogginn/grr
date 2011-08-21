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


"""Main Django renderer."""

import crypt


from django import http
from django import shortcuts

from grr.client import conf as flags
import logging

# Support grr plugins (These only need to be imported here)
from grr.gui import plugins
from grr.gui import renderers
from grr.lib import log
from grr.lib import stats

SERVER_NAME = "GRR Admin Console"
FLAGS = flags.FLAGS

# Counters used here
stats.STATS.grr_admin_ui_unknown_renderer = 0
stats.STATS.grr_admin_ui_renderer_called = 0
stats.STATS.grr_admin_ui_access_denied = 0
stats.STATS.grr_admin_ui_renderer_failed = 0

LOGGER = log.GrrLogger(component="AdminUI")


AUTHORIZED_USERS = {}


def LoadPasswordFile(authorized_users):
  for line in open(FLAGS.htpasswd):
    username, crypt_hash = line.strip().split(":")
    authorized_users[username] = crypt_hash

# This file is loaded by django upon the first request - therefore FLAGS is
# already initialized.
if FLAGS.htpasswd is not None:
  LoadPasswordFile(AUTHORIZED_USERS)


def SecurityCheck(func):
  """Generic request checking decorator.

  Args:
    func: The function being wrapped.

  Returns:
    A function which is used to wrap a RequestHandler.

  This will get called for all requests that get passed through one of our
  handlers.
  """

  def Wrapper(request, *args, **kwargs):
    """Wrapping function."""
    event_id = LOGGER.GetNewEventId()

    # Modify request adding an event_id attribute to track the event
    request.event_id = event_id
    request.user = ""

    if AUTHORIZED_USERS:
      authorized = False
      try:
        auth_type, authorization = request.META.get(
            "HTTP_AUTHORIZATION", " ").split(" ", 1)
        if auth_type == "Basic":
          user, password = authorization.decode("base64").split(":", 1)
          crypt_hash = AUTHORIZED_USERS[user]
          # Check the hash is ok
          salt = crypt_hash[:2]
          if crypt.crypt(password, salt) == crypt_hash:
            authorized = True
            # The password is ok - update the user
            request.user = user

      except (IndexError, KeyError): pass

      if not authorized:
        result = http.HttpResponse("Unauthorized", status=401)
        result["WWW-Authenticate"] = "Basic realm='Secure Area'"
        return result

    # Modify this to implement some security checking (e.g. username/password,
    # SSL etc).
    response = func(request, *args, **kwargs)

    return response

  return Wrapper


@SecurityCheck
def Homepage(unused_request):
  """Basic handler to render the index page."""

  context = {"title": SERVER_NAME}
  return shortcuts.render_to_response("base.html", context)


@SecurityCheck
def RenderGenericRenderer(request):
  """Django handler for rendering registered GUI Elements."""
  try:
    action, table_name = request.path.split("/")[-2:]

    table_cls = renderers.Renderer.NewPlugin(name=table_name)
  except KeyError:
    stats.STATS.grr_admin_ui_unknown_renderer += 1
    return AccessDenied("Error: Renderer %s not found" % table_name)

  # Check that the action is valid
  ["Layout", "RenderAjax", "Download"].index(action)
  table = table_cls()
  stats.STATS.grr_admin_ui_renderer_called += 1
  result = http.HttpResponse(mimetype="text/html")

  # This is needed to force the server to use a session cookie - this is
  # required for the django CSRF mechanism.
  request.session.set_test_cookie()

  # Pass the request only from POST parameters
  if FLAGS.debug:
    # Allow both for debugging
    request.REQ = request.REQUEST
  else:
    # Only POST in production for CSRF protections.
    request.REQ = request.POST

  # Allow potential exceptions to be raised here so we can see them in the debug
  # log.
  result = getattr(table, action)(request, result) or result

  if not isinstance(result, http.HttpResponse):
    raise RuntimeError("Renderer returned invalid response %r" % result)

  # Prepend bad json to break json attacks as per:
  content_type = result.get("Content-Type", 0)
  if content_type and "json" in content_type.lower():
    result.content = ")]}\n" + result.content

  return result


def AccessDenied(message):
  """Return an access denied Response object."""
  response = shortcuts.render_to_response("404.html", {"message": message})
  logging.warn(message)
  response.status_code = 403
  stats.STATS.grr_admin_ui_access_denied += 1
  return response


def ServerError(unused_request, template_name="500.html"):
  """500 Error handler."""
  stats.STATS.grr_admin_ui_renderer_failed += 1
  return shortcuts.render_to_response(template_name)