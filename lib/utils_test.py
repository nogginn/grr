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

"""Tests for utility classes."""



from grr.client import conf
from grr.lib import test_lib
from grr.lib import utils
from grr.proto import jobs_pb2


class StoreTests(test_lib.GRRBaseTest):
  """Store tests."""

  def test01StoreExpiration(self):
    """Testing store removes objects when full."""
    s = utils.FastStore(max_size=5)
    keys = []
    for i in range(0, 100):
      keys.append(s.Put(i, i))

    ## This should not raise
    s.Get(keys[-1])

    # This should raise though
    self.assertRaises(KeyError, s.Get, keys[0])

  def test02StoreRefresh(self):
    """Test that store keeps recently gotten objects fresh."""
    s = utils.FastStore(max_size=5)
    keys = []
    for i in range(0, 5):
      keys.append(s.Put(i, i))

    ## This should not raise because keys[0] should be refreshed each time its
    ## gotten
    for i in range(0, 1000):
      s.Get(keys[0])
      s.Put(i, i)

  def test03Expire(self):
    """Tests the expire mechanism."""
    s = utils.FastStore(max_size=100)
    key = "test1"
    s.Put(key, 1)

    # This should not raise
    self.assertEqual(s.Get(key), 1)
    s.ExpireObject(key)

    self.assertRaises(KeyError, s.Get, key)

  def test04CallBack(self):
    """Test that callbacks are called using object destruction."""
    results = []

    def Callback(obj):
      results.append(obj)

    s = utils.FastStore(max_size=5, kill_cb=Callback)
    for i in range(0, 10):
      s.Put(i, i)

    # Only the first 5 messages have been expired (and hence called)
    self.assertEqual(results, range(0, 5))


class ProtoDictTests(test_lib.GRRBaseTest):
  """ProtoDict tests."""

  def setUp(self):
    self.proto = jobs_pb2.Dict()
    self.dict_test = {}
    for i in range(10):
      self.dict_test[unicode(i)] = unicode(i)
      i = jobs_pb2.DataBlob(string=unicode(i))
      self.proto.dat.add(k=i, v=i)
    for i in range(10):
      self.dict_test[i] = i
      i = jobs_pb2.DataBlob(integer=i)
      self.proto.dat.add(k=i, v=i)
    for i in range(10):
      self.dict_test[str(i)] = str(i)
      i = jobs_pb2.DataBlob(string=str(i))
      self.proto.dat.add(k=i, v=i)
    for i in range(10):
      test_pb = jobs_pb2.Interface(mac_address="AA:BB:CC:DD:EE:FF")
      self.dict_test["p" + str(i)] = test_pb
      v = jobs_pb2.DataBlob(data=test_pb.SerializeToString(),
                            proto_name="Interface")
      k = jobs_pb2.DataBlob(string="p" + str(i))
      self.proto.dat.add(k=k, v=v)
    for i in range(10):
      self.dict_test["none" + str(i)] = None
      v = jobs_pb2.DataBlob(none="None")
      k = jobs_pb2.DataBlob(string="none" + str(i))
      self.proto.dat.add(k=k, v=v)
    for i in range(10):
      self.dict_test["bool" + str(i)] = True
      v = jobs_pb2.DataBlob(boolean=True)
      k = jobs_pb2.DataBlob(string="bool" + str(i))
      self.proto.dat.add(k=k, v=v)

  def test01ParsingNone(self):
    """Testing initializing from None."""
    protodict = utils.ProtoDict(None)

    self.assertEqual(type(protodict._proto), jobs_pb2.Dict)
    self.assertEqual(protodict.ToDict(), {})

  def test02InitializingFromProto(self):
    """Test initializing from protobuf."""
    # Initialize from proto
    proto_under_test = utils.ProtoDict(self.proto)
    self.assertEqual(proto_under_test.ToDict(), self.dict_test)

  def test03InitializingFromDict(self):
    """Test initializing from dict."""
    # Initialize from dict
    proto_under_test = utils.ProtoDict(self.dict_test)
    self.assertEqual(proto_under_test.ToDict(), self.dict_test)

  def test04InitializingFromString(self):
    """Test initializing from string."""
    # Initialize from dict
    string = self.proto.SerializeToString()
    proto_under_test = utils.ProtoDict(string)
    self.assertEqual(proto_under_test.ToDict(), self.dict_test)
    self.assertEqual(proto_under_test.ToProto().SerializeToString(), string)

  def test05Serializing(self):
    """Test initializing from dict."""
    # Initialize from dict
    proto_under_test = utils.ProtoDict(self.proto)
    self.assertEqual(proto_under_test.ToDict(), self.dict_test)
    self.assertEqual(str(proto_under_test), self.proto.SerializeToString())

  def test06GetItem(self):
    """Test __getitem__."""
    proto_under_test = utils.ProtoDict(self.dict_test)

    for k in self.dict_test:
      self.assertEqual(proto_under_test[k], self.dict_test[k])

  def test07SetItem(self):
    """Test __setitem__."""
    proto_under_test = utils.ProtoDict()

    for k in self.dict_test:
      proto_under_test[k] = self.dict_test[k]

    self.assertEqual(proto_under_test.ToDict(), self.dict_test)

  def test08MultiAssign(self):
    """Test we can assign multiple times to the same proto dict."""
    proto_under_test = utils.ProtoDict(self.dict_test)
    proto_under_test[1] = 1
    proto_under_test[1] = 1
    self.assertEqual(proto_under_test[1], 1)

  def test09Delete(self):
    proto_under_test = utils.ProtoDict(dict(a="value1", b="value2"))

    self.assertEqual(proto_under_test["a"], "value1")
    self.assertEqual(proto_under_test["b"], "value2")

    del proto_under_test["a"]
    self.assertRaises(KeyError, proto_under_test.__getitem__, "a")
    self.assertEqual(proto_under_test.Get("a", "default"), "default")
    self.assertEqual(proto_under_test["b"], "value2")

  def test10AssignNone(self):
    """Test None assignment via dict and directly."""
    self.dict_test["none1"] = None

    proto_under_test = utils.ProtoDict(self.dict_test)
    self.assertEqual(proto_under_test["none1"], None)

    proto_under_test["none2"] = None
    self.assertEqual(proto_under_test["none2"], None)

  def test10AssignBool(self):
    """Test boolean assignment via dict and directly."""
    self.dict_test["bool1"] = True
    self.dict_test["bool2"] = False

    proto_under_test = utils.ProtoDict(self.dict_test)
    self.assertEqual(proto_under_test["bool1"], True)
    self.assertEqual(proto_under_test["bool2"], False)

    proto_under_test["bool3"] = True
    proto_under_test["bool4"] = False
    self.assertEqual(proto_under_test["bool3"], True)
    self.assertEqual(proto_under_test["bool4"], False)

  def test11ProtoDictIterator(self):
    proto_under_test = utils.ProtoDict(self.dict_test)
    for key in self.dict_test:
      self.assertTrue(key in proto_under_test)

    for key in proto_under_test:
      self.assertTrue(key in self.dict_test)

    self.assertFalse("nonexistent" in proto_under_test)


class UtilsTest(test_lib.GRRBaseTest):
  """Utilities tests."""

  def testNormpath(self):
    """Test our Normpath."""
    data = [
        ("foo/../../../../", "/"),
        ("/foo/../../../../bar", "/bar"),
        ("/foo/bar/../3sdfdfsa/.", "/foo/3sdfdfsa"),
        ("../foo/bar", "/foo/bar"),
        ("./foo/bar", "/foo/bar"),
        ("/", "/"),
        ]

    for test, expected in data:
      self.assertEqual(expected, utils.NormalizePath(test))

  def testPathspecToAff4(self):
    """Test PathspecToAff4."""
    pb = jobs_pb2.Path()

    data = [
        ("\\\\.\\Volume{111}", "\\Windows\\", 0, "/fs/os/Volume{111}/Windows/"),
        ("\\\\.\\V{111}\\", "Windows\\file", 0, "/fs/os/V{111}/Windows/file"),
        ("\\\\.\\Volume{111}", "/Windows/", 0, "/fs/os/Volume{111}/Windows/"),
        ("\\\\.\\V{111}\\", "Windows\\file", 1, "/fs/raw/V{111}/Windows/file"),
        ("", "HKEY_LOCAL_MACHINE\\SOFTWARE", 2,
         "/registry/HKEY_LOCAL_MACHINE/SOFTWARE"),
        ]

    for device, path, ptype, result in data:
      pb.device = device
      pb.path = path
      pb.pathtype = ptype

      self.assertEqual(utils.PathspecToAff4(pb), result)


def main(argv):
  test_lib.main(argv)

if __name__ == "__main__":
  conf.StartMain(main)