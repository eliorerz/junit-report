from pathlib import Path

from junit_report import JunitTestSuite, JunitTestCase


REPORT_DIR = Path.cwd().joinpath(".reports")


@JunitTestSuite(REPORT_DIR)
def test_suite():
    first_test_case()
    other_test_case()


@JunitTestCase()
def other_test_case():
    nested_test_case()


@JunitTestCase()
def nested_test_case():
    pass


@JunitTestCase()
def first_test_case():
    pass


def main():
    test_suite()
    print("success")


if __name__ == '__main__':
    main()
