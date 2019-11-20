import unittest

from os2datascanner.engine2.model.core import (
        Source, Handle, UnknownSchemeError, DeserialisationError)
from os2datascanner.engine2.model.data import DataSource, DataHandle
from os2datascanner.engine2.model.file import (
        FilesystemSource, FilesystemHandle)
from os2datascanner.engine2.model.filtered import (
        FilteredSource, FilteredHandle, FilterType)
from os2datascanner.engine2.model.http import WebSource, WebHandle
from os2datascanner.engine2.model.smb import SMBSource, SMBHandle
from os2datascanner.engine2.model.smbc import SMBCSource, SMBCHandle
from os2datascanner.engine2.model.tar import TarSource, TarHandle
from os2datascanner.engine2.model.zip import ZipSource, ZipHandle


class JSONTests(unittest.TestCase):
    def test_json_round_trip(self):
        example_handles = [
            FilesystemHandle(
                    FilesystemSource("/usr/share/common-licenses"),
                    "GPL-3"),
            DataHandle(
                    DataSource(b"Test", "text/plain"),
                    "file"),
            FilteredHandle(
                    FilteredSource(
                            FilesystemHandle(
                                    FilesystemSource("/usr/share/doc/coreutils"),
                                    "changelog.Debian.gz"),
                            FilterType.GZIP),
                    "changelog.Debian"),
            SMBHandle(
                    SMBSource(
                            "//SERVER/Resource", "username"),
                    "~ocument.docx"),
            SMBCHandle(
                    SMBCSource(
                            "//SERVER/Resource",
                            "username", "topsecret", "WORKGROUP8"),
                    "~ocument.docx"),
            ZipHandle(
                    ZipSource(
                            SMBCHandle(
                                    SMBCSource(
                                            "//SERVER/Resource",
                                            "username", driveletter="W"),
                                    "Confidential Documents.zip")),
                    "doc/Personal Information.docx"),
            WebHandle(
                    WebSource(
                            "https://secret.data.invalid/"),
                    "lottery-numbers-for-next-week.txt"),
            TarHandle(
                    TarSource(
                            FilesystemHandle(
                                    FilesystemSource(
                                            "/home/user"),
                                    "Downloads/data.tar.gz")),
                    "data0.txt")
        ]

        for handle in example_handles:
            with self.subTest(handle):
                json = handle.to_json_object()
                print(handle)
                print(json)
                self.assertEqual(handle, handle.from_json_object(json))
                print("--")

    def test_invalid_json(self):
        with self.assertRaises(UnknownSchemeError):
            Source.from_json_object({
                "type": "gopher",
                "hostname": "gopher.invalid"
            })
        with self.assertRaises(UnknownSchemeError):
            Handle.from_json_object({
                "type": "gopher",
                "source": {
                    "type": "gopher",
                    "hostname": "gopher.invalid"
                },
                "path": "/Reference"
            })

    def test_incomplete_json(self):
        with self.assertRaises(DeserialisationError):
            Source.from_json_object({
                "hostname": "gopher.invalid"
            })
        with self.assertRaises(DeserialisationError):
            Handle.from_json_object({
                "source": {
                    "type": "gopher",
                    "hostname": "gopher.invalid"
                },
                "path": "/Reference"
            })

    def test_double_json_registration(self):
        with self.assertRaises(ValueError):
            @Source.json_handler("file")
            def handle_json(j):
                pass
        with self.assertRaises(ValueError):
            @Handle.json_handler("file")
            def handle_json(j):
                pass
