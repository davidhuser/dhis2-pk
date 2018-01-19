import pytest

from pk.core.exceptions import ClientException
from pk.share import SharingDefinition, UserGroupAccess, validate_filter
from pk.core.static import newest_dhis


@pytest.fixture()
def sharingdefinitions():
    # no userGroup sharing
    uid = 'dataElement1'
    object_type = 'dataElements'
    public_access = 'readwrite'
    sd0 = SharingDefinition(uid, object_type, public_access)

    # usergroup sharing
    uid = 'dataElement1'
    object_type = 'dataElements'
    public_access = 'readwrite'
    usergroup_access = {UserGroupAccess(uid='userGroup111', access='readwrite')}
    sd1 = SharingDefinition(uid, object_type, public_access, usergroup_access)

    # different usergroup
    uid = 'dataElement1'
    object_type = 'dataElements'
    public_access = 'readwrite'
    usergroup_access = {UserGroupAccess(uid='userGroup222', access='readwrite')}
    sd2 = SharingDefinition(uid, object_type, public_access, usergroup_access)

    # different usergroup access
    uid = 'dataElement1'
    object_type = 'dataElements'
    public_access = 'readwrite'
    usergroup_access = {UserGroupAccess(uid='userGroup222', access='read')}
    sd3 = SharingDefinition(uid, object_type, public_access, usergroup_access)

    # different object type
    uid = 'dataElement1'
    object_type = 'categoryOptions'
    public_access = 'readwrite'
    usergroup_access = {UserGroupAccess(uid='userGroup222', access='read')}
    sd4 = SharingDefinition(uid, object_type, public_access, usergroup_access)

    # copy of above
    uid = 'dataElement1'
    object_type = 'categoryOptions'
    public_access = 'readwrite'
    usergroup_access = {UserGroupAccess(uid='userGroup222', access='read')}
    sd4_copy = SharingDefinition(uid, object_type, public_access, usergroup_access)

    return sd0, sd1, sd2, sd3, sd4, sd4_copy


def test_sharingdefinition_not_equal(sharingdefinitions):
    sd0 = sharingdefinitions[0]
    sd1 = sharingdefinitions[1]
    sd2 = sharingdefinitions[2]
    sd3 = sharingdefinitions[3]
    sd4 = sharingdefinitions[4]
    sd4_copy = sharingdefinitions[5]

    assert all([isinstance(sd, SharingDefinition) for sd in sharingdefinitions])
    assert all([isinstance(sd, SharingDefinition) for sd in (sd0, sd1, sd2, sd3, sd4, sd4_copy)])

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


def test_filter_delimiter():
    argument = 'name:like:ABC||name:like:XYZ'
    for version in range(22, 24):
        with pytest.raises(ClientException):
            validate_filter(argument, version)

    for version in range(25, newest_dhis):
        assert '||' == validate_filter(argument, version)

    argument = 'name:^like:ABC'
    for version in range(28, newest_dhis):
        with pytest.raises(ClientException):
            validate_filter(argument, version)

    argument = 'name:^like:CDB||name:like:EFG'
    for version in range(28, newest_dhis):
        with pytest.raises(ClientException):
            validate_filter(argument, version)

    argument = 'name:like:ABC||name:like:CDE&&name:like:EFG'
    for version in range(22, newest_dhis):
        with pytest.raises(ClientException):
            validate_filter(argument, version)


@pytest.fixture()
def sharingdefinitions_multi_uga():
    # no userGroup sharing
    uid = 'dataElement1'
    object_type = 'dataElements'
    public_access = 'readwrite'
    sd0 = SharingDefinition(uid, object_type, public_access)

    # multiple usergroups 1
    uid = 'dataElement1'
    object_type = 'dataElements'
    public_access = 'readwrite'

    uga1 = UserGroupAccess(uid='userGroup222', access='readwrite')
    uga2 = UserGroupAccess(uid='userGroup333', access='read')
    sd1 = SharingDefinition(uid, object_type, public_access, {uga1, uga2})

    # multiple usergroups 2
    uid = 'dataElement1'
    object_type = 'dataElements'
    public_access = 'readwrite'

    uga3 = UserGroupAccess(uid='userGroup222', access='readwrite')
    uga4 = UserGroupAccess(uid='userGroup444', access='readwrite')
    sd2 = SharingDefinition(uid, object_type, public_access, {uga3, uga4})

    uga5 = UserGroupAccess(uid='userGroup222', access='readwrite')
    uga6 = UserGroupAccess(uid='userGroup444', access='readwrite')
    sd3 = SharingDefinition(uid, object_type, public_access, {uga5, uga6})

    assert sd0 != sd1
    assert sd1 != sd2
    assert sd0 != sd2
    assert sd2 == sd3


@pytest.fixture()
def sharingdefinitions_changed_order():
    uid = 'dataElement1'
    object_type = 'dataElements'
    public_access = 'readwrite'

    uga1 = UserGroupAccess(uid='userGroup222', access='readwrite')
    uga2 = UserGroupAccess(uid='userGroup333', access='read')
    sd0 = SharingDefinition(uid, object_type, public_access, {uga1, uga2})

    uga1 = UserGroupAccess(uid='userGroup222', access='readwrite')
    uga2 = UserGroupAccess(uid='userGroup333', access='read')
    sd1 = SharingDefinition(uid, object_type, public_access, {uga2, uga1})

    assert sd0 == sd1
