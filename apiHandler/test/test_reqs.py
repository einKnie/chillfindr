"""Test availability of required packages."""
# from: https://stackoverflow.com/a/45474387/240950

import unittest
from pathlib import Path

import pkg_resources

_REQUIREMENTS_PATH = Path(__file__).with_name("requirements.txt")


class TestRequirements(unittest.TestCase):
    """Test availability of required packages."""

    def test_requirements(self):
        """Test that each required package is available."""
        # Ref: https://stackoverflow.com/a/45474387/
        requirements = pkg_resources.parse_requirements(_REQUIREMENTS_PATH.open())
        for requirement in requirements:
            requirement = str(requirement)
            with self.subTest(requirement=requirement):
                print("testing %s" %(requirement))
                pkg_resources.require(requirement)
