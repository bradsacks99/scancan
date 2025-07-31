""" test_scancan.py """
from src.config import SCAN_CAN_VERSION as __version__

def test_version():
    """
    Test that the __version__ variable is set to the expected version string.
    """
    assert __version__ == '0.1.0'
