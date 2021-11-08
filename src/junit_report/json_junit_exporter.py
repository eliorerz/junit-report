import datetime
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Dict

from junit_xml import TestCase, to_xml_report_string, TestSuite

from .utils import CaseFailure


@dataclass
class CaseFormatKeys:
    case_name: str
    severity_key: str
    case_classname: str = None
    case_category: str = None
    case_timestamp: str = None


class JsonJunitExporter:
    DEFAULT_SEVERITY_LEVELS = ("error", "critical", "fatal")
    REPORT_PREFIX = "junit_report"

    def __init__(self,
                 fmt: CaseFormatKeys,
                 update_format_keys: bool = True,
                 report_prefix: str = REPORT_PREFIX,
                 severity_export_values: Tuple[str, ...] = DEFAULT_SEVERITY_LEVELS):
        self._format = fmt
        self._report_prefix = report_prefix
        self._severity_export_values = severity_export_values
        if update_format_keys:
            self._update_format_keys()

    def _update_format_keys(self):
        self._format.case_classname = self._format.case_classname or self._format.case_name
        self._format.case_category = self._format.case_category or self._format.case_name

    def _get_failure_test_case(self, entry: Dict[str, str], severity: str) -> TestCase:
        case = TestCase(name=entry[self._format.case_name],
                        classname=entry[self._format.case_classname],
                        category=entry[self._format.case_category],
                        timestamp=entry.get(self._format.case_timestamp, str(datetime.datetime.now()))
                        )
        failure_msg = json.dumps(entry, indent=4)
        failure = CaseFailure(message=failure_msg, output=failure_msg, type=severity)
        case.failures.append(failure)
        return case

    def collect(self, entries: List[Dict[str, str]], report_dir: Path, suite_name: str) -> str:
        test_cases = list()
        for entry in entries:
            severity = entry.get(self._format.severity_key, None)
            if severity in self._severity_export_values:
                test_cases.append(self._get_failure_test_case(entry, severity))

        report_dir.mkdir(exist_ok=True)
        xml_report = to_xml_report_string(test_suites=[TestSuite(name=suite_name,
                                                                 test_cases=test_cases,
                                                                 timestamp=self._get_suite_timestamp(test_cases))])
        with open(report_dir.joinpath(f"{self._report_prefix}_{suite_name}.xml"), "w") as f:
            f.write(xml_report)
            return f.name

    @classmethod
    def _get_suite_timestamp(cls, test_cases: List[TestCase]) -> str:
        return test_cases[0].timestamp if test_cases else str(datetime.datetime.now())
