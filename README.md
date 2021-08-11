
# Junit-Report

This Python package adds more control to your tests by decorating your functions and pytest fixtures and exporting them as JUnit xml.

**Table of contents**

- [Junit-Report](#junit-report)
  - [Installation](#installation)
  - [Usage](#usage)
  - [OS parameters used for configuration](#os-parameters-used-for-configuration)


## Installation

```bash
pip install junit-report
```


##  Usage 

```python
import pytest

from junit_report import JunitTestSuite, JunitTestCase, JunitFixtureTestCase

class TestSomeThing:

    @pytest.fixture
    @JunitFixtureTestCase()
    def my_fixture(self):
        # do stuff ..
        
        @JunitTestCase()
        def nested_case():
          pass
        
        yield nested_case
        
    @JunitTestCase()
    def my_first_test_case(self):
        pass
    
    @JunitTestCase()
    def my_second_test_case(self, name: str):
        raise ValueError(f"Invalid name {name}")
    
    @JunitTestSuite()
    def test_suite(self, my_fixture):
        my_fixture()
        self.my_first_test_case()
        self.my_second_test_case("John")

```


### Output
```xml
<?xml version="1.0" ?>
<testsuites disabled="0" errors="0" failures="1" tests="4" time="0.000301361083984375">
	<testsuite disabled="0" errors="0" failures="1" name="TestSomeThing_test_suite" skipped="0" tests="4" time="0.000301361083984375">
		<testcase name="my_fixture" time="0.000163" classname="TestSomeThing" class="fixture"/>
		<testcase name="nested_case" time="0.000034" classname="module_name.test" class="function"/>
		<testcase name="my_first_test_case" time="0.000017" classname="TestSomeThing" class="function"/>
		<testcase name="my_second_test_case" time="0.000087" classname="TestSomeThing" class="function">
			<failure type="ValueError" message="Invalid name John">Traceback (most recent call last): ... ValueError: Invalid name John</failure>
		</testcase>
	</testsuite>
</testsuites>
```

## OS parameters used for configuration

| Variable                    | Description                                                                                                                                 |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| JUNIT_REPORT_DIR            | Reports directory where the reports will be extracted. If it does not exist - create it.                                                        |
