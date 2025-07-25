"""Association Definitions: DMS Level2b product associations."""

import logging

from jwst.associations.lib.constraint import Constraint, SimpleConstraint
from jwst.associations.lib.dms_base import (
    Constraint_TSO,
    Constraint_WFSC,
    nissoss_calibrated_filter,
    nrccoron_valid_detector,
    nrsfss_valid_detector,
    nrsifu_valid_detector,
    nrslamp_valid_detector,
)
from jwst.associations.lib.process_list import ListCategory
from jwst.associations.lib.rules_level2_base import (
    ASN_SCHEMA,  # noqa: F401
    AsnMixin_Lv2Image,
    AsnMixin_Lv2Imprint,
    AsnMixin_Lv2Nod,
    AsnMixin_Lv2Special,
    AsnMixin_Lv2Spectral,
    AsnMixin_Lv2WFSS,
    Constraint_Background,
    Constraint_Base,
    Constraint_Image_Nonscience,
    Constraint_Image_Science,
    Constraint_Imprint,
    Constraint_Imprint_Special,
    Constraint_Mode,
    Constraint_Single_Science,
    Constraint_Special,
    Constraint_Spectral_Science,
    Constraint_Target,
    DMSAttrConstraint,
    DMSLevel2bBase,
    Utility,  # noqa: F401
)
from jwst.associations.registry import RegistryMarker

__all__ = [
    "Asn_Lv2CoronAsRate",
    "Asn_Lv2FGS",
    "Asn_Lv2Image",
    "Asn_Lv2ImageNonScience",
    "Asn_Lv2ImageSpecial",
    "Asn_Lv2ImageTSO",
    "Asn_Lv2MIRLRSFixedSlitNod",
    "Asn_Lv2NRSFSS",
    "Asn_Lv2NRSIFUNod",
    "Asn_Lv2NRSLAMPImage",
    "Asn_Lv2NRSLAMPSpectral",
    "Asn_Lv2NRSMSA",
    "Asn_Lv2Spec",
    "Asn_Lv2SpecImprint",
    "Asn_Lv2SpecSpecial",
    "Asn_Lv2SpecTSO",
    "Asn_Lv2WFSSNIS",
    "Asn_Lv2WFSSNRC",
    "Asn_Lv2WFSSParallel",
    "Asn_Lv2WFSC",
]

# Configure logging
logger = logging.getLogger(__name__)


# --------------------------------
# Start of the User-level rules
# --------------------------------
@RegistryMarker.rule
class Asn_Lv2CoronAsRate(AsnMixin_Lv2Image, DMSLevel2bBase):
    """
    Create normal rate products for some coronographic data.

    Characteristics;
        - Association type: ``image2``
        - Pipeline: ``calwebb_image2``
        - NIRCam Coronagraphic
        - Only subarray=Full exposures
        - Treat as non-timeseries, producing "rate" products
    """

    def __init__(self, *args, **kwargs):
        # Setup constraints
        self.constraints = Constraint(
            [
                Constraint_Base(),
                Constraint_Mode(),
                DMSAttrConstraint(
                    name="exp_type",
                    sources=["exp_type"],
                    value="nrc_coron",
                ),
                DMSAttrConstraint(
                    name="subarray",
                    sources=["subarray"],
                    value="full",
                ),
                SimpleConstraint(
                    value=True,
                    sources=nrccoron_valid_detector,
                ),
                Constraint(
                    [
                        Constraint_Background(),
                        Constraint_Single_Science(self.has_science, self.get_exposure_type),
                    ],
                    reduce=Constraint.any,
                ),
            ]
        )

        # Now check and continue initialization.
        super().__init__(*args, **kwargs)

    def is_item_coron(self, _item):
        """
        Override to always return false.

        The override will force `make_member` to create a "rate"
        product instead of a "rateints" product.

        Returns
        -------
        bool
            False.
        """
        return False


@RegistryMarker.rule
class Asn_Lv2Image(AsnMixin_Lv2Image, DMSLevel2bBase):
    """
    Level2b Non-TSO Science Image Association.

    Characteristics:
        - Association type: ``image2``
        - Pipeline: ``calwebb_image2``
        - Image-based science exposures
        - Single science exposure
        - Non-TSO
        - Non-coronagraphic
    """

    def __init__(self, *args, **kwargs):
        # Setup constraints
        self.constraints = Constraint(
            [
                Constraint_Base(),
                Constraint_Mode(),
                Constraint_Image_Science(),
                Constraint(
                    [
                        Constraint_TSO(),
                    ],
                    reduce=Constraint.notany,
                ),
                Constraint(
                    [
                        Constraint_Background(),
                        Constraint_Single_Science(self.has_science, self.get_exposure_type),
                    ],
                    reduce=Constraint.any,
                ),
            ]
        )

        # Now check and continue initialization.
        super(Asn_Lv2Image, self).__init__(*args, **kwargs)


@RegistryMarker.rule
class Asn_Lv2ImageNonScience(AsnMixin_Lv2Special, AsnMixin_Lv2Image, DMSLevel2bBase):
    """
    Level2b Non-science Image Association.

    Characteristics:
        - Association type: ``image2``
        - Pipeline: ``calwebb_image2``
        - Image-based non-science exposures, such as target acquisitions
        - Single science exposure
    """

    def __init__(self, *args, **kwargs):
        # Setup constraints
        self.constraints = Constraint(
            [
                Constraint_Base(),
                Constraint_Image_Nonscience(),
                Constraint_Single_Science(self.has_science, self.get_exposure_type),
            ]
        )

        # Now check and continue initialization.
        super(Asn_Lv2ImageNonScience, self).__init__(*args, **kwargs)


@RegistryMarker.rule
class Asn_Lv2ImageSpecial(AsnMixin_Lv2Special, AsnMixin_Lv2Image, DMSLevel2bBase):
    """
    Level2b Auxiliary Science Image Association.

    Characteristics:
        - Association type: ``image2``
        - Pipeline: ``calwebb_image2``
        - Image-based science exposures that are to be used as background or PSF exposures
        - Single science exposure
        - No other exposure can be part of the association
    """

    def __init__(self, *args, **kwargs):
        # Setup constraints
        self.constraints = Constraint(
            [
                Constraint_Base(),
                Constraint_Mode(),
                Constraint_Image_Science(),
                Constraint_Single_Science(self.has_science, self.get_exposure_type),
                Constraint_Special(),  # background and ref_psf exposures
            ]
        )

        # Now check and continue initialization.
        super(Asn_Lv2ImageSpecial, self).__init__(*args, **kwargs)


@RegistryMarker.rule
class Asn_Lv2ImageTSO(AsnMixin_Lv2Image, DMSLevel2bBase):
    """
    Level2b Time Series Science Image Association.

    Characteristics:
        - Association type: ``tso-image2``
        - Pipeline: ``calwebb_tso-image2``
        - Image-based Time Series exposures
        - Single science exposure
    """

    def __init__(self, *args, **kwargs):
        # Setup constraints
        self.constraints = Constraint(
            [
                Constraint_Base(),
                Constraint_Mode(),
                Constraint_Image_Science(),
                Constraint_Single_Science(self.has_science, self.get_exposure_type),
                Constraint_TSO(),
            ]
        )

        # Now check and continue initialization.
        super(Asn_Lv2ImageTSO, self).__init__(*args, **kwargs)

    def _init_hook(self, item):
        """Post-check and pre-add initialization."""
        super(Asn_Lv2ImageTSO, self)._init_hook(item)
        self.data["asn_type"] = "tso-image2"


@RegistryMarker.rule
class Asn_Lv2FGS(AsnMixin_Lv2Image, DMSLevel2bBase):
    """
    Level2b FGS Association.

    Characteristics:
        - Association type: ``image2``
        - Pipeline: ``calwebb_image2``
        - Image-based FGS science exposures
        - Single science exposure
    """

    def __init__(self, *args, **kwargs):
        # Setup constraints
        self.constraints = Constraint(
            [
                Constraint_Base(),
                Constraint_Single_Science(self.has_science, self.get_exposure_type),
                DMSAttrConstraint(
                    name="exp_type",
                    sources=["exp_type"],
                    value=("fgs_image|fgs_focus"),
                ),
                Constraint([Constraint_WFSC()], reduce=Constraint.notany),
            ]
        )

        super(Asn_Lv2FGS, self).__init__(*args, **kwargs)


@RegistryMarker.rule
class Asn_Lv2Spec(AsnMixin_Lv2Spectral, AsnMixin_Lv2Imprint, DMSLevel2bBase):
    """
    Level2b Science Spectral Association.

    Characteristics:
        - Association type: ``spec2``
        - Pipeline: ``calwebb_spec2``
        - Spectral-based single target science exposures
        - Single science exposure
        - Non-TSO
        - Not part of a background dither observation
    """

    def __init__(self, *args, **kwargs):
        # Setup constraints
        self.constraints = Constraint(
            [
                Constraint_Base(),
                Constraint_Mode(),
                Constraint_Spectral_Science(
                    exclude_exp_types=["nis_wfss", "nrc_wfss", "nrs_fixedslit", "nrs_msaspec"]
                ),
                Constraint(
                    [
                        #  Allow either any background, or ensure imprint and science members
                        #  match on mosaic tile number
                        Constraint_Background(),
                        Constraint(
                            [
                                Constraint(
                                    [
                                        Constraint_Imprint(),
                                        Constraint_Single_Science(
                                            self.has_science, self.get_exposure_type
                                        ),
                                    ],
                                    reduce=Constraint.any,
                                ),
                                DMSAttrConstraint(name="mostilno", sources=["mostilno"]),
                            ],
                            reduce=Constraint.all,
                        ),
                    ],
                    reduce=Constraint.any,
                ),
                Constraint(
                    [
                        Constraint_TSO(),
                        DMSAttrConstraint(
                            name="patttype",
                            sources=["patttype"],
                            value="2-point-nod|4-point-nod|along-slit-nod",
                        ),
                    ],
                    reduce=Constraint.notany,
                ),
                SimpleConstraint(
                    value=True,
                    test=lambda _value, item: nrsifu_valid_detector(item),
                    force_unique=False,
                ),
            ]
        )

        # Now check and continue initialization.
        super(Asn_Lv2Spec, self).__init__(*args, **kwargs)


@RegistryMarker.rule
class Asn_Lv2SpecImprint(AsnMixin_Lv2Special, AsnMixin_Lv2Spectral, DMSLevel2bBase):
    """
    Level2b Treat Imprint/Leakcal as science.

    Characteristics:
        - Association type: ``spec2``
        - Pipeline: ``calwebb_spec2``
        - Only handles Imprint/Leakcal exposures
        - Single science exposure
    """

    def __init__(self, *args, **kwargs):
        # Setup constraints
        self.constraints = Constraint(
            [
                Constraint_Base(),
                Constraint_Mode(),
                Constraint_Spectral_Science(),
                Constraint_Single_Science(self.has_science, self.get_exposure_type),
                SimpleConstraint(
                    value=True,
                    test=lambda _value, item: nrsifu_valid_detector(item),
                    force_unique=False,
                ),
                DMSAttrConstraint(name="imprint", sources=["is_imprt"]),
            ]
        )

        # Now check and continue initialization.
        super(Asn_Lv2SpecImprint, self).__init__(*args, **kwargs)


@RegistryMarker.rule
class Asn_Lv2SpecSpecial(
    AsnMixin_Lv2Special, AsnMixin_Lv2Spectral, AsnMixin_Lv2Imprint, DMSLevel2bBase
):
    """
    Level2b Auxiliary Science Spectral Association.

    Characteristics:
        - Association type: ``spec2``
        - Pipeline: ``calwebb_spec2``
        - Spectral-based single target science exposures that are background exposures
        - Single science exposure
    """

    def __init__(self, *args, **kwargs):
        # Setup constraints
        self.constraints = Constraint(
            [
                Constraint_Base(),
                Constraint_Mode(),
                Constraint_Spectral_Science(),
                Constraint_Special(),  # background and ref_psf exposures
                SimpleConstraint(
                    value=True,
                    test=lambda _value, item: nrsifu_valid_detector(item),
                    force_unique=False,
                ),
                Constraint(
                    [
                        Constraint_Imprint_Special(self),
                        Constraint_Single_Science(self.has_science, self.get_exposure_type),
                    ],
                    reduce=Constraint.any,
                ),
            ]
        )

        # Now check and continue initialization.
        super(Asn_Lv2SpecSpecial, self).__init__(*args, **kwargs)


@RegistryMarker.rule
class Asn_Lv2SpecTSO(AsnMixin_Lv2Spectral, DMSLevel2bBase):
    """
    Level2b Time Series Science Spectral Association.

    Characteristics:
        - Association type: ``tso-spec2``
        - Pipeline: ``calwebb_tso-spec2``
        - Spectral-based single target time series exposures
        - Single science exposure
        - No other exposure can be part of the association
    """

    def __init__(self, *args, **kwargs):
        # Setup constraints
        self.constraints = Constraint(
            [
                Constraint_Base(),
                Constraint_Mode(),
                Constraint_Spectral_Science(exclude_exp_types=["nrs_msaspec", "nrs_fixedslit"]),
                Constraint_Single_Science(self.has_science, self.get_exposure_type),
                Constraint_TSO(),
                Constraint(
                    [
                        Constraint(
                            [
                                DMSAttrConstraint(
                                    name="exp_type",
                                    sources=["exp_type"],
                                    value="nrc_tsgrism",
                                ),
                                DMSAttrConstraint(
                                    name="pupil",
                                    sources=["pupil"],
                                    value="clear|gdhs0|gdhs60",
                                ),
                            ],
                        )
                    ],
                    reduce=Constraint.notany,
                ),
                # Don't allow NIRSpec invalid optical paths in spec2
                Constraint(
                    [
                        Constraint(
                            [
                                DMSAttrConstraint(
                                    name="exp_type", sources=["exp_type"], value="nrs_brightobj"
                                ),
                                SimpleConstraint(
                                    value=False,
                                    test=lambda value, item: nrsfss_valid_detector(item) == value,
                                    force_unique=False,
                                ),
                            ]
                        ),
                    ],
                    reduce=Constraint.notany,
                ),
                # Don't allow NIRISS SOSS with uncalibrated filters
                Constraint(
                    [
                        Constraint(
                            [
                                DMSAttrConstraint(
                                    name="exp_type", sources=["exp_type"], value="nis_soss"
                                ),
                                SimpleConstraint(
                                    value=False,
                                    test=lambda value, item: nissoss_calibrated_filter(item)
                                    == value,
                                    force_unique=False,
                                ),
                            ]
                        ),
                    ],
                    reduce=Constraint.notany,
                ),
            ]
        )

        # Now check and continue initialization.
        super(Asn_Lv2SpecTSO, self).__init__(*args, **kwargs)

    def _init_hook(self, item):
        """Post-check and pre-add initialization."""
        super(Asn_Lv2SpecTSO, self)._init_hook(item)
        self.data["asn_type"] = "tso-spec2"


@RegistryMarker.rule
class Asn_Lv2MIRLRSFixedSlitNod(AsnMixin_Lv2Spectral, DMSLevel2bBase):
    """
    Level2b MIRI LRS Fixed Slit background nods Association.

    Characteristics:
        - Association type: ``spec2``
        - Pipeline: ``calwebb_spec2``
        - MIRI LRS Fixed slit
        - Single science exposure
        - Include slit nods as backgrounds
    """

    def __init__(self, *args, **kwargs):
        # Setup constraints
        self.constraints = Constraint(
            [
                Constraint_Base(),
                Constraint_Mode(),
                DMSAttrConstraint(name="exp_type", sources=["exp_type"], value="mir_lrs-fixedslit"),
                DMSAttrConstraint(
                    name="patttype",
                    sources=["patttype"],
                    value="along-slit-nod",
                ),
                SimpleConstraint(
                    value=True,
                    test=lambda _value, _item: self.acid.type != "background",
                    force_unique=False,
                ),
                Constraint(
                    [
                        Constraint(
                            [
                                DMSAttrConstraint(
                                    name="patt_num",
                                    sources=["patt_num"],
                                ),
                                Constraint_Single_Science(
                                    self.has_science,
                                    self.get_exposure_type,
                                    reprocess_on_match=True,
                                    work_over=ListCategory.EXISTING,
                                ),
                            ]
                        ),
                        Constraint(
                            [
                                DMSAttrConstraint(
                                    name="is_current_patt_num",
                                    sources=["patt_num"],
                                    value=lambda: "((?!{}).)*".format(
                                        self.constraints["patt_num"].value
                                    ),
                                ),
                                SimpleConstraint(
                                    name="force_match",
                                    value=None,
                                    sources=lambda _item: False,
                                    test=lambda _constraint, _obj: True,
                                    force_unique=True,
                                ),
                            ]
                        ),
                    ],
                    reduce=Constraint.any,
                ),
            ]
        )

        # Now check and continue initialization.
        super(Asn_Lv2MIRLRSFixedSlitNod, self).__init__(*args, **kwargs)

    def get_exposure_type(self, item, default="science"):
        """
        Modify exposure type depending on dither pointing index.

        Behaves as the superclass method. However, if the constraint
        `is_current_patt_num` is True, mark the exposure type as
        `background`.

        Parameters
        ----------
        item : member
            The item to pull exposure type from.
        default : str
            The default value if no exposure type is present, defaults to "science".

        Returns
        -------
        str
            The exposure type of the item.
        """
        exp_type = super(Asn_Lv2MIRLRSFixedSlitNod, self).get_exposure_type(item, default)
        if exp_type == "science" and self.constraints["is_current_patt_num"].matched:
            exp_type = "background"

        return exp_type


@RegistryMarker.rule
class Asn_Lv2NRSLAMPImage(AsnMixin_Lv2Image, AsnMixin_Lv2Special, DMSLevel2bBase):
    """
    Level2b NIRSpec image Lamp Calibrations Association.

    Characteristics:
        - Association type: ``image2``
        - Pipeline: ``calwebb_image2``
        - Image-based calibration exposures
        - Single science exposure
    """

    def __init__(self, *args, **kwargs):
        # Setup constraints
        self.constraints = Constraint(
            [
                Constraint_Base(),
                Constraint_Single_Science(self.has_science, self.get_exposure_type),
                DMSAttrConstraint(name="exp_type", sources=["exp_type"], value="nrs_lamp"),
                DMSAttrConstraint(sources=["grating"], value="mirror"),
                DMSAttrConstraint(sources=["opmode"], value="image", required=False),
            ]
        )

        super(Asn_Lv2NRSLAMPImage, self).__init__(*args, **kwargs)


@RegistryMarker.rule
class Asn_Lv2NRSLAMPSpectral(AsnMixin_Lv2Special, DMSLevel2bBase):
    """
    Level2b NIRSpec spectral Lamp Calibrations Association.

    Characteristics:
        - Association type: ``nrslamp-spec2``
        - Pipeline: ``calwebb_nrslamp-spec2``
        - Spectral-based calibration exposures
        - Single science exposure
    """

    def __init__(self, *args, **kwargs):
        self.constraints = Constraint(
            [
                Constraint_Base(),
                Constraint_Single_Science(self.has_science, self.get_exposure_type),
                DMSAttrConstraint(
                    name="exp_type",
                    sources=["exp_type"],
                    value="nrs_autoflat|nrs_autowave|nrs_lamp",
                ),
                DMSAttrConstraint(name="opt_elem", sources=["filter"], value="opaque"),
                SimpleConstraint(
                    value=True,
                    test=lambda _value, item: nrslamp_valid_detector(item),
                    force_unique=False,
                ),
                Constraint(
                    [
                        Constraint(
                            [
                                DMSAttrConstraint(
                                    name="opmode",
                                    sources=["opmode"],
                                    value="msaspec",
                                )
                            ],
                            reduce=Constraint.notany,
                        ),
                        Constraint(
                            [
                                DMSAttrConstraint(sources=["opmode"], value="msaspec"),
                                DMSAttrConstraint(sources=["msametfl"]),
                            ]
                        ),
                    ],
                    reduce=Constraint.any,
                ),
                DMSAttrConstraint(
                    name="lamp",
                    sources=["lamp"],
                ),
                Constraint(
                    [
                        DMSAttrConstraint(
                            sources=["grating"],
                            value="mirror",
                            force_unique=False,
                        ),
                        DMSAttrConstraint(
                            sources=["opmode"],
                            value="grating-only",
                            force_unique=False,
                        ),
                        DMSAttrConstraint(
                            sources=["lamp"],
                            value="nolamp",
                            force_unique=False,
                        ),
                    ],
                    reduce=Constraint.notany,
                ),
            ]
        )

        super(Asn_Lv2NRSLAMPSpectral, self).__init__(*args, **kwargs)

    def _init_hook(self, item):
        """Post-check and pre-add initialization."""
        super(Asn_Lv2NRSLAMPSpectral, self)._init_hook(item)
        self.data["asn_type"] = "nrslamp-spec2"


@RegistryMarker.rule
class Asn_Lv2WFSSNIS(
    AsnMixin_Lv2WFSS,
    AsnMixin_Lv2Spectral,
):
    """
    Level2b WFSS/GRISM Association.

    Characteristics:
        - Association type: ``spec2``
        - Pipeline: ``calwebb_spec2``
        - Multi-object science exposures
        - Single science exposure
        - Require a source catalog from processing of the corresponding direct imagery.
    """

    def __init__(self, *args, **kwargs):
        self.constraints = Constraint(
            [
                Constraint_Base(),
                Constraint_Target(),
                Constraint(
                    [
                        DMSAttrConstraint(
                            name="exp_type",
                            sources=["exp_type"],
                            value="nis_wfss",
                        ),
                        DMSAttrConstraint(
                            name="image_exp_type",
                            sources=["exp_type"],
                            value="nis_image",
                            force_reprocess=ListCategory.NONSCIENCE,
                            only_on_match=True,
                        ),
                    ],
                    reduce=Constraint.any,
                ),
                DMSAttrConstraint(
                    name="instrument",
                    sources=["instrume"],
                ),
                DMSAttrConstraint(
                    name="instrument",
                    sources=["instrume"],
                ),
                DMSAttrConstraint(
                    name="pupil",
                    sources=["pupil"],
                ),
                DMSAttrConstraint(
                    name="subarray",
                    sources=["subarray"],
                ),
                Constraint(
                    [
                        SimpleConstraint(
                            value="science",
                            test=lambda value, item: self.get_exposure_type(item) != value,
                            force_unique=False,
                        ),
                        Constraint_Single_Science(self.has_science, self.get_exposure_type),
                    ],
                    reduce=Constraint.any,
                ),
            ]
        )

        super(Asn_Lv2WFSSNIS, self).__init__(*args, **kwargs)


@RegistryMarker.rule
class Asn_Lv2WFSSNRC(
    AsnMixin_Lv2WFSS,
    AsnMixin_Lv2Spectral,
):
    """
    Level2b WFSS/GRISM Association.

    Characteristics:
        - Association type: ``spec2``
        - Pipeline: ``calwebb_spec2``
        - Multi-object science exposures
        - Single science exposure
        - Require a source catalog from processing of the corresponding direct imagery.
    """

    def __init__(self, *args, **kwargs):
        self.constraints = Constraint(
            [
                Constraint_Base(),
                Constraint_Target(),
                Constraint(
                    [
                        DMSAttrConstraint(
                            name="exp_type",
                            sources=["exp_type"],
                            value="nrc_wfss",
                        ),
                        DMSAttrConstraint(
                            name="image_exp_type",
                            sources=["exp_type"],
                            value="nrc_image",
                            force_reprocess=ListCategory.NONSCIENCE,
                            only_on_match=True,
                        ),
                    ],
                    reduce=Constraint.any,
                ),
                DMSAttrConstraint(
                    name="instrument",
                    sources=["instrume"],
                ),
                DMSAttrConstraint(
                    name="detector",
                    sources=["detector"],
                ),
                Constraint(
                    [
                        SimpleConstraint(
                            value="science",
                            test=lambda value, item: self.get_exposure_type(item) != value,
                            force_unique=False,
                        ),
                        Constraint_Single_Science(self.has_science, self.get_exposure_type),
                    ],
                    reduce=Constraint.any,
                ),
            ]
        )

        super(Asn_Lv2WFSSNRC, self).__init__(*args, **kwargs)


@RegistryMarker.rule
class Asn_Lv2NRSMSA(AsnMixin_Lv2Nod, AsnMixin_Lv2Spectral, DMSLevel2bBase):
    """
    Level2b NIRSpec MSA Association.

    Characteristics:
        - Association type: ``spec2``
        - Pipeline: ``calwebb_spec2``
        - Spectral-based NIRSpec MSA multi-object science exposures
        - Single science exposure
        - Handle slitlet nodding for background subtraction
    """

    def __init__(self, *args, **kwargs):
        # Setup constraints
        self.constraints = Constraint(
            [
                Constraint_Base(),
                Constraint_Mode(),
                Constraint(
                    [
                        DMSAttrConstraint(
                            name="exp_type", sources=["exp_type"], value="nrs_msaspec"
                        ),
                        DMSAttrConstraint(sources=["msametfl"]),
                        DMSAttrConstraint(
                            name="expspcin",
                            sources=["expspcin"],
                        ),
                    ]
                ),
            ]
        )

        # Now check and continue initialization.
        super(Asn_Lv2NRSMSA, self).__init__(*args, **kwargs)


@RegistryMarker.rule
class Asn_Lv2NRSFSS(AsnMixin_Lv2Nod, AsnMixin_Lv2Spectral, DMSLevel2bBase):
    """
    Level2b NIRSpec Fixed-slit Association.

    Notes
    -----
    Characteristics:
        - Association type: ``spec2``
        - Pipeline: ``calwebb_spec2``
        - Spectral-based NIRSpec fixed-slit single target science exposures
        - Single science exposure
        - Handle along-the-slit background nodding

    Association includes both the background and science exposures of the nodding.
    The identified science exposure is fixed by the nod, pattern, and exposure number
    to prevent other science exposures being included.
    """

    def __init__(self, *args, **kwargs):
        # Setup constraints
        self.constraints = Constraint(
            [
                Constraint_Base(),
                Constraint_Mode(),
                DMSAttrConstraint(name="exp_type", sources=["exp_type"], value="nrs_fixedslit"),
                SimpleConstraint(
                    value=True,
                    test=lambda _value, item: nrsfss_valid_detector(item),
                    force_unique=False,
                ),
                Constraint(
                    [
                        SimpleConstraint(
                            value="science",
                            test=lambda value, item: self.get_exposure_type(item) != value,
                            force_unique=False,
                        ),
                        Constraint(
                            [
                                DMSAttrConstraint(
                                    name="expspcin",
                                    sources=["expspcin"],
                                ),
                                DMSAttrConstraint(
                                    name="nods",
                                    sources=["numdthpt"],
                                ),
                                DMSAttrConstraint(
                                    name="subpxpts",
                                    sources=["subpxpns", "subpxpts"],
                                ),
                                SimpleConstraint(
                                    value="science",
                                    test=lambda value, item: self.get_exposure_type(item) == value,
                                    force_unique=False,
                                ),
                            ]
                        ),
                    ],
                    reduce=Constraint.any,
                ),
            ]
        )

        # Now check and continue initialization.
        super(Asn_Lv2NRSFSS, self).__init__(*args, **kwargs)


@RegistryMarker.rule
class Asn_Lv2NRSIFUNod(AsnMixin_Lv2Imprint, AsnMixin_Lv2Nod, AsnMixin_Lv2Spectral, DMSLevel2bBase):
    """
    Level2b NIRSpec IFU Association.

    Characteristics:
        - Association type: ``spec2``
        - Pipeline: ``calwebb_spec2``
        - Spectral-based NIRSpec IFU multi-object science exposures
        - Single science exposure
        - Handle 2 and 4 point background nodding
        - Include related imprint exposures
    """

    def __init__(self, *args, **kwargs):
        # Setup constraints
        self.constraints = Constraint(
            [
                Constraint_Base(),
                Constraint_Mode(),
                DMSAttrConstraint(name="exp_type", sources=["exp_type"], value="nrs_ifu"),
                SimpleConstraint(
                    value=True,
                    test=lambda _value, item: nrsifu_valid_detector(item),
                    force_unique=False,
                ),
                DMSAttrConstraint(
                    name="patttype",
                    sources=["patttype"],
                    value="2-point-nod|4-point-nod",
                    force_unique=True,
                ),
                DMSAttrConstraint(
                    name="mosaic_tile",
                    sources=["mostilno"],
                ),
            ]
        )

        # Now check and continue initialization.
        super(Asn_Lv2NRSIFUNod, self).__init__(*args, **kwargs)


@RegistryMarker.rule
class Asn_Lv2WFSC(DMSLevel2bBase):
    """
    Level2b Wavefront Sensing & Control Association.

    Characteristics:
        - Association type: ``wfs-image2``
        - Pipeline: ``calwebb_wfs-image2``
        - WFS and WFS&C observations
        - Single science exposure
    """

    def __init__(self, *args, **kwargs):
        # Setup constraints
        self.constraints = Constraint(
            [
                Constraint_Base(),
                Constraint_Image_Science(),
                Constraint_Single_Science(self.has_science, self.get_exposure_type),
                Constraint_WFSC(),
                Constraint(
                    [
                        DMSAttrConstraint(
                            name="dms_note",
                            sources=["dms_note"],
                            value="wfsc_los_jitter",
                        ),
                        DMSAttrConstraint(name="exp_type", sources=["exp_type"], value="nrc_image"),
                    ],
                    reduce=Constraint.notall,
                ),
            ]
        )

        # Now check and continue initialization.
        super(Asn_Lv2WFSC, self).__init__(*args, **kwargs)

    def _init_hook(self, item):
        """Post-check and pre-add initialization."""
        super(Asn_Lv2WFSC, self)._init_hook(item)
        self.data["asn_type"] = "wfs-image2"


@RegistryMarker.rule
class Asn_Lv2WFSSParallel(
    AsnMixin_Lv2WFSS,
    AsnMixin_Lv2Spectral,
):
    """
    Level 2b WFSS/GRISM associations for WFSS taken in pure-parallel mode.

    Characteristics:
        - Association type: ``spec2``
        - Pipeline: ``calwebb_spec2``
        - Multi-object science exposures
        - Single Science exposure
        - Require a source catalog from processing of the corresponding direct imagery.

    WFSS is executed differently when taken as part of a pure-parallel proposal than
    when WFSS is done as the primary. The differences are as follows. When primary,
    all components, the direct image and the two GRISM exposures, are executed
    within the same observation. When in parallel, each component is taken as a separate
    observation. These are always in associations of type DIRECT_IMAGE.

    Another difference is that there is no ``targetid`` assigned to the parallel
    exposures. However, since WFSS parallels are very specific, there is no need to
    constrain on target. A default value is used for the Level 3 product naming.
    """

    def __init__(self, *args, **kwargs):
        self.constraints = Constraint(
            [
                DMSAttrConstraint(
                    name="acdirect",
                    sources=["asn_candidate"],
                    value=r"\[\('c\d{4}', 'direct_image'\)\]",
                ),
                Constraint(
                    [
                        DMSAttrConstraint(
                            name="exp_type",
                            sources=["exp_type"],
                            value="nis_wfss|nrc_wfss",
                        ),
                        DMSAttrConstraint(
                            name="image_exp_type",
                            sources=["exp_type"],
                            value="nis_image|nrc_image",
                            force_reprocess=ListCategory.NONSCIENCE,
                            only_on_match=True,
                        ),
                    ],
                    reduce=Constraint.any,
                ),
                Constraint(
                    [
                        SimpleConstraint(
                            value="science",
                            test=lambda value, item: self.get_exposure_type(item) != value,
                            force_unique=False,
                        ),
                        Constraint_Single_Science(self.has_science, self.get_exposure_type),
                    ],
                    reduce=Constraint.any,
                ),
                Constraint_Target(),
                DMSAttrConstraint(
                    name="instrument",
                    sources=["instrume"],
                ),
            ]
        )

        super(Asn_Lv2WFSSParallel, self).__init__(*args, **kwargs)

    @staticmethod
    def find_closest_direct(_science, directs):
        """
        Find the direct image that is closest to the science.

        For NIRCam pure parallel observations, there should
        only be one long-wavelength direct image in a given
        direct_image candidate. Find it by searching for 'long'
        filenames. All [a|b]long filenames should belong to the
        same level 3 product, which will be associated to the
        grism image.

        For NIRISS, only one direct image optical path should
        be associated with a given grism image.

        Parameters
        ----------
        _science : dict
            The science member to compare against; unused.

        directs : [dict[,...]]
            The available direct members.

        Returns
        -------
        closest : dict
            The direct image that is the "closest"
        """
        long_directs = [d for d in directs if "long" in d["expname"]]
        if len(long_directs) == 0:
            long_directs.append(directs[0])  # If the search fails, just use the first.

        return long_directs[0]

    def validate_candidates(self, _member):
        """
        Stub to always return True.

        For this association, stub this to always return True

        Parameters
        ----------
        _member : member
            Member being added; ignored.

        Returns
        -------
        bool
            True.
        """
        return True
