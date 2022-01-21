# Django Settings Holder

[![Coverage Status](https://coveralls.io/repos/github/MrThearMan/django-settings-holder/badge.svg?branch=main)](https://coveralls.io/github/MrThearMan/django-settings-holder?branch=main)
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/MrThearMan/django-settings-holder/Tests)](https://github.com/MrThearMan/django-settings-holder/actions/workflows/main.yml)
[![PyPI](https://img.shields.io/pypi/v/django-settings-holder)](https://pypi.org/project/django-settings-holder)
[![GitHub](https://img.shields.io/github/license/MrThearMan/django-settings-holder)](https://github.com/MrThearMan/django-settings-holder/blob/main/LICENSE)
[![GitHub last commit](https://img.shields.io/github/last-commit/MrThearMan/django-settings-holder)](https://github.com/MrThearMan/django-settings-holder/commits/main)
[![GitHub issues](https://img.shields.io/github/issues-raw/MrThearMan/django-settings-holder)](https://github.com/MrThearMan/django-settings-holder/issues)


[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-settings-holder)](https://pypi.org/project/django-settings-holder)
[![PyPI - Django Version](https://img.shields.io/pypi/djversions/django-settings-holder)](https://pypi.org/project/django-settings-holder)

```shell
pip install django-settings-holder
```

---

**Documentation**: [https://mrthearman.github.io/django-settings-holder/](https://mrthearman.github.io/django-settings-holder/)

**Source Code**: [https://github.com/MrThearMan/django-settings-holder](https://github.com/MrThearMan/django-settings-holder)

---

This library provides utilities for Django extensions that want to define their own settings dictionaries.
Settings can be included in a SettingsHolder that allows them to be accessed via attributes.
User defined settings can be reloaded automatically to the SettingsHolder from the `setting_changed` signal.
Functions in dot import notation are automatically imported so that the imported function is available in
the SettingsHolder.

