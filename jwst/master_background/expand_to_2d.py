import logging

import numpy as np
from gwcs.wcstools import grid_from_bounding_box
from stdatamodels.jwst import datamodels
from stdatamodels.jwst.datamodels import dqflags

from jwst.assign_wcs import nirspec  # For NIRSpec IFU data
from jwst.datamodels import ModelContainer
from jwst.lib.wcs_utils import get_wavelengths

log = logging.getLogger(__name__)

WFSS_EXPTYPES = ["NIS_WFSS", "NRC_WFSS", "NRC_GRISM", "NRC_TSGRISM"]

__all__ = [
    "expand_to_2d",
    "bkg_for_container",
    "create_bkg",
    "bkg_for_multislit",
    "bkg_for_image",
    "bkg_for_ifu_image",
]


def expand_to_2d(input_data, m_bkg_spec, allow_mos=False):
    """
    Expand a 1-D background to 2-D.

    Parameters
    ----------
    input_data : `~jwst.datamodels.JwstDataModel`
        The input science data.
    m_bkg_spec : str or `~jwst.datamodels.JwstDataModel`
        Either the name of a file containing a 1-D background spectrum,
        or a data model containing such a spectrum.
    allow_mos : bool
        If True, NIRSpec MOS data is supported. If False,
        background is set to 0.0 for any slit marked as exposure
        type NRS_MSASPEC.  This parameter should be set to True only
        for the master_background_mos step in the spec2 pipeline;
        MOS data is not supported via the master_background step
        in the spec3 pipeline.

    Returns
    -------
    background : `~jwst.datamodels.JwstDataModel`
        A copy of `input_data` but with the data replaced by the background,
        "expanded" from 1-D to 2-D.
    """
    with datamodels.open(m_bkg_spec) as bkg:
        if hasattr(bkg, "spec"):  # MultiSpecModel
            if len(bkg.spec) > 1:
                log.warning("The input 1-D spectrum contains multiple spectra")
            spec_table = bkg.spec[0].spec_table
        else:  # CombinedSpecModel
            spec_table = bkg.spec_table
        tab_wavelength = spec_table["wavelength"].copy()
        tab_background = spec_table["surf_bright"]

    # We're going to use np.interp, so tab_wavelength must be strictly
    # increasing.
    if not np.all(np.diff(tab_wavelength) > 0):
        index = np.argsort(tab_wavelength)
        tab_wavelength = tab_wavelength[index].copy()
        tab_background = tab_background[index].copy()

    # Handle associations, or input ModelContainers
    if isinstance(input_data, ModelContainer):
        background = bkg_for_container(
            input_data, tab_wavelength, tab_background, allow_mos=allow_mos
        )

    else:
        background = create_bkg(input_data, tab_wavelength, tab_background, allow_mos=allow_mos)

    return background


def bkg_for_container(input_data, tab_wavelength, tab_background, allow_mos=False):
    """
    Create a 2-D background for a container object.

    Parameters
    ----------
    input_data : JWST association or `~jwst.datamodels.ModelContainer`
        The input science data.
    tab_wavelength : 1-D ndarray
        The wavelength column read from the 1-D background table.
    tab_background : 1-D ndarray
        The surf_bright column read from the 1-D background table.
    allow_mos : bool
        If True, NIRSpec MOS data is supported. If False,
        background is set to 0.0 for any slit marked as exposure
        type NRS_MSASPEC.  This parameter should be set to True only
        for the master_background_mos step in the spec2 pipeline;
        MOS data is not supported via the master_background step
        in the spec3 pipeline.

    Returns
    -------
    background : `~jwst.datamodels.ModelContainer`
        A copy of `input_data` but with the data replaced by the background,
        "expanded" from 1-D to 2-D.
    """
    background = ModelContainer()
    for input_model in input_data:
        temp = create_bkg(input_model, tab_wavelength, tab_background, allow_mos=allow_mos)
        background.append(temp)

    return background


def create_bkg(input_data, tab_wavelength, tab_background, allow_mos=False):
    """
    Create a 2-D background.

    Parameters
    ----------
    input_data : `~jwst.datamodels.JwstDataModel`
        The input science data.
    tab_wavelength : 1-D ndarray
        The wavelength column read from the 1-D background table.
    tab_background : 1-D ndarray
        The surf_bright column read from the 1-D background table.
    allow_mos : bool
        If True, NIRSpec MOS data is supported. If False,
        background is set to 0.0 for any slit marked as exposure
        type NRS_MSASPEC.  This parameter should be set to True only
        for the master_background_mos step in the spec2 pipeline;
        MOS data is not supported via the master_background step
        in the spec3 pipeline.

    Returns
    -------
    background : `~jwst.datamodels.JwstDataModel`
        A copy of `input_data` but with the data replaced by the background,
        "expanded" from 1-D to 2-D.
    """
    # Handle individual NIRSpec FS, NIRSpec MOS
    if isinstance(input_data, datamodels.MultiSlitModel):
        background = bkg_for_multislit(
            input_data, tab_wavelength, tab_background, allow_mos=allow_mos
        )

    # Handle MIRI LRS
    elif isinstance(input_data, datamodels.ImageModel):
        background = bkg_for_image(input_data, tab_wavelength, tab_background)

    # Handle MIRI MRS and NIRSpec IFU
    elif isinstance(input_data, datamodels.IFUImageModel):
        background = bkg_for_ifu_image(input_data, tab_wavelength, tab_background)

    else:
        # Shouldn't get here.
        raise TypeError(f"Input type {type(input_data)} is not supported.")

    return background


def bkg_for_multislit(input_data, tab_wavelength, tab_background, allow_mos=False):
    """
    Create a 2-D background for a MultiSlitModel.

    Parameters
    ----------
    input_data : `~jwst.datamodels.MultiSlitModel`
        The input science data.
    tab_wavelength : 1-D ndarray
        The wavelength column read from the 1-D background table.
    tab_background : 1-D ndarray
        The surf_bright column read from the 1-D background table.
    allow_mos : bool
        If True, NIRSpec MOS data is supported. If False,
        background is set to 0.0 for any slit marked as exposure
        type NRS_MSASPEC.  This parameter should be set to True only
        for the master_background_mos step in the spec2 pipeline;
        MOS data is not supported via the master_background step
        in the spec3 pipeline.

    Returns
    -------
    background : `~jwst.datamodels.MultiSlitModel`
        A copy of `input_data` but with the data replaced by the background,
        "expanded" from 1-D to 2-D.
    """
    from jwst.master_background.nirspec_utils import correct_nrs_fs_bkg

    background = input_data.copy()
    min_wave = np.amin(tab_wavelength)
    max_wave = np.amax(tab_wavelength)

    for k, slit in enumerate(input_data.slits):
        log.info(f"Expanding background for slit {slit.name}")

        wl_array = get_wavelengths(slit, input_data.meta.exposure.type)
        if wl_array is None:
            raise RuntimeError(f"Can't determine wavelengths for {type(slit)}")

        # Wherever the wavelength is NaN, the background surface brightness
        # should to be set to 0.  We replace NaN elements in wl_array with
        # -1, so that np.interp will detect that those values are out of range
        # (note the `left` argument to np.interp) and set the output to 0.
        wl_array[np.isnan(wl_array)] = -1.0

        # flag values outside of background wavelength table
        mask_limit = (wl_array > max_wave) | (wl_array < min_wave)
        wl_array[mask_limit] = -1

        # bkg_surf_bright will be a 2-D array, because wl_array is 2-D.
        bkg_surf_bright = np.interp(wl_array, tab_wavelength, tab_background, left=0.0, right=0.0)

        background.slits[k].data[:] = bkg_surf_bright.copy()
        background.slits[k].dq[mask_limit] = np.bitwise_or(
            background.slits[k].dq[mask_limit], dqflags.pixel["DO_NOT_USE"]
        )

        # Check exposure type for special handling
        try:
            exp_type = slit.meta.exposure.type
        except AttributeError:
            exp_type = None
        if exp_type is None:
            exp_type = input_data.meta.exposure.type

        # NIRSpec MOS should only have backgrounds assigned in spec2,
        # via the master_background_mos step.
        if exp_type == "NRS_MSASPEC" and not allow_mos:
            log.warning("Master background subtraction is not supported for NIRSpec MOS spectra.")
            log.warning("Setting the background to 0.0")
            background.slits[k].data[:] = 0.0
            background.slits[k].dq[:] = 0
            continue

        # NIRSpec fixed slits need corrections applied to the 2D background
        # if the slit contains a point source, in order to make the master bkg
        # match the calibrated science data in the slit.
        if exp_type == "NRS_FIXEDSLIT" and slit.source_type.upper() == "POINT":
            background.slits[k] = correct_nrs_fs_bkg(background.slits[k])

    return background


def bkg_for_image(input_data, tab_wavelength, tab_background):
    """
    Create a 2-D background for an ImageModel.

    Parameters
    ----------
    input_data : `~jwst.datamodels.ImageModel`
        The input science data.
    tab_wavelength : 1-D ndarray
        The wavelength column read from the 1-D background table.
    tab_background : 1-D ndarray
        The surf_bright column read from the 1-D background table.

    Returns
    -------
    background : `~jwst.datamodels.ImageModel`
        A copy of `input_data` but with the data replaced by the background,
        "expanded" from 1-D to 2-D.
    """
    background = input_data.copy()
    min_wave = np.amin(tab_wavelength)
    max_wave = np.amax(tab_wavelength)
    wl_array = get_wavelengths(input_data, input_data.meta.exposure.type)
    if wl_array is None:
        raise RuntimeError(f"Can't determine wavelengths for {type(input_data)}")

    wl_array[np.isnan(wl_array)] = -1.0
    # flag values outside of background wavelength table
    mask_limit = (wl_array > max_wave) | (wl_array < min_wave)
    wl_array[mask_limit] = -1
    # bkg_surf_bright will be a 2-D array, because wl_array is 2-D.
    bkg_surf_bright = np.interp(wl_array, tab_wavelength, tab_background, left=0.0, right=0.0)

    background.data[:] = bkg_surf_bright.copy()
    background.dq[mask_limit] = np.bitwise_or(
        background.dq[mask_limit], dqflags.pixel["DO_NOT_USE"]
    )

    return background


def bkg_for_ifu_image(input_data, tab_wavelength, tab_background):
    """
    Create a 2-D background for an IFUImageModel.

    Parameters
    ----------
    input_data : `~jwst.datamodels.IFUImageModel`
        The input science data.
    tab_wavelength : 1-D ndarray
        The wavelength column read from the 1-D background table.
    tab_background : 1-D ndarray
        The surf_bright column read from the 1-D background table.

    Returns
    -------
    background : `~jwst.datamodels.IFUImageModel`
        A copy of `input_data` but with the data replaced by the background,
        "expanded" from 1-D to 2-D. The dq flags are set to DO_NOT_USE
        for the pixels outside the region provided in the X1D background
        wavelength table.
    """
    from jwst.master_background.nirspec_utils import correct_nrs_ifu_bkg

    background = input_data.copy()
    background.data[:, :] = 0.0

    if input_data.meta.instrument.name.upper() == "NIRSPEC":
        list_of_wcs = nirspec.nrs_ifu_wcs(input_data)
        for ifu_wcs in list_of_wcs:
            x, y = grid_from_bounding_box(ifu_wcs.bounding_box)
            wl_array = ifu_wcs(x, y)[2]
            wl_array[np.isnan(wl_array)] = -1.0

            # Anywhere science pixels are beyond the wavelength range of the background, zero
            # background will be used.
            # TODO - add another DQ Flag something like NO_BACKGROUND when we have space in dqflags
            bkg_surf_bright = np.interp(
                wl_array, tab_wavelength, tab_background, left=0.0, right=0.0
            )
            background.data[y.astype(int), x.astype(int)] = bkg_surf_bright.copy()

        # If the science target is a point source, apply pathloss corrections
        # to the background to make it match the calibrated science data
        if input_data.meta.target.source_type == "POINT":
            background = correct_nrs_ifu_bkg(background)

    elif input_data.meta.instrument.name.upper() == "MIRI":
        shape = input_data.data.shape
        grid = np.indices(shape, dtype=np.float64)
        wl_array = input_data.meta.wcs(grid[1], grid[0])[2]
        # first remove the nans from wl_array and replace with -1
        mask = np.isnan(wl_array)
        wl_array[mask] = -1.0

        # Anywhere science pixels are beyond the wavelength range of the background, zero
        # background will be used.
        # TODO - add another DQ Flag something like NO_BACKGROUND when we have space in dqflags
        bkg_surf_bright = np.interp(wl_array, tab_wavelength, tab_background, left=0.0, right=0.0)
        background.data[:, :] = bkg_surf_bright.copy()

    else:
        raise TypeError(f"Exposure type {input_data.meta.exposure.type} is not supported.")

    return background
