import os

import pytest

from jwst.lib.suffix import replace_suffix
from jwst.regtest.st_fitsdiff import STFITSDiff as FITSDiff
from jwst.stpipe import Step


@pytest.fixture(scope="module")
def run_pipeline(rtdata_module):
    """Run the calwebb_spec2 pipeline on a NIRSpec lamp exposure.

    Input data has EXP_TYPE = NRS_AUTOWAVE, OPMODE = FIXEDSLIT
    """
    rtdata = rtdata_module

    # Get the input exposure
    rtdata.get_data("nirspec/lamp/jw01125001001_03104_00010_nrs2_rate.fits")

    # Run the calwebb_spec2 pipeline; save results from intermediate steps
    args = [
        "jwst.pipeline.Spec2Pipeline",
        rtdata.input,
        "--steps.assign_wcs.save_results=true",
        "--steps.extract_2d.save_results=true",
        "--steps.flat_field.save_results=true",
    ]
    Step.from_cmdline(args)

    return rtdata


@pytest.mark.bigdata
@pytest.mark.parametrize("suffix", ["assign_wcs", "extract_2d", "flat_field", "cal", "s2d", "x1d"])
def test_nirspec_lamp_fs_spec2(run_pipeline, fitsdiff_default_kwargs, suffix):
    """Regression test for calwebb_spec2 on NIRSpec lamp in Fixed-Slit mode."""

    # Run the pipeline and retrieve outputs
    rtdata = run_pipeline
    output = replace_suffix(os.path.splitext(os.path.basename(rtdata.input))[0], suffix) + ".fits"
    rtdata.output = output

    # Get the truth files
    rtdata.get_truth(os.path.join("truth/test_nirspec_lamp_spec2", output))

    # Compare the results
    diff = FITSDiff(rtdata.output, rtdata.truth, **fitsdiff_default_kwargs)
    assert diff.identical, diff.report()
