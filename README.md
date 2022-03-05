# Django Settings Holder

[![Coverage Status][coverage-badge]][coverage]
[![GitHub Workflow Status][status-badge]][status]
[![PyPI][pypi-badge]][pypi]
[![GitHub][licence-badge]][licence]
[![GitHub Last Commit][repo-badge]][repo]
[![GitHub Issues][issues-badge]][issues]
[![Python Version][version-badge]][pypi]

```shell
pip install django-settings-holder
```

---

**Documentation**: [https://mrthearman.github.io/django-settings-holder/](https://mrthearman.github.io/django-settings-holder/)

**Source Code**: [https://github.com/MrThearMan/django-settings-holder/](https://github.com/MrThearMan/django-settings-holder/)

---

This library provides utilities for Django extensions that want to define their own settings dictionaries.
Settings can be included in a SettingsHolder that allows them to be accessed via attributes.
User defined settings can be reloaded automatically to the SettingsHolder from the `setting_changed` signal.
Functions in dot import notation are automatically imported so that the imported function is available in
the SettingsHolder.


[coverage-badge]: https://coveralls.io/repos/github/MrThearMan/django-settings-holder/badge.svg?branch=main
[status-badge]: https://img.shields.io/github/workflow/status/MrThearMan/django-settings-holder/Tests
[pypi-badge]: https://img.shields.io/pypi/v/django-settings-holder
[licence-badge]: https://img.shields.io/github/license/MrThearMan/django-settings-holder
[repo-badge]: https://img.shields.io/github/last-commit/MrThearMan/django-settings-holder
[issues-badge]: https://img.shields.io/github/issues-raw/MrThearMan/django-settings-holder
[version-badge]: https://img.shields.io/pypi/pyversions/django-settings-holder

[coverage]: https://coveralls.io/github/MrThearMan/django-settings-holder?branch=main
[status]: https://github.com/MrThearMan/django-settings-holder/actions/workflows/main.yml
[pypi]: https://pypi.org/project/django-settings-holder
[licence]: https://github.com/MrThearMan/django-settings-holder/blob/main/LICENSE
[repo]: https://github.com/MrThearMan/django-settings-holder/commits/main
[issues]: https://github.com/MrThearMan/django-settings-holder/issues