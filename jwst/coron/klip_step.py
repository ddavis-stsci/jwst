#! /usr/bin/env python
from stdatamodels.jwst import datamodels

from jwst.coron import klip
from jwst.stpipe import Step

__all__ = ["KlipStep"]


class KlipStep(Step):
    """
    Performs KLIP processing on a science target coronagraphic exposure.

    The input science exposure is assumed to be a fully calibrated
    level-2b image. The processing is performed using a set of reference PSF
    images observed in the same coronagraphic mode.
    """

    class_alias = "klip"

    spec = """
        truncate = integer(default=50,min=0) # The number of KL transform rows to keep
    """  # noqa: E501

    def process(self, target, psfrefs):
        """
        Execute the KLIP calibration step.

        Parameters
        ----------
        target : str or CubeModel
            CubeModel or file containing science target exposure
        psfrefs : str or CubeModel
            CubeModel or file containing PSF Reference exposures

        Returns
        -------
        psf_sub : CubeModel
            Science target CubeModel with the PSF subtracted
        """
        with datamodels.open(target) as target_model:
            # Retrieve the parameter values
            truncate = self.truncate
            self.log.info("KL transform truncation = %d", truncate)

            # Get the PSF reference images
            refs_model = datamodels.open(psfrefs)

            # Call the KLIP routine
            psf_sub, psf_fit = klip.klip(target_model, refs_model, truncate)

        # Update the step completion status
        psf_sub.meta.cal_step.klip = "COMPLETE"

        # return psf_sub, psf_fit
        return psf_sub
