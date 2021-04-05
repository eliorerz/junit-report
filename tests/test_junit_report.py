import shutil

import pytest
import xmltodict

from src.junit_report import CaseFailure, JunitTestCase, JunitTestSuite, SuiteNotExistError
from tests import REPORT_DIR, BaseTest


class TestJunitReport(BaseTest):
    @classmethod
    @pytest.fixture(autouse=True)
    def teardown(cls):
        yield
        shutil.rmtree(REPORT_DIR, ignore_errors=True)

    @pytest.fixture
    def base_class(self):
        class A:
            REPORT_PATH = REPORT_DIR.joinpath("junit_A_test_suite2_report.xml")
            ERROR_MESSAGE = "Some error"

            @JunitTestCase()
            def _test_case1(self):
                pass

            @JunitTestCase()
            def _test_case2(self):
                pass

            @JunitTestCase()
            def _test_case3(self):
                pass

            @JunitTestCase()
            def _exception_case(self):
                raise ValueError(self.ERROR_MESSAGE)

        return A

    @pytest.fixture
    def test_suite_single_case(self, base_class):
        class A(base_class):
            @JunitTestSuite(REPORT_DIR)
            def test_suite2(self):
                self._test_case1()

        yield A()

    @pytest.fixture
    def multiple_cases_class(self, base_class):
        class A(base_class):
            @JunitTestSuite(REPORT_DIR)
            def test_suite2(self):
                self._test_case1()
                self._test_case2()
                self._test_case3()

        yield A()

    @pytest.fixture
    def exception_class(self, base_class):
        class A(base_class):
            @JunitTestSuite(REPORT_DIR)
            def test_suite2(self):
                self._exception_case()
                self._test_case1()

        yield A()

    @pytest.fixture
    def exception_class_multiple_cases(self, base_class):
        class A(base_class):
            @JunitTestSuite(REPORT_DIR)
            def test_suite2(self):
                self._test_case1()
                self._test_case2()
                self._exception_case()
                self._test_case3()

        yield A()

    def test_single_testcase(self, test_suite_single_case):
        test_suite_single_case.test_suite2()

        with open(test_suite_single_case.REPORT_PATH) as f:
            xml_results = xmltodict.parse(f.read())

        cases = self.assert_xml_report_results(xml_results, testsuite_tests=1, testsuite_name="A_test_suite2")

        assert cases["@classname"] == "A"
        assert cases["@name"] == "_test_case1"

        self.delete_test_suite(test_suite_single_case.test_suite2.__wrapped__)

    def test_multiple_testcase(self, multiple_cases_class):
        multiple_cases_class.test_suite2()

        with open(multiple_cases_class.REPORT_PATH) as f:
            xml_results = xmltodict.parse(f.read())

        cases = self.assert_xml_report_results(xml_results, testsuite_tests=3, testsuite_name="A_test_suite2")

        assert isinstance(cases, list)
        i = 1
        for case in cases:
            assert case["@classname"] == "A"
            assert case["@name"] == f"_test_case{i}"
            i += 1

        self.delete_test_suite(multiple_cases_class.test_suite2.__wrapped__)

    def test_exception_on_single_case(self, exception_class):

        with pytest.raises(ValueError):
            exception_class.test_suite2()

        with open(exception_class.REPORT_PATH) as f:
            xml_results = xmltodict.parse(f.read())

        self.assert_xml_report_results(xml_results, failures=1, testsuite_tests=1, testsuite_name="A_test_suite2")

        self.delete_test_suite(exception_class.test_suite2.__wrapped__)

    def test_exception_on_multiple_cases(self, exception_class_multiple_cases):
        with pytest.raises(ValueError):
            exception_class_multiple_cases.test_suite2()

        with open(exception_class_multiple_cases.REPORT_PATH) as f:
            xml_results = xmltodict.parse(f.read())

        cases = self.assert_xml_report_results(
            xml_results, failures=1, testsuite_tests=3, testsuite_name="A_test_suite2"
        )

        assert isinstance(cases, list)
        i = 1
        for case in cases:
            assert case["@classname"] == "A"
            if i == 3:
                assert case["@name"] == "_exception_case"
                assert case["failure"]["@type"] == "ValueError"
                assert case["failure"]["@message"] == exception_class_multiple_cases.ERROR_MESSAGE
            i += 1

        self.delete_test_suite(exception_class_multiple_cases.test_suite2.__wrapped__)

    def test_register_not_exist(self):
        from junit_xml import TestCase

        def some_suite():
            pass

        JunitTestSuite.FAIL_ON_MISSING_SUITE = True
        with pytest.raises(SuiteNotExistError):
            JunitTestSuite.register_case(TestCase("case_name"), some_suite)

        JunitTestSuite.FAIL_ON_MISSING_SUITE = False
        JunitTestSuite.register_case(TestCase("case_name"), some_suite)

    def test_register(self):
        from junit_xml import TestCase

        start = len(JunitTestSuite._junit_suites)

        @JunitTestSuite()
        def suite_name1():
            pass

        @JunitTestSuite()
        def suite_name2():
            pass

        @JunitTestSuite()
        def suite_name3():
            pass

        assert len(JunitTestSuite._junit_suites) == start + 3

        JunitTestSuite.register_case(TestCase("case_name"), suite_name1.__wrapped__)
        JunitTestSuite.register_case(TestCase("case_name"), suite_name2.__wrapped__)
        JunitTestSuite.register_case(TestCase("case_name"), suite_name3.__wrapped__)

        JunitTestSuite._junit_suites.pop(suite_name1.__wrapped__)
        JunitTestSuite._junit_suites.pop(suite_name2.__wrapped__)
        JunitTestSuite._junit_suites.pop(suite_name3.__wrapped__)

    def test_case_failure(self):
        cf = CaseFailure("some message", "bla bla")

        assert cf.message == cf["message"]
        assert cf.output == cf["output"]
        assert cf.type == cf["type"]

    def test_register_two_suites_same_name(self):
        start = len(JunitTestSuite._junit_suites)

        class ClassA:
            @JunitTestSuite(REPORT_DIR)
            def test_suite(self):
                self.test_case()

            @JunitTestCase()
            def test_case(self):
                pass

        class ClassB:
            @JunitTestSuite(REPORT_DIR)
            def test_suite(self):
                self.test_case()

            @JunitTestCase()
            def test_case(self):
                pass

        ClassA().test_suite()
        ClassB().test_suite()

        assert len(JunitTestSuite._junit_suites) - start == 2
        assert len(list(REPORT_DIR.glob("*.xml"))) == 2

        JunitTestSuite._junit_suites.pop(ClassA.test_suite.__wrapped__)
        JunitTestSuite._junit_suites.pop(ClassB.test_suite.__wrapped__)
