import os
from pathlib import Path

from src.junit_report.utils import Utils
from tests import REPORT_DIR


class TestJunitReport:
    def test_report_path_env_var(self):
        expected_with_none = REPORT_DIR.joinpath("new")
        os.environ["JUNIT_REPORT_DIR"] = str(expected_with_none)

        result_with_none = Utils.get_report_dir(None)
        assert result_with_none == expected_with_none

        expected_with_path = Path().cwd().joinpath("new_reports_dir")
        result = Utils.get_report_dir(expected_with_path)

        assert result == expected_with_path

        os.environ.pop(Utils.DEFAULT_REPORT_PATH_KEY)
