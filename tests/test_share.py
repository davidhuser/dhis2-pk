import pytest

from pk.core.exceptions import ClientException
from pk.core.static import newest_dhis, valid_uid
from pk.core.dhis import Dhis
from pk.share import Permission, ObjectSharing, UserGroupAccess, skip, set_delimiter


@pytest.fixture()
def sharingdefinitions():
    # no userGroup sharing
    uid = 'dataElement1'
    object_type = 'dataElements'
    public_access = 'rw------'
    sd0 = ObjectSharing(uid, object_type, public_access)

    # usergroup sharing
    uid = 'dataElement1'
    object_type = 'dataElements'
    public_access = 'rw------'
    usergroup_access = {UserGroupAccess(uid='userGroup111', access='rw------')}
    sd1 = ObjectSharing(uid, object_type, public_access, usergroup_access)

    # different usergroup
    uid = 'dataElement1'
    object_type = 'dataElements'
    public_access = 'rw------'
    usergroup_access = {UserGroupAccess(uid='userGroup222', access='rw------')}
    sd2 = ObjectSharing(uid, object_type, public_access, usergroup_access)

    # different usergroup access
    uid = 'dataElement1'
    object_type = 'dataElements'
    public_access = 'rw------'
    usergroup_access = {UserGroupAccess(uid='userGroup222', access='r-------')}
    sd3 = ObjectSharing(uid, object_type, public_access, usergroup_access)

    # different object type
    uid = 'dataElement1'
    object_type = 'categoryOptions'
    public_access = 'rw------'
    usergroup_access = {UserGroupAccess(uid='userGroup222', access='r-------')}
    sd4 = ObjectSharing(uid, object_type, public_access, usergroup_access)

    # copy of above
    uid = 'dataElement1'
    object_type = 'categoryOptions'
    public_access = 'rw------'
    usergroup_access = {UserGroupAccess(uid='userGroup222', access='r-------')}
    sd4_copy = ObjectSharing(uid, object_type, public_access, usergroup_access)

    return sd0, sd1, sd2, sd3, sd4, sd4_copy


def test_sharingdefinition_not_equal(sharingdefinitions):
    sd0 = sharingdefinitions[0]
    sd1 = sharingdefinitions[1]
    sd2 = sharingdefinitions[2]
    sd3 = sharingdefinitions[3]
    sd4 = sharingdefinitions[4]
    sd4_copy = sharingdefinitions[5]

    assert all([isinstance(sd, ObjectSharing) for sd in sharingdefinitions])
    assert all([isinstance(sd, ObjectSharing) for sd in (sd0, sd1, sd2, sd3, sd4, sd4_copy)])

    assert sd0 != sd1
    assert sd1 != sd2
    assert sd2 != sd3
    assert sd3 != sd4
    assert sd4 != sd0


def test_sharingdefinitions_equal(sharingdefinitions):
    sd4 = sharingdefinitions[4]
    sd4_copy = sharingdefinitions[5]
    assert sd4 == sd4_copy


def test_sharingdefinitions_set(sharingdefinitions):
    assert len(sharingdefinitions) == 6
    assert len(set(sharingdefinitions)) == 5  # don't count the copy


@pytest.fixture()
def dhis_accesses():
    return [Dhis('play.dhis2.org/demo', 'admin', 'district', api_version=i) for i in range(22, newest_dhis)]


@pytest.fixture()
def sharingdefinitions_multi_uga():
    # no userGroup sharing
    uid = 'dataElement1'
    object_type = 'dataElements'
    public_access = 'rw------'
    sd0 = ObjectSharing(uid, object_type, public_access)

    # multiple usergroups 1
    uid = 'dataElement1'
    object_type = 'dataElements'
    public_access = 'rw------'

    uga1 = UserGroupAccess(uid='userGroup222', access='rw------')
    uga2 = UserGroupAccess(uid='userGroup333', access='r-------')
    sd1 = ObjectSharing(uid, object_type, public_access, {uga1, uga2})

    # multiple usergroups 2
    uid = 'dataElement1'
    object_type = 'dataElements'
    public_access = 'rw------'

    uga3 = UserGroupAccess(uid='userGroup222', access='rw------')
    uga4 = UserGroupAccess(uid='userGroup444', access='rw------')
    sd2 = ObjectSharing(uid, object_type, public_access, {uga3, uga4})

    uga5 = UserGroupAccess(uid='userGroup222', access='rw------')
    uga6 = UserGroupAccess(uid='userGroup444', access='rw------')
    sd3 = ObjectSharing(uid, object_type, public_access, {uga5, uga6})

    assert sd0 != sd1
    assert sd1 != sd2
    assert sd0 != sd2
    assert sd2 == sd3


@pytest.fixture()
def sharingdefinitions_changed_order():
    uid = 'dataElement1'
    object_type = 'dataElements'
    public_access = 'rw------'

    uga1 = UserGroupAccess(uid='userGroup222', access='rw------')
    uga2 = UserGroupAccess(uid='userGroup333', access='r-------')
    sd0 = ObjectSharing(uid, object_type, public_access, {uga1, uga2})

    uga1 = UserGroupAccess(uid='userGroup222', access='rw------')
    uga2 = UserGroupAccess(uid='userGroup333', access='r-------')
    sd1 = ObjectSharing(uid, object_type, public_access, {uga2, uga1})

    assert sd0 == sd1


def test_skip():
    uid = 'dataElement1'
    object_type = 'dataElements'
    public_access = 'rw------'

    existing = {
        "id": uid,
        "publicAccess": public_access,
        "userGroupAccesses": [
            {
                "id": "userGroup222",
                "access": 'rw------'
            },
            {
                "id": "userGroup333",
                "access": 'r-------'
            }
        ]
    }

    uga1 = UserGroupAccess(uid='userGroup222', access='rw------')
    uga2 = UserGroupAccess(uid='userGroup333', access='r-------')
    submitted = ObjectSharing(uid, object_type, public_access, {uga1, uga2})

    skip_it = skip(overwrite=False, elem=existing, new=submitted)
    assert skip_it is True


def test_skip_2():
    uid = 'dataElement1'
    object_type = 'dataElements'
    public_access = 'rw------'

    existing = {
        "id": uid,
        "publicAccess": public_access,
        "userGroupAccesses": [
            {
                "id": "userGroup222",
                "access": 'r-------'
            },
            {
                "id": "userGroup333",
                "access": 'r-------'
            }
        ]
    }

    uga1 = UserGroupAccess(uid='userGroup222', access='rw------')
    uga2 = UserGroupAccess(uid='userGroup333', access='r-------')
    submitted = ObjectSharing(uid, object_type, public_access, {uga1, uga2})

    skip_it = skip(overwrite=False, elem=existing, new=submitted)
    assert skip_it is False


def test_skip_3():
    uid = 'dataElement1'
    object_type = 'dataElements'
    public_access = 'rw------'

    existing = {
        "id": uid,
        "publicAccess": 'rw------',
        "userGroupAccesses": [
            {
                "id": "userGroup222",
                "access": 'rw------'
            },
            {
                "id": "userGroup333",
                "access": 'r-------'
            }
        ]
    }

    uga1 = UserGroupAccess(uid='userGroup222', access='rw------')
    uga2 = UserGroupAccess(uid='userGroup333', access='r-------')
    submitted = ObjectSharing(uid, object_type, public_access, {uga1, uga2})

    skip_it = skip(overwrite=True, elem=existing, new=submitted)
    assert skip_it is False


def test_skip_4():
    uid = 'dataElement1'
    object_type = 'dataElements'
    public_access = 'readwrite'

    existing = {
        "id": uid,
        "publicAccess": 'r-------',
        "userGroupAccesses": [
            {
                "id": "userGroup222",
                "access": 'rw------'
            },
            {
                "id": "userGroup333",
                "access": 'r-------'
            }
        ]
    }

    uga1 = UserGroupAccess(uid='userGroup222', access='r-------')
    uga2 = UserGroupAccess(uid='userGroup333', access='r-------')
    submitted = ObjectSharing(uid, object_type, public_access, {uga1, uga2})

    skip_it = skip(overwrite=True, elem=existing, new=submitted)
    assert skip_it is False


def test_permissions():
    access = '--------'
    p = Permission(access)
    assert p.permission == access

    access = 'r-------'
    p = Permission(access)
    assert p.permission == access

    access = 'rw------'
    p = Permission(access)
    assert p.permission == access

    access = 'none'
    p = Permission(access)
    assert p.permission == '--------'

    access = 'readonly'
    p = Permission(access)
    assert p.permission == 'r-------'

    access = 'readwrite'
    p = Permission(access)
    assert p.permission == 'rw------'

    with pytest.raises(ClientException):
        Permission('...')


def test_validuid():
    uids = [
        'FjqZHqXYz6B',
        'lJA6yJOaz55',
        'zFnd4rhAgB4',
        'S4yhX7Irce4',
        'Xthl7KLnu4x',
        'fq1tNzpMtrr',
        'Nq8NwQkGL0u',
        'XGm1jea1msS',
        'EazKJw2dECM',
        'HDAwB6ZbPMu',
        'ggOZLNSKmJu',
        'NwMvNTk4qUO',
        'XHj7GOnCQvR',
        'XYo8Tvbs7z2',
        'CbKdovHx51o',
        'l2WnnARMNr3',
        'V4a9SacO0R6',
        'kJjHszgtHPX',
        'AugqpMvB9AT',
        's1E14OBogl5',
        'r0Czhz5UOrn',
        'pWEpEPVGfgq',
        'XbwQwczCusw',
        'v2LGMXSkof6',
        'EaLniEadnJe',
        'FzvyQnjERUj',
        'jOdbKHZiKep',
        'TpM8F1gik4i',
        'UbfsXKJfm1r',
        'np88NID7Uvq',
        'n1Bk5GlvW6r',
        'hLB2ZXJDya0',
        'IeFeKjgl5Eh',
        'Z3EyTxH2Ml0',
        'r5u0yVtbA45',
        'oXgLKgWjP6G',
        'zxm1YQYmOM5',
        'XfvTvygOvac',
        'inCqnYYGgWm',
        'n4ixTc9nVaO',
        'R6lhihYtXeI',
        'hJbAYoes7ph',
        'qZCHwPTPx8P',
        'IhIxzH33Mz2',
        'G171OHsyq5v',
        'IEzfnYq0nKH',
        'XtJWthTq2QZ',
        'jlhmYBKTYsc',
        'Aj1fCFtoytr',
        'PTgEah2fjZU',
        'mZyojwGIKmE',
        'I5dhtf5BxeD',
        'Pg3MbAeIemc',
        'oZ48IXw8IUE',
        'E93rcsxl5gl',
        'LkQEG37VpIO',
        'tVAtJLpaL0J',
        'qX68Gpm4eHZ',
        'xVRUSY1X7X6',
        'oNKwIrE6VA0',
        'PuhA2JcHMMp',
        'xeYhiwxO9Cb',
        'Qwb7MfiGFqR',
        'JFfdlEbZBRT',
        'smmuiJ7KWmu',
        'JZzaLyAc3hE',
        'uCFa0Ep658M',
        'L9i7m8zjnuV',
        'NnO7Nmk0nsM',
        'zB7FfdPNiDB',
        'hwSaexMTKsp',
        'lyvh4lKj0FM',
        'ywP0U0vpaeH',
        'TJk296r9Xza',
        'kqIKFCnWpU6',
        'z4tsh8HnW1N',
        'lhkoiVpverj',
        'lNdeZ2bWtns',
        'NJCmEOiieR0',
        'uGWrydu23dU',
        'gb0QsIxz8Uo',
        'ewRtIxUaAQX',
        'oXDtuP3G4yl',
        'A6RFqo2enp3',
        'yStt4YXd6kd',
        'ANvrHN97pyc',
        'K3gdtgj0b2M',
        'vMDQ6ScolID',
        'vrsNFUVSRiO',
        'Ks8B1UkrRaV',
        'AcUvuI5WElt',
        'gKH5WRzbira',
        'BzEsYbkoje5',
        'mXbpBP3oZf1',
        'hlG4uMY10Ta',
        'fU8Oh0i5OzP',
        'QbQZy8gWn7K',
        'Dho12fNjDUW',
        'prmRBBixnch',
        'IArasnc5pvK',
        'eqmGKKoLUwh',
        'cwiFMeoRLyU',
        'F0rL9aZb4zy',
        'cEiBt7VMUPU',
        'XStWcBR1Vvq',
        'spgh5JSx0PP',
        'nXbsfkOx8ES',
        'LewYTpXt4QM',
        'HiT1vEOMDlr',
        'R1KbVP6FRYf',
        'OwtSjEHWCcu',
        'PytEX0fscW3',
        'de171Utglms',
        'LTXWbUt5V4W',
        'KY6uFYshFW1',
        'VatiRAeQqoj',
        'JHFbevWcdn0',
        'vd72wQVFPwt',
        'KLqndgUbBVP',
        'Ci7eb3LxeFM',
        'M44B1pDDV1G',
        'TIPPujLCxIc',
        'BmhAXgS0gkS',
        'P82SuzTY6Hn',
        'AfkfzB3R7hA',
        'cQ9fgFHP84m',
        'I4eG76IAjmN',
        'fD08CoDDZ9R',
        'yNSQb6pBs8e',
        'VG8NyRpRO63',
        'JyLMGtP2kjB',
        'ZoGbvzf8QGn',
        'hQ4lvdea8vU',
        'nJTi9gCVJ5z',
        'b9C9cEi03SN',
        'ahDiD9OaFvP',
        'sgsvIkBufgF',
        'eoLUqlEvpFS',
        'FzBmCSMJ24s',
        'odgjiqtKIUB',
        'O0IKViohARV',
        'MngSKxGmulw',
        'F6jnbub9BsD',
        'w3USiF7XCFi',
        'arddWyb2U2q',
        'MCI6Pqonwgy',
        'CxRY9CrqEpo',
        'wF4UdsrEKPE',
        'mlAShOTiy75',
        'k5hoVdjgBC9',
        'Mrvk6ptc3m5',
        'n2uzQ9PUD12',
        'OmK7oZDg5BG',
        'vzdLKqqy81g',
        'R4ZR2TfEbiI',
        'BWdZH0sThPw',
        'Y8qLVqQX5IC',
        'oPmMvS0gdPt',
        'Q2ude04tqKp',
        'bDgRPWZV7Z8',
        'cXEkxxBCZK7',
        'iUWVby4WnDB',
        'tLi9H0SIUuV',
        'ILIogP2iauO',
        'liIVDHo67uI',
        'FKjEOCwAQHf',
        'ouZmSX9qH2G',
        'GJVyYvKqyYZ',
        'PyjQPA7Ya2E',
        'xnmbbxDlXZP',
        'MpnamMdU518',
        'b7pWzh2tbv8',
        'tpo3r7DkbXh',
        'fIbcvxDpotg',
        'Xwe4w6V0oIy',
        'EU3nkZMh2ub',
        'd4eyg4aNamR',
        'mdoQucW5N93',
        'FwWe2xy6McF',
        'RoDgibPCmK0',
        'dadfSWnEx8Z',
        'lpmHuFAdytS',
        'Ujbt5FQMlaF',
        'k2o8A4VRI6m',
        'z9M3nX4SyZ8',
        'IpRrBFD1nfP',
        'g2BFEUL7E3R',
        'siswzRcABsN',
        'UKfJf4IEs9f',
        'wk6QfllQgyK',
        'PuYEOaSqMl8',
        'nZCFF6J5Pi4',
        'r0s2YV0DnzZ',
        'nAItDTm9hKm',
        'kOarAA7WOvU',
        'z2AZL3dxonk',
        'u8FSTRjoDGF',
        'LJi9F925sGj',
        'kehNpYifbno',
        'fD27p35zqUs'
    ]
    assert all([valid_uid(uid) for uid in uids])

    assert valid_uid('2132xf') is False
