# Authors: Alexandre Gramfort <alexandre.gramfort@inria.fr>
#          Joan Massich <mailsik@gmail.com>
#
# License: BSD Style.

import os
from os import path as op

import numpy as np

from ...utils import _get_path
from ....utils import _fetch_file, verbose, _TempDir

BASE_URL = 'https://physionet.org/pn4/sleep-edfx/'
SLEEP_RECORDS = 'physionet_sleep_records.npy'


def update_sleep_records():
    # XXX: use requrie pandas
    import pandas as pd

    SLEEP_RECORDS = 'physionet_sleep_records.npy'
    npy_records = np.load(op.join(op.dirname(__file__), SLEEP_RECORDS))

    SLEEP_RECORDS = 'records.json'
    tmp = _TempDir()
    sha1sums_url = BASE_URL + "SHA1SUMS"
    sha1sums_fname = op.join(tmp, 'sha1sums')
    _fetch_file(sha1sums_url, sha1sums_fname)
    yy = pd.read_csv(sha1sums_fname, sep='  ', header=None,
                          names=['sha', 'fname'], engine='python')
    sha1_df = pd.read_csv(sha1sums_fname, sep='  ', header=None,
                          names=['sha', 'fname'], engine='python')
    select_age_records = sha1_df.fname.str.startswith('SC') & sha1_df.fname.str.endswith('edf')
    sha1_df = sha1_df[select_age_records]
    sha1_df['id']= [name[:6] for name in sha1_df.fname]

    subjects_url = BASE_URL + 'SC-subjects.xls'
    subjects_fname = op.join(tmp, 'SC-subjects.xls')
    _fetch_file(url=subjects_url, file_name=subjects_fname,
                hash_='0ba6650892c5d33a8e2b3f62ce1cc9f30438c54f',
                hash_type='sha1')

    xx = pd.read_excel(subjects_fname)
    xx = xx.rename(index=str, columns={'sex (F=1)': 'sex',
                                       'LightsOff': 'lights off'})
    xx['sex'] = (xx.sex.astype('category')
                       .cat.rename_categories({1:'female', 2:'male'}))
    xx['id'] = ['SC4{0:02d}{1:1d}'.format(s, n)
                for s, n in zip(xx.subject, xx.night)]

    data = xx.set_index('id').join(sha1_df.set_index('id')).dropna()
    data['record type'] = data.fname.str.split('-', expand=True)[1].str.split('.', expand=True)[0].astype('category')

    data.set_index(['subject', 'night', 'record type'])
    data.to_json(op.join(op.dirname(__file__), SLEEP_RECORDS),
                 orient='records', lines=True)
    # data.to_json()
    # sha1sums_fname = "SHA1SUMS"
    # sha1sums_fname = op.
    # "SHA1SUMS"
    # name =

    # _fetch_file

    # # now the numpy records files that contains info on dataset:
    # # It was obtained with:
    # base_url = "https://physionet.org/pn4/sleep-edfx/"
    # sha1sums_url = base_url + "SHA1SUMS"
    # sha1sums_fname = "SHA1SUMS"
    # _fetch_file(sha1sums_url, sha1sums_fname)
    # df = pd.read_csv(sha1sums_fname, sep='  ', header=None,
    #                  names=['sha', 'fname'], engine='python')
    # df[['subject', 'type']] = df.fname.str.split('-', expand=True)
    # df = df[df['type'].str.endswith('.edf') == True].copy()
    # df['type'] = df['type'].apply(lambda x: x.split(".")[0])
    # df['subject'] = df['subject'].str[:-1]
    # df.set_index(pd.factorize(df.subject)[0], inplace=True)


@verbose
def data_path(path=None, force_update=False, update_path=None, verbose=None):
    """Get path to local copy of EEG Physionet age Polysomnography dataset URL.

    This is a low-level function useful for getting a local copy of a
    remote Polysomnography dataset [1]_ which is available at PhysioNet [2]_.

    Parameters
    ----------
    path : None | str
        Location of where to look for the data storing location.
        If None, the environment variable or config parameter
        ``MNE_DATASETS_PHYSIONET_SLEEP_PATH`` is used. If it doesn't exist, the
        "~/mne_data" directory is used. If the dataset
        is not found under the given path, the data
        will be automatically downloaded to the specified folder.
    force_update : bool
        Force update of the dataset even if a local copy exists.
    update_path : bool | None
        If True, set the MNE_DATASETS_PHYSIONET_SLEEP_PATH in mne-python
        config to the given path. If None, the user is prompted.
    verbose : bool, str, int, or None
        If not None, override default verbose level (see :func:`mne.verbose`).

    Returns
    -------
    path : list of str
        Local path to the given data file. This path is contained inside a list
        of length one, for compatibility.

    References
    ----------
    .. [1] B Kemp, AH Zwinderman, B Tuk, HAC Kamphuisen, JJL Oberyé. Analysis of
           a sleep-dependent neuronal feedback loop: the slow-wave microcontinuity
           of the EEG. IEEE-BME 47(9):1185-1194 (2000).
    .. [2] Goldberger AL, Amaral LAN, Glass L, Hausdorff JM, Ivanov PCh,
           Mark RG, Mietus JE, Moody GB, Peng C-K, Stanley HE. (2000)
           PhysioBank, PhysioToolkit, and PhysioNet: Components of a New
           Research Resource for Complex Physiologic Signals.
           Circulation 101(23):e215-e220
    """  # noqa: E501
    key = 'PHYSIONET_SLEEP_PATH'
    name = 'PHYSIONET_SLEEP'
    path = _get_path(path, key, name)
    return op.join(path, 'physionet-sleep-data')


def _fetch_one(fname, hashsum, path, force_update):
    # Fetch the file
    url = BASE_URL + '/' + fname
    destination = op.join(path, fname)
    if not op.isfile(destination) or force_update:
        if op.isfile(destination):
            os.remove(destination)
        if not op.isdir(op.dirname(destination)):
            os.makedirs(op.dirname(destination))
        _fetch_file(url, destination, print_destination=False,
                    hash_=hashsum, hash_type='sha1')
    return destination


@verbose
def fetch_data(subjects, path=None, force_update=False, update_path=None,
               base_url=BASE_URL, verbose=None):  # noqa: D301
    """Get paths to local copies of PhysioNet Polysomnography dataset files.

    This will fetch data for the EEGBCI dataset [1]_, which is also
    available at PhysioNet [2]_.

    Parameters
    ----------
    subject : list of int
        The subjects to use. Can be in the range of 0-60 (inclusive).
    path : None | str
        Location of where to look for the EEGBCI data storing location.
        If None, the environment variable or config parameter
        ``MNE_DATASETS_PHYSIONET_SLEEP_PATH`` is used. If it doesn't exist, the
        "~/mne_data" directory is used. If the Polysomnography dataset
        is not found under the given path, the data
        will be automatically downloaded to the specified folder.
    force_update : bool
        Force update of the dataset even if a local copy exists.
    update_path : bool | None
        If True, set the MNE_DATASETS_EEGBCI_PATH in mne-python
        config to the given path. If None, the user is prompted.
    verbose : bool, str, int, or None
        If not None, override default verbose level (see :func:`mne.verbose`
        and :ref:`Logging documentation <tut_logging>` for more).

    Returns
    -------
    paths : list
        List of local data paths of the given type.

    Notes
    -----
    For example, one could do:

        >>> from mne.datasets import sleep_physionet
        >>> sleep_physionet.fetch_data(subjects=[0])  # doctest: +SKIP

    This would download data for subject 0 if it isn't there already.

    References
    ----------
    .. [1] B Kemp, AH Zwinderman, B Tuk, HAC Kamphuisen, JJL Oberyé. Analysis of
           a sleep-dependent neuronal feedback loop: the slow-wave microcontinuity
           of the EEG. IEEE-BME 47(9):1185-1194 (2000).
    .. [2] Goldberger AL, Amaral LAN, Glass L, Hausdorff JM, Ivanov PCh,
           Mark RG, Mietus JE, Moody GB, Peng C-K, Stanley HE. (2000)
           PhysioBank, PhysioToolkit, and PhysioNet: Components of a New
           Research Resource for Complex Physiologic Signals.
           Circulation 101(23):e215-e220
    """
    records = np.load(op.join(op.dirname(__file__), SLEEP_RECORDS))
    path = data_path(path=path, update_path=update_path)
    params = [path, force_update]

    fnames = []
    for subject in subjects:
        assert 0 <= subject <= 60
        idx_psg, idx_hyp = np.where(records['index'] == subject)[0]
        psg_fname, sha_psg = records['fname'][idx_psg], records['sha'][idx_psg]
        hyp_fname, sha_hyp = records['fname'][idx_hyp], records['sha'][idx_hyp]

        psg_fname = _fetch_one(psg_fname, sha_psg, *params)
        hyp_fname = _fetch_one(hyp_fname, sha_hyp, *params)
        fnames.append([psg_fname, hyp_fname])

    return fnames
