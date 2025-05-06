from os import path
import pytest
import numpy as np

RESOURCES = path.join(path.dirname(path.abspath(__file__)), "resources")

# Model parameter file paths
ECOTRACER_GROUP_INFO_PATH = path.join(
    RESOURCES, "test_inputs", "BlackSea-Ecotracer input.csv"
)
ECOTRACER_GROUP_INFO_PATH2 = path.join(
    RESOURCES, "test_inputs", "BlackSea-Ecotracer input 2.csv"
)
ECOSIM_GROUP_INFO_PATH = path.join(
    RESOURCES, "test_inputs", "BlackSea-Group info.csv"
)
VULNERABILITIES_PATH = path.join(
    RESOURCES, "test_inputs", "BlackSea-Vulnerabilities.csv"
)
CONTAMINANT_FORCING_PATH = path.join(
    RESOURCES, "test_inputs", "BlackSea-ContaminantForcing.csv"
)

def assert_arrays_close(expected, produced, rtol=1e-7, atol=1e-9, context=""):
    """
    Asserts that two numpy arrays are close element-wise.
    Provides detailed failure message if they are not.
    """
    if expected.shape != produced.shape:
        pytest.fail(
            f"Shape mismatch {context}: Expected {expected.shape}, Got {produced.shape}"
        )

    are_close = np.allclose(expected, produced, rtol=rtol, atol=atol)

    if not are_close:
        abs_diff = np.abs(expected - produced)
        max_abs_diff = np.max(abs_diff)
        max_abs_diff_idx = np.unravel_index(np.argmax(abs_diff), abs_diff.shape)

        num_diff = np.sum(~np.isclose(expected, produced, rtol=rtol, atol=atol))
        sum_abs_diff = np.sum(abs_diff)

        fail_msg = (
            f"Array comparison failed {context} (rtol={rtol}, atol={atol}).\n"
            f"  Max absolute difference: {max_abs_diff:.4g} at index {max_abs_diff_idx}\n"
            f"  Number of differing elements: {num_diff} / {expected.size}\n"
            f"  Total absolute difference sum: {sum_abs_diff:.4g}"
        )
        pytest.fail(fail_msg)
