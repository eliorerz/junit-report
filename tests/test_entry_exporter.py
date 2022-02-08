import json
import shutil
from pathlib import Path

import pytest
import xmltodict

from src.junit_report import JsonJunitExporter, CaseFormatKeys
from tests import REPORT_DIR, BaseTest

JSON_DATA = """
[
  {
    "id": "48595d36-9682-4c88-8b60-607a91229743",
    "time": "2021-11-07T00:31:33.630Z",
    "message": "Init message",
    "severity": "info"
  },
  {
    "id": "48595d36-9682-4c88-8b60-607a91229745",
    "time": "2021-11-07T00:31:33.636Z",
    "message": "Successfully registered",
    "severity": "info"
  },
  {
    "id": "48595d36-9682-4c88-8b60-607a91229746",
    "time": "2021-11-07T00:31:36.290Z",
    "message": "Updated event",
    "severity": "info"
  },
  {
    "id": "48595d36-9682-4c88-8b60-607a91229748",
    "time": "2021-11-07T00:32:56.284Z",
    "message": "Validation that used to succeed is now failing",
    "severity": "warning"
  },
  {
    "id": "48595d36-9682-4c88-8b60-607a91229749",
    "time": "2021-11-07T00:33:01.285Z",
    "message": "Fatal error",
    "extra_field": "This is an Error event",
    "severity": "error"
  },
  {
    "id": "48595d36-9682-4c88-8b60-607a91229740",
    "time": "2021-11-07T00:33:15.285Z",
    "message": "Critical error - KeyError on python script",
    "severity": "critical"
  }
]
"""


class TestJsonJunitExporter(BaseTest):

    @staticmethod
    def get_test_report(test_report_path: Path):
        with open(test_report_path) as f:
            return xmltodict.parse(f.read())

    @classmethod
    @pytest.fixture(autouse=True)
    def cleanup(cls):
        yield
        shutil.rmtree(REPORT_DIR, ignore_errors=True)

    def test_parsed_events(self):
        events = json.loads(JSON_DATA)
        failures_exporter = JsonJunitExporter(fmt=CaseFormatKeys(case_name="id", severity_key="severity"),
                                              export_on_success=False)
        file_name = failures_exporter.collect(events, suite_name="failures_test_suite", report_dir=REPORT_DIR)
        self.assert_xml_report_results_with_cases(self.get_test_report(Path(file_name)),
                                                  testsuite_tests=2, failures=2, testsuite_name="failures_test_suite")

    def test_all_parsed_events(self):
        events = json.loads(JSON_DATA)
        all_exporter = JsonJunitExporter(fmt=CaseFormatKeys(case_name="id", severity_key="severity"))
        file_name = all_exporter.collect(events, suite_name="all_test_suite", report_dir=REPORT_DIR)
        self.assert_xml_report_results_with_cases(self.get_test_report(Path(file_name)),
                                                  testsuite_tests=6, failures=2, testsuite_name="all_test_suite")

    def test_empty_events(self):
        events = json.loads("[]")
        exporter = JsonJunitExporter(fmt=CaseFormatKeys(case_name="id", severity_key="severity", case_timestamp="time"))
        file_name = exporter.collect(events, suite_name="empty_test_suite", report_dir=REPORT_DIR)
        self.assert_xml_report_results_with_cases(self.get_test_report(Path(file_name)),
                                                  testsuite_tests=0, failures=0, testsuite_name="empty_test_suite")
