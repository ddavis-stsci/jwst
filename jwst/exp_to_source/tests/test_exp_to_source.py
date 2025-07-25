import numpy as np
import pytest
from stdatamodels.jwst.datamodels import MultiExposureModel, MultiSlitModel

from jwst.datamodels import ModelContainer
from jwst.exp_to_source import exp_to_source, multislit_to_container
from jwst.exp_to_source.tests import helpers


@pytest.fixture(scope="module")
def run_exp_to_source():
    inputs = [MultiSlitModel(f) for f in helpers.INPUT_FILES]
    outputs = exp_to_source(inputs)
    yield inputs, outputs
    for model in inputs:
        model.close()


def test_model_structure(run_exp_to_source):
    inputs, outputs = run_exp_to_source
    assert len(outputs) == 5
    assert len(outputs[next(iter(outputs))].exposures) == 3
    for in_idx, in_model in enumerate(inputs):
        for slit in in_model.slits:
            exposure = outputs[str(slit.source_id)].exposures[in_idx]
            assert (exposure.data == slit.data).all()
            assert len(exposure.meta._instance) >= len(in_model.meta._instance)
            assert exposure.meta.filename == in_model.meta.filename
            assert outputs[str(slit.source_id)].meta.filename != in_model.meta.filename


def test_model_roundtrip(tmp_path, run_exp_to_source):
    inputs, outputs = run_exp_to_source
    files = []
    for output in outputs:
        file_path = tmp_path / (output + ".fits")
        outputs[output].save(file_path)
        files.append(file_path)
    for file_path in files:
        with MultiExposureModel(file_path) as multiexposure_model:
            assert len(multiexposure_model.exposures) == 3
            exp_files = set()
            for exposure in multiexposure_model.exposures:
                exp_files.add(exposure.meta.filename)
            assert len(exp_files) == len(multiexposure_model.exposures)
            assert multiexposure_model.meta.filename not in exp_files


def test_container_structure():
    """Test for container usage."""

    # Setup input
    inputs = [MultiSlitModel(f) for f in helpers.INPUT_FILES]
    container = ModelContainer(inputs)

    # Make the source-based containers
    outputs = multislit_to_container(container)

    # See what we got.
    assert len(container) == 3
    assert len(outputs) == 5
    for i, model in enumerate(container):
        for slit in model.slits:
            exposure = outputs[str(slit.source_id)][i]
            assert (exposure.data == slit.data).all()
            assert np.array_equal(exposure.data, slit.data)
            assert exposure.meta.filename == model.meta.filename
            assert exposure.meta.wcs.pipeline == slit.meta.wcs.pipeline

    # Closeout
    container.close()
    for model in inputs:
        model.close()
    for model in outputs.values():
        model.close()


def test_slit_exptype():
    """Test for slit exposure type handling."""

    # Setup input
    inputs = [MultiSlitModel(f) for f in helpers.INPUT_FILES]
    container = ModelContainer(inputs)

    # Add a slit exposure type to each input
    for model in container:
        for slit in model.slits:
            if slit.source_id == 1:
                slit.meta.exposure = {"type": "NRS_MSASPEC"}
            else:
                slit.meta.exposure = {"type": "NRS_FIXEDSLIT"}

    # Make the source-based containers
    outputs = multislit_to_container(container)

    # Check that exposure type was passed from input to output
    assert len(container) == 3
    assert len(outputs) == 5
    for i, model in enumerate(container):
        for slit in model.slits:
            exposure = outputs[str(slit.source_id)][i]
            assert exposure.meta.exposure.type == slit.meta.exposure.type
            if slit.source_id == 1:
                assert exposure.meta.exposure.type == "NRS_MSASPEC"
            else:
                assert exposure.meta.exposure.type == "NRS_FIXEDSLIT"

    # Closeout
    container.close()
    for model in inputs:
        model.close()
    for model in outputs.values():
        model.close()
