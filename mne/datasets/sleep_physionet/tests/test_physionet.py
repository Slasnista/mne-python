# Authors: Alexandre Gramfort <alexandre.gramfort@inria.fr>
#          Joan Massich <mailsik@gmail.com>
#
# License: BSD Style.

import os.path as op

import numpy as np
from numpy.testing import assert_array_equal

import pytest

from mne.utils import run_tests_if_main, requires_good_network
from mne.utils import requires_pandas, requires_version
from mne.datasets.sleep_physionet import age, temazepam
from mne.datasets.sleep_physionet._utils import _update_sleep_temazepam_records
from mne.datasets.sleep_physionet._utils import _update_sleep_age_records
from mne.datasets.sleep_physionet._utils import AGE_SLEEP_RECORDS
from mne.datasets.sleep_physionet._utils import TEMAZEPAM_SLEEP_RECORDS
from mne.datasets.sleep_physionet._utils import BASE_URL


@pytest.fixture(scope='session')
def physionet_tmpdir(tmpdir_factory):
    return str(tmpdir_factory.mktemp('physionet_files'))


def _fake_fetch_file(url, path, print_destination, hash_, hash_type):
    print(path, hash_)
    pass


def _keep_basename_only(path_structure):
    return np.vectorize(op.basename)(np.array(path_structure))


@requires_good_network
@requires_pandas
@requires_version('xlrd', '0.9')
@pytest.mark.slowtest
def test_run_update_age_records(tmpdir):
    """Test Sleep Physionet URL handling."""
    import pandas as pd
    fname = op.join(str(tmpdir), "records.csv")
    _update_sleep_age_records(fname)
    data = pd.read_csv(fname)
    pd.testing.assert_frame_equal(data, pd.read_csv(AGE_SLEEP_RECORDS))


@requires_good_network
def test_sleep_physionet_age(physionet_tmpdir, mocker):
    """Test Sleep Physionet URL handling."""
    my_func = mocker.patch('mne.datasets.sleep_physionet._utils._fetch_file',
                           side_effect=_fake_fetch_file)

    params = {'path': physionet_tmpdir, 'update_path': False}

    with pytest.raises(ValueError, match='Only subjects 0 to 19 are'):
        paths = age.fetch_data(subjects=[20], recording=[1], **params)

    paths = age.fetch_data(subjects=[0], recording=[1], **params)
    assert_array_equal(_keep_basename_only(paths),
                       [['SC4001E0-PSG.edf', 'SC4001EC-Hypnogram.edf']])

    paths = age.fetch_data(subjects=[0, 1], recording=[1], **params)
    assert_array_equal(_keep_basename_only(paths),
                       [['SC4001E0-PSG.edf', 'SC4001EC-Hypnogram.edf'],
                        ['SC4011E0-PSG.edf', 'SC4011EH-Hypnogram.edf']])

    paths = age.fetch_data(subjects=[0], recording=[1, 2], **params)
    assert_array_equal(_keep_basename_only(paths),
                       [['SC4001E0-PSG.edf', 'SC4001EC-Hypnogram.edf'],
                        ['SC4002E0-PSG.edf', 'SC4002EC-Hypnogram.edf']])

    assert my_func.call_count == 10
    EXPECTED_FILE_HASHES = {
        # 'SC4001E0-PSG.edf': 'adabd3b01fc7bb75c523a974f38ee3ae4e57b40f',
        # 'SC4001EC-Hypnogram.edf': '21c998eadc8b1e3ea6727d3585186b8f76e7e70b',
        # 'SC4001E0-PSG.edf': 'adabd3b01fc7bb75c523a974f38ee3ae4e57b40f',
        # 'SC4001EC-Hypnogram.edf': '21c998eadc8b1e3ea6727d3585186b8f76e7e70b',
        # 'SC4011E0-PSG.edf': '4d17451f7847355bcab17584de05e7e1df58c660',
        # 'SC4011EH-Hypnogram.edf': 'd582a3cbe2db481a362af890bc5a2f5ca7c878dc',
        # 'SC4001E0-PSG.edf': 'adabd3b01fc7bb75c523a974f38ee3ae4e57b40f',
        # 'SC4001EC-Hypnogram.edf': '21c998eadc8b1e3ea6727d3585186b8f76e7e70b',
        # 'SC4002E0-PSG.edf': 'c6b6d7a8605cc7e7602b6028ee77f6fbf5f7581d',
        'SC4002EC-Hypnogram.edf': '386230188a3552b1fc90bba0fb7476ceaca174b6'
    }
    for name, file_hash in EXPECTED_FILE_HASHES.items():
        base = age.data_path(path=physionet_tmpdir)
        my_func.assert_called_with(_get_expected_url(name),
                                   _get_expected_path(base, name),
                                   hash_=file_hash,
                                   hash_type='sha1',
                                   print_destination=False)


@requires_good_network
@requires_pandas
@requires_version('xlrd', '0.9')
@pytest.mark.slowtest
def test_run_update_temazepam_records(tmpdir):
    """Test Sleep Physionet URL handling."""
    import pandas as pd
    fname = op.join(str(tmpdir), "records.csv")
    _update_sleep_temazepam_records(fname)
    data = pd.read_csv(fname)
    pd.testing.assert_frame_equal(data, pd.read_csv(TEMAZEPAM_SLEEP_RECORDS))


def _get_expected_url(name):
    return BASE_URL + '/' + name


def _get_expected_path(base, name):
    return op.join(base, name)


@requires_good_network
def test_sleep_physionet_temazepam(physionet_tmpdir, mocker):
    """Test Sleep Physionet URL handling."""
    my_func = mocker.patch('mne.datasets.sleep_physionet._utils._fetch_file',
                           side_effect=_fake_fetch_file)

    params = {'path': physionet_tmpdir, 'update_path': False}

    paths = temazepam.fetch_data(subjects=[0], **params)
    assert_array_equal(_keep_basename_only(paths),
                       [['ST7011J0-PSG.edf', 'ST7011JP-Hypnogram.edf']])

    assert my_func.call_count == 2
    EXPECTED_FILE_HASHES = {
        # 'ST7011J0-PSG.edf': 'b9d11484126ebff1884034396d6a20c62c0ef48d',
        'ST7011JP-Hypnogram.edf': 'ff28e5e01296cefed49ae0c27cfb3ebc42e710bf'}
    for name, file_hash in EXPECTED_FILE_HASHES.items():
        base = temazepam.data_path(path=physionet_tmpdir)
        my_func.assert_called_with(_get_expected_url(name),
                                   _get_expected_path(base, name),
                                   hash_=file_hash,
                                   hash_type='sha1',
                                   print_destination=False)

    with pytest.raises(ValueError, match='Only subjects 0 to 21 are'):
        paths = temazepam.fetch_data(subjects=[22], **params)


run_tests_if_main()
