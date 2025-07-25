Description
===========

:Class: `jwst.skymatch.SkymatchStep`
:Alias: skymatch

Overview
--------
The ``skymatch`` step can be used to compute sky values in a collection of
input images that contain both sky and source signal. The sky values can be
computed for each image separately or in a way that matches the sky levels
amongst the collection of images so as to minimize their differences.
This operation is typically applied before doing cosmic-ray rejection and
combining multiple images into a mosaic.
When running the ``skymatch`` step in a matching mode,
it compares *total* signal levels in *the overlap regions* of a set of input
images and computes the signal offsets either for each image *or a set/group of
images* (see Image Groups section below) that will
minimize -- in a least squares sense -- the residuals across
the entire set. This comparison is performed directly on the input images
without resampling them onto a common grid. The overlap regions are computed
directly on the sky (celestial sphere) for each pair of input images.
Matching based on total signal level is especially useful for images that
are dominated by large, diffuse sources, where it is
difficult -- if not impossible -- to find and measure true sky.

Note that the meaning of "sky background" depends on the chosen sky computation
method. When the matching method is used, for example, the reported "sky" value
is only the offset in levels between images and does not necessarily include
the true total sky level.

.. note::
   Throughout this document the term "sky" is used in a generic sense,
   referring to any kind of non-source background signal, which may include
   actual sky, as well as instrumental (e.g. thermal) background, etc.

The step records information in three keywords that are included in the output
files:

BKGMETH
  records the sky method that was used to compute sky levels

BKGLEVEL
  the sky level computed for each image

BKGSUB
  a boolean indicating whether or not the sky was subtracted from the
  output images. Note that by default the step argument "subtract" is set to
  ``False``, which means that the sky will *NOT* be subtracted
  (see the :ref:`skymatch step arguments <skymatch_arguments>` for more
  details).

Both the "BKGSUB" and "BKGLEVEL" keyword values are important information for
downstream tasks, such as
:ref:`outlier detection <outlier_detection_step>` and
:ref:`resampling <resample_step>`.
Outlier detection will use the BKGLEVEL values to internally equalize the
images, which is necessary to prevent false detections due to overall
differences in signal levels between images, and the resample step will
subtract the BKGLEVEL values from each input image when combining them into
a mosaic.

Sky background
--------------
For a detailed discussion of JWST background components, please see
`Rigby et al. "How Dark the Sky: The JWST Backgrounds", 2023
<https://doi.org/10.48550/arXiv.2211.09890>`_ and
`"JWST Background Model" section in the JWST User Documentation
<https://jwst-docs.stsci.edu/jwst-general-support/jwst-background-model>`_
Here we just note that some components (e.g., in-field zodiacal light)
result in reproducible background structures in all detectors when they are
exposed simultaneously, while other components (e.g. stray light, thermal
emission) can produce varying background from one exposure to the next
exposure. The type of background structure that dominates a particular dataset
affects the optimal way to group images in the skymatch step.

Image Groups
------------
When computing and matching sky background on a set of input images, a *single
sky level* (or offset, depending on selected ``skymethod``) can be computed
either for each input image or for groups of two or more input images.

When background is dominated by zodiacal light, images taken at the same time
(e.g., NIRCam images from all short-wave detectors) can be sky matched
together; that is, a single background
level can be computed and applied to all these images because we can assume
that for the next exposure we will get a similar background structure, albeit
with an offset level (common to all images in an exposure). Using grouped
images with a common background level offers several advantages:
more data are used to compute the single sky level, and the
background level of images that do not overlap individually
with any other images in other exposures can still be adjusted (as long as they
belong to a group). This is the default operating mode for the ``skymatch``
step.

Identification of images that belong to the same "exposure" and therefore
can be grouped together is based on several attributes described in
`jwst.datamodels.ModelContainer`. This grouping is performed automatically
in the ``skymatch`` step using the
`jwst.datamodels.ModelContainer.models_grouped` property or
:py:meth:`jwst.datamodels.ModelLibrary.group_indices`.

However, when background across different detectors in a single "exposure"
(or "group") is dominated by unpredictable background components, we no longer
can use a single background level for all images in a group. In this case,
it may be desirable to match image backgrounds independently. This can be
achieved either by setting the ``image_model.meta.group_id`` attribute to a
unique string or integer value for each image, or by adding the ``group_id``
attribute to the ``members`` of the input ASN table - see
`~jwst.datamodels.ModelContainer` for more details.

.. note::
    Group ID (``group_id``) is used by both ``tweakreg`` and ``skymatch`` steps
    and so modifying it for one step will affect the results in another step.
    If it is desirable to apply different grouping strategies to the
    ``tweakreg`` and ``skymatch`` steps, one may need to run each step
    individually and provide a different ASN as input to each step.

Assumptions
-----------
When matching sky background, the code needs to compute bounding polygon
intersections in world coordinates. The input images, therefore, need to have
a valid WCS, generated by the :ref:`assign_wcs <assign_wcs_step>` step.

Algorithms
----------
The ``skymatch`` step provides several methods for constant sky background
value computations.

The first method, called "local", essentially is an enhanced version of the
original sky subtraction method used in older versions of
:ref:`astrodrizzle <drizzle:astrodrizzle_>`.
This method simply computes the mean/median/mode/etc. value of the sky
separately in each input image. This method was upgraded to be able to use DQ
flags to remove bad pixels from being used in the computations of sky
statistics.

In addition to the classic "local" method, two other methods have been
introduced: "global" and "match", as well as a combination of the
two -- "global+match".

#. The "global" method essentially uses the "local" method to first compute a
   sky value for each image separately, and then assigns the minimum of those
   results to all images in the collection. Hence after subtraction of the
   sky values only one image will have a net sky of zero, while the remaining
   images will have some small positive residual.

#. The "match" algorithm computes only a correction value for each image, such
   that, when applied to each image, the mismatch between *all* pairs of images
   is minimized, in the least-squares sense. For each pair of images, the sky
   mismatch is computed *only* in the regions in which the two images overlap
   on the sky.

   This makes the "match" algorithm particularly useful
   for equalizing sky values in large mosaics in which one may have
   only pair-wise intersection of adjacent images without having
   a common intersection region (on the sky) in all images.

   Note that if the argument "match_down=True", matching will be done to the
   image with the lowest sky value, and if "match_down=False" it will be done
   to the image with the highest value
   (see :ref:`skymatch step arguments <skymatch_arguments>` for full details).

#. The "global+match" algorithm combines the "global" and "match" methods.
   It uses the "global" algorithm to find a baseline sky value common to all
   input images and the "match" algorithm to equalize sky values among images.
   The direction of matching (to the lowest or highest) is again controlled by
   the "match_down" argument.

In the "local" and "global" methods, which find sky levels in each image,
the calculation of the image statistics takes advantage of sigma clipping
to remove contributions from isolated sources. This can work well for
accurately determining the true sky level in images that contain semi-large
regions of empty sky. The "match" algorithm, on the other hand, compares the
*total* signal levels integrated over regions of overlap in each image pair.
This method can produce better results when there are no large empty regions
of sky in the images. This method cannot measure the true sky level, but
instead provides additive corrections that can be used to equalize the signal
between overlapping images.

User-Supplied Sky Values
-------------------------
The ``skymatch`` step can also accept user-supplied sky values for each image.
This is useful when sky values have been determined based on a custom workflow
outside the pipeline. To use this feature, the user must provide a list of sky
values matching the number of images (``skylist`` parameter) and set the
``skymethod`` parameter to "user". The ``skylist`` must be a two-column
whitespace-delimited file with the first column containing the image filenames
and the second column containing the sky values. There must be exactly one line
per image in the input list.

Examples
--------
To get a better idea of the behavior of these different methods, the tables
below show the results for two hypothetical sets of images. The first example
is for a set of 6 images that form a 2x3 mosaic, with every image having
overlap with its immediate neighbors. The first column of the table gives the
actual (fake) sky signal that was imposed in each image, and the subsequent
columns show the results computed by each method (i.e. the values of the
resulting BKGLEVEL keywords).
All results are for the case where the step argument ``match_down = True``,
which means matching is done to the image with the lowest sky value.
Note that these examples are for the highly simplistic case where each example
image contains nothing but the constant sky value. Hence the sky computations
are not affected at all by any source content and are therefore able to
determine the sky values exactly in each image. Results for real images will
of course not be so exact.

+-------+-------+--------+-------+--------------+
| Sky   | Local | Global | Match | Global+Match |
+=======+=======+========+=======+==============+
| 100   |  100  |  100   |    0  |        100   |
+-------+-------+--------+-------+--------------+
| 120   |  120  |  100   |   20  |        120   |
+-------+-------+--------+-------+--------------+
| 105   |  105  |  100   |    5  |        105   |
+-------+-------+--------+-------+--------------+
| 110   |  110  |  100   |   10  |        110   |
+-------+-------+--------+-------+--------------+
| 105   |  105  |  100   |    5  |        105   |
+-------+-------+--------+-------+--------------+
| 115   |  115  |  100   |   15  |        115   |
+-------+-------+--------+-------+--------------+

local
  finds the sky level of each image independently of the rest.
global
  uses the minimum sky level found by "local" and applies it to all images.
match
  with "match_down=True" finds the offset needed to match all images
  to the level of the image with the lowest sky level.
global+match
  with "match_down=True" finds the offsets and global value
  needed to set all images to a sky level of zero. In this trivial example,
  the results are identical to the "local" method.

The second example is for a set of 7 images, where the first 4 form a 2x2
mosaic, with overlaps, and the second set of 3 images forms another mosaic,
with internal overlap, but the 2 mosaics do *NOT* overlap one another.

+-------+-------+--------+-------+--------------+
| Sky   | Local | Global | Match | Global+Match |
+=======+=======+========+=======+==============+
| 100   |  100  |   90   |     0 |    86.25     |
+-------+-------+--------+-------+--------------+
| 120   |  120  |   90   |    20 |   106.25     |
+-------+-------+--------+-------+--------------+
| 105   |  105  |   90   |     5 |    91.25     |
+-------+-------+--------+-------+--------------+
| 110   |  110  |   90   |    10 |    96.25     |
+-------+-------+--------+-------+--------------+
|  95   |   95  |   90   |  8.75 |     95       |
+-------+-------+--------+-------+--------------+
|  90   |   90  |   90   |  3.75 |     90       |
+-------+-------+--------+-------+--------------+
| 100   |  100  |   90   | 13.75 |    100       |
+-------+-------+--------+-------+--------------+

In this case, the "local" method again computes the sky in each image
independently of the rest, and the "global" method sets the result for
each image to the minimum value returned by "local". The matching results,
however, require some explanation. With "match" only, all of the results
give the proper offsets required to equalize the images contained within
each mosaic, but the algorithm does not have the information needed to
match the two (non-overlapping) mosaics to one another. Similarly, the
"global+match" results again provide proper matching within each mosaic,
but will leave an overall residual in one of the mosaics.

Limitations and Discussions
---------------------------
As aluded to above, the best sky computation method depends on the nature
of the data in the input images. If the input images contain mostly
compact, isolated sources, the "local" and "global" algorithms can do a
good job at finding the true sky level in each image. If the images contain
large, diffuse sources, the "match" algorithm is more appropriate, assuming
of course there is sufficient overlap between images from which to compute
the matching values. In the event there is not overlap between all of the
images, as illustrated in the second example above, the "match" method can
still provide useful results for matching the levels within each
non-contigous region covered by the images, but will not provide a good
overall sky level across all of the images. In these situations it is more
appropriate to either process the non-contiguous groups independently of
one another or use the "local" or "global" methods to compute the sky
separately in each image. The latter option will of course only work well
if the images are not domimated by extended, diffuse sources.

The primary reason for introducing the ``skymatch`` algorithm was to try to
equalize the sky in large mosaics in which computation of the
absolute sky is difficult, due to the presence of large diffuse
sources in the image. As discussed above, the ``skymatch`` step
accomplishes this by comparing the sky values in the
overlap regions of each image pair. The quality of sky matching will
obviously depend on how well these sky values can be estimated.
True background may not be present at all in some images, in which case
the computed "sky" may be the surface brightness of a large galaxy, nebula,
etc.

Here is a brief list of possible limitations and factors that can affect
the outcome of the matching (sky subtraction in general) algorithm:

#. Because sky computation is performed on *flat-fielded* but
   *not distortion corrected* images, it is important to keep in mind
   that flat-fielding is performed to obtain correct surface brightnesses.
   Because the surface brightness of a pixel containing a point-like source
   will change inversely with a change to the pixel area, it is advisable to
   mask point-like sources through user-supplied mask files. Values
   different from zero in user-supplied masks indicate good data pixels.
   Alternatively, one can use the ``upper`` parameter to exclude the use of
   pixels containing bright objects when performing the sky computations.

#. The input images may contain cosmic rays. This
   algorithm does not perform CR cleaning. A possible way of minimizing
   the effect of the cosmic rays on sky computations is to use
   clipping (\ ``nclip`` > 0) and/or set the ``upper`` parameter to a value
   larger than most of the sky background (or extended sources) but
   lower than the values of most CR-affected pixels.

#. In general, clipping is a good way of eliminating bad pixels:
   pixels affected by CR, hot/dead pixels, etc. However, for
   images with complicated backgrounds (extended galaxies, nebulae,
   etc.), affected by CR and noise, the clipping process may mask different
   pixels in different images. If variations in the background are
   too strong, clipping may converge to different sky values in
   different images even when factoring in the true difference
   in the sky background between the two images.

#. In general images can have different true background values
   (we could measure it if images were not affected by large diffuse
   sources). However, arguments such as ``lower`` and ``upper`` will
   apply to all images regardless of the intrinsic differences
   in sky levels (see :ref:`skymatch step arguments <skymatch_arguments>`).
