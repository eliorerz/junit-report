
junit-report
===========
---
This Python package adds more control to your tests by decorating your functions and pytest fixtures and exporting them as JUnit xml.

## Installation

`pip install junit-report`


##  Usage 

```python
import pytest

from junit_report import JunitTestSuite, JunitTestCase, JunitFixtureTestCase

class TestSomeThing:

    @pytest.fixture
    @JunitFixtureTestCase()
    def my_fixture(self):
        pass
    
    @JunitTestCase()
    def my_first_test_case(self):
        pass
    
    @JunitTestCase()
    def my_second_test_case(self, name: str):
        raise ValueError(f"Invalid name {name}")
    
    @JunitTestSuite()
    def test_suite(self, my_fixture):
        self.my_first_test_case()    
        self.my_second_test_case("John")

```


### Output
```xml
<?xml version="1.0" ?>
<?xml version="1.0" ?>
<testsuites disabled="0" errors="0" failures="1" tests="3" time="8.893013000488281e-05">
	<testsuite disabled="0" errors="0" failures="1" name="TestSomeThing_test_suite" skipped="0" tests="3" time="8.893013000488281e-05">
		<testcase name="my_fixture" time="0.000010" classname="TestSomeThing" class="fixture"/>
		<testcase name="my_first_test_case" time="0.000007" classname="TestSomeThing" class="function"/>
		<testcase name="my_second_test_case" time="0.000071" classname="TestSomeThing" class="function">
			<failure type="ValueError" message="Invalid name John">Traceback ... ValueError(f&quot;Invalid name {name}&quot;) ValueError: Invalid name John</failure>
		</testcase>
	</testsuite>
</testsuites>

```