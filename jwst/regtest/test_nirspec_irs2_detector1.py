""" Test for the detector1 pipeline using NIRSpec data in IRS2 mode. This takes
    an uncal file and generates the stage 1 FITS files (rate) along with the
    intermediate products."""

import os
import pytest

from astropy.io.fits.diff import FITSDiff
from jwst.stpipe import Step

@pytest.fixture(scope="module")
def run_pipeline(rtdata_module, jail):
    """Run calwebb_Detector1 pipeline on NIRSpec uncal data. This test is for
       data taken with the IRS2 mode. The steps are similar to the NIRCam level
       2a test but the IRS2 mode tests different paths in the same modules."""
    rtdata = rtdata_module
    rtdata.get_data("nirspec/fs/jw0010010_11010_nrs1_chimera_uncal.fits")

    Step.from_cmdline(["jwst.pipeline.Detector1Pipeline", rtdata.input,
                       "--save_calibrated_ramp=True",
                       "--steps.group_scale.save_results=True",
                       "--steps.dq_init.save_results=True",
                       "--steps.saturation.save_results=True",
                       "--steps.superbias.save_results=True",
                       "--steps.refpix.save_results=True",
                       "--steps.linearity.save_results=True",
                       "--steps.dark_current.save_results=True",
                       "--steps.jump.save_results=True",
                       "--steps.ramp_fit.save_results=True",
                       "--steps.gain_scale.save_results=True",
                       "--steps.jump.rejection_threshold=20.0"])

    return rtdata

@pytest.mark.bigdata
@pytest.mark.parametrize("output", [
    'jw0010010_11010_nrs1_chimera_ramp.fits',
    'jw0010010_11010_nrs1_chimera_dark_current.fits',
    'jw0010010_11010_nrs1_chimera_dq_init.fits',
    'jw0010010_11010_nrs1_chimera_gain_scale.fits',
    'jw0010010_11010_nrs1_chimera_group_scale.fits',
    'jw0010010_11010_nrs1_chimera_jump.fits',
    'jw0010010_11010_nrs1_chimera_linearity.fits',
    'jw0010010_11010_nrs1_chimera_refpix.fits',
    'jw0010010_11010_nrs1_chimera_saturation.fits',
    'jw0010010_11010_nrs1_chimera_superbias.fits',
    'jw0010010_11010_nrs1_chimera_0_ramp_fit.fits',],
                         ids=['ramp','dark_current','dq_init','gain_scale',
                              'group_scale','jump','linearity','refpix',
                              'saturation','superbias','0_ramp_fit'])
def test_nirspec_det1pipeline(run_pipeline, fitsdiff_default_kwargs, output):
    """
    Regression test of calwebb_Detector1 pipeline performed on NIRSpec data.
    """
    rtdata = run_pipeline
    rtdata.output = output
    rtdata.get_truth(os.path.join("truth/test_nirspec_irs2_detector1/", output))


    diff = FITSDiff(rtdata.output, rtdata.truth, **fitsdiff_default_kwargs)
    assert diff.identical, diff.report()
