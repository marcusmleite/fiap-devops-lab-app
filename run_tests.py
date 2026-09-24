import os
import sys
import time
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

TEST_DIR = Path(__file__).parent / "tests"
RESULTS_DIR = Path(__file__).parent / "test-results"
RESULTS_FILE = RESULTS_DIR / "unittest.xml"


class JUnitResult(unittest.TextTestResult):
    def startTest(self, test):
        test._started_at = time.time()
        super().startTest(test)

    def addSuccess(self, test):
        test._duration = time.time() - getattr(test, "_started_at", time.time())
        super().addSuccess(test)

    def addFailure(self, test, err):
        test._duration = time.time() - getattr(test, "_started_at", time.time())
        super().addFailure(test, err)

    def addError(self, test, err):
        test._duration = time.time() - getattr(test, "_started_at", time.time())
        super().addError(test, err)


class JUnitRunner(unittest.TextTestRunner):
    resultclass = JUnitResult


def write_junit_xml(result):
    RESULTS_DIR.mkdir(exist_ok=True)
    failures = dict((test.id(), err) for test, err in result.failures)
    errors = dict((test.id(), err) for test, err in result.errors)
    suite = ET.Element(
        "testsuite",
        {
            "name": "fiap-devops-lab-tests",
            "tests": str(result.testsRun),
            "failures": str(len(result.failures)),
            "errors": str(len(result.errors)),
            "skipped": str(len(result.skipped)),
        },
    )
    all_tests = []
    for test_case in result.successes if hasattr(result, "successes") else []:
        all_tests.append(test_case)
    for test_case, _ in result.failures + result.errors + result.skipped:
        all_tests.append(test_case)
    # TextTestResult does not store successes by default; discover test names again for reporting.
    discovered = unittest.defaultTestLoader.discover(str(TEST_DIR))
    for test in iter_tests(discovered):
        test_id = test.id()
        case = ET.SubElement(
            suite,
            "testcase",
            {
                "classname": test.__class__.__name__,
                "name": test._testMethodName,
                "time": str(round(getattr(test, "_duration", 0.0), 4)),
            },
        )
        if test_id in failures:
            ET.SubElement(case, "failure", {"message": "failure"}).text = failures[test_id]
        if test_id in errors:
            ET.SubElement(case, "error", {"message": "error"}).text = errors[test_id]
    ET.ElementTree(suite).write(RESULTS_FILE, encoding="utf-8", xml_declaration=True)


def iter_tests(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from iter_tests(item)
        else:
            yield item


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover(str(TEST_DIR))
    runner = JUnitRunner(verbosity=2)
    result = runner.run(suite)
    write_junit_xml(result)
    print(f"JUnit XML gerado em: {RESULTS_FILE}")
    sys.exit(0 if result.wasSuccessful() else 1)
