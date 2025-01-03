"""
Simple pytest hooks for saving summary info (total numbers only) to a JSON file
(instead of using "--junit-xml", which doesn't and can't include warnings,
see https://github.com/pytest-dev/pytest/issues/2717).

If pytest "--log-level" option is set to any value, creates a file
"pytest-summary.json" in the current directory. GitHub actions will process it
using .github/workflows/summary.py to create run annotations.
"""
_pytest_summary = {}


def pytest_collection_modifyitems(session, config, items):
    """
    Called by pytest after collecting all tests
    (the only possibility to get their count).
    """
    _pytest_summary['tests'] = len(items)  # "collected items"


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    Called by pytest before reporting the summary
    (terminalreporter.stats has all the numbers except "collected items",
    which thus had to be obtained previously).
    """
    if config.getoption('log_level') is None:
        return
    # all KNOWN_TYPES from pytest/src/_pytest/terminal.py
    for name in ['failed', 'passed', 'skipped', 'deselected', 'xfailed',
                 'xpassed', 'warnings', 'error']:
        _pytest_summary[name] = len(terminalreporter.stats.get(name, []))
    import json
    with open('pytest-summary.json', 'w') as f:
        json.dump(_pytest_summary, f)
