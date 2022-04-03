import datetime
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Union

from junit_xml import TestCase, to_xml_report_string, TestSuite

from .utils import CaseFailure, Utils


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
                 export_on_success: bool = True,
                 severity_export_values: Tuple[str, ...] = DEFAULT_SEVERITY_LEVELS):
        self._format = fmt
        self._report_prefix = report_prefix
        self._export_on_success = export_on_success
        self._severity_export_values = severity_export_values
        if update_format_keys:
            self._update_format_keys()

    def _update_format_keys(self):
        self._format.case_classname = self._format.case_classname or self._format.case_name
        self._format.case_category = self._format.case_category or self._format.case_name

    def _get_test_case(self, entry: Dict[str, str], severity: str) -> Union[TestCase, None]:
        msg = json.dumps(entry, indent=4)
        case = TestCase(name=entry[self._format.case_name],
                        classname=entry[self._format.case_classname],
                        category=entry[self._format.case_category],
                        timestamp=entry.get(self._format.case_timestamp, str(datetime.datetime.now()))
                        )

        if severity in self._severity_export_values:
            failure = CaseFailure(message=msg, output=msg, type=severity)
            case.failures.append(failure)
        elif not self._export_on_success:
            return None

        if not case.is_failure():
            case.stdout = msg
        return case

    def collect(self, entries: List[Dict[str, str]],
                suite_name: str,
                report_dir: Optional[Path] = None,
                xml_suffix: str = ""
                ) -> str:
        report_dir = Utils.get_report_dir(report_dir)

        test_cases = list()
        for entry in entries:
            test_case = self._get_test_case(entry, entry.get(self._format.severity_key, None))
            if test_case is not None:
                test_cases.append(test_case)

        report_dir.mkdir(exist_ok=True)
        xml_report = to_xml_report_string(test_suites=[TestSuite(name=suite_name,
                                                                 test_cases=test_cases,
                                                                 timestamp=self._get_suite_timestamp(test_cases))])
        file_name = f"{self._report_prefix}_{suite_name}{f'_{xml_suffix}' if xml_suffix else ''}.xml"
        with open(report_dir.joinpath(file_name), "w") as f:
            f.write(xml_report)
            return f.name

    @classmethod
    def _get_suite_timestamp(cls, test_cases: List[TestCase]) -> str:
        return test_cases[0].timestamp if test_cases else str(datetime.datetime.now())
