import os
import pytest
from .context import mapsrc

# the below two lines are for pip installing with test option and when
# the tests will open files:
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
os.chdir(CURRENT_DIR)


def test_mapsrc():
    assert 1 == 1
