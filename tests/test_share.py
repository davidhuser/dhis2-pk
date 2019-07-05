from collections import namedtuple

import pytest

from pk.share import (
    Permission,
    UserGroupAccess,
    ShareableObject,
    set_delimiter,
    UserGroupAccessMerge,
    merge,
    PUBLIC_ACCESS_INHERITED,
    validate_args,
    validate_data_access
)
from pk.common.exceptions import PKClientException


class TestPermission(object):

    def test_symbolic_notation_unique(self):
        options = ('rw', 'r-', '--')
        assert len(Permission.symbolic_notation) == len(set(Permission.symbolic_notation))
        assert(len(options)**2 == len(Permission.symbolic_notation))

    def test_permission_not_equal(self):
        assert Permission(metadata='readwrite', data=None) != Permission(metadata=None, data=None)

    def test_permission_init(self):
        p = Permission(metadata='rw', data='r-')
        assert p.metadata == 'rw'
        assert p.data == 'r-'

    @pytest.mark.parametrize('public_args, metadata, data, symbol', [
        ([['readwrite', 'readonly']], 'readwrite', 'readonly', 'rwr-----'),
        ([['readwrite', None]], 'readwrite', None, 'rw------'),
        ([['readwrite']], 'readwrite', None, 'rw------'),
        ([['readonly', 'readwrite']], 'readonly', 'readwrite', 'r-rw----'),
    ])
    def test_permission_from_public_args(self, public_args, metadata, data, symbol):
        p = Permission.from_public_args(public_args)
        assert p.metadata == metadata
        assert p.data == data
        assert p.to_symbol() == symbol

    def test_permission_from_public_args_inherited(self):
        """If not specified, assume it's inherited from server definition"""
        assert Permission.from_public_args(None) == PUBLIC_ACCESS_INHERITED

    @pytest.mark.parametrize('symbol, metadata, data', [
        ('rwrw----', 'readwrite', 'readwrite'),
        ('rwr-----', 'readwrite', 'readonly'),
        ('rw------', 'readwrite', None),
        ('r-rw----', 'readonly', 'readwrite'),
        ('r-r-----', 'readonly', 'readonly'),
        ('r-------', 'readonly', None),
        ('--rw----', None, 'readwrite'),
        ('--r-----', None, 'readonly'),
        ('--------', None, None)
    ])
    def test_permission_from_symbol(self, symbol, metadata, data):
        p = Permission.from_symbol(symbol)
        assert p.metadata == metadata
        assert p.data == data

    @pytest.mark.parametrize('groups, metadata, data', [
        (['aFilter', 'readwrite', 'readwrite'], 'readwrite', 'readwrite'),
        (['aFilter', 'readwrite', 'readonly'], 'readwrite', 'readonly'),
        (['aFilter', 'readwrite'], 'readwrite', None),
        (['aFilter', 'readonly', 'readwrite'], 'readonly', 'readwrite'),
        (['aFilter', 'readonly', 'readonly'], 'readonly', 'readonly'),
        (['aFilter', 'readonly', 'none'], 'readonly', 'none'),
        (['aFilter', 'none', 'readwrite'], 'none', 'readwrite'),
        (['aFilter', 'none', 'readonly'], 'none', 'readonly'),
        (['aFilter', 'none', 'none'], 'none', 'none'),
        (['aFilter', 'none'], 'none', None)

    ])
    def test_permission_from_group_args(self, groups, metadata, data):
        p = Permission.from_group_args(groups)
        assert p.metadata == metadata
        assert p.data == data

    def test_all_equal(self):
        p1 = Permission(metadata='readwrite', data='readonly')
        p2 = Permission.from_public_args([['readwrite', 'readonly']])
        p3 = Permission.from_symbol('rwr-----')
        p4 = Permission.from_group_args(['aFilter', 'readwrite', 'readonly'])

        assert p1 == p2
        assert p3 == p4
        assert p1 == p4

        assert p1.to_symbol() == p2.to_symbol()
        assert p3.to_symbol() == p4.to_symbol()
        assert p1.to_symbol() == p4.to_symbol()

    def test_print(self):
        assert str(Permission(metadata=None, data=None)) == '[metadata:none]'
        assert str(Permission(metadata=None, data='readwrite')) == '[metadata:none] [data:readwrite]'
        assert repr(Permission(metadata=None, data='readwrite')) == 'None readwrite'

class TestUserGroupAccess(object):

    @pytest.mark.parametrize('access, permission', [
        ('rw------', Permission(metadata='readwrite', data='none')),
        ('rw------', Permission(metadata='readwrite', data=None)),
    ])
    def test_from_dict(self, access, permission):
        data = {'id': 'abc', 'access': access}
        uga = UserGroupAccess.from_dict(data)
        assert permission.to_symbol() == access
        assert uga.to_json() == {"id": "abc", "access": permission.to_symbol()}

    @pytest.mark.parametrize('access', [
        'ab-------', 'readwrite', 123, None
    ])
    def test_from_dict_invalid_access(self, access):
        data = {'id': 'abc', 'access': access}
        uga = UserGroupAccess.from_dict(data)
        assert uga.permission == Permission(None, None)
        assert uga.to_json() == {"id": "abc", "access": "--------"}

    def test_inequality(self):
        uga1 = UserGroupAccess(uid='abc', permission=Permission(metadata='readwrite', data='readwrite'))
        uga2 = UserGroupAccess(uid='abc', permission=Permission(metadata='readonly', data='readwrite'))
        uga3 = UserGroupAccess(uid='cde', permission=Permission(metadata='readwrite', data='readwrite'))

        assert uga1 != uga2
        assert uga1 != uga3


class TestShareableObject(object):

    def test_equality(self):
        s1 = ShareableObject(
            'dataElements',
            'abc',
            'DE01',
            'rw------',
            usergroup_accesses={
                UserGroupAccess(uid='123', permission='rwr-----'),
                UserGroupAccess(uid='456', permission='rwr-----'),
            }
        )
        s2 = ShareableObject(
            'dataElements',
            'abc',
            'DE01',
            'rw------',
            usergroup_accesses={
                UserGroupAccess(uid='456', permission='rwr-----'),  # switched out
                UserGroupAccess(uid='123', permission='rwr-----'),
            }
        )
        assert s1 == s2

        s3 = ShareableObject(
            'dataElements',
            'abc',
            'DE01',
            'rw------',
            usergroup_accesses={
                UserGroupAccess(uid='456', permission='rwr-----'),
            }
        )
        assert s1 != s3

    def test_identifier(self):
        s1 = ShareableObject(
            obj_type='dataElements',
            uid='abc',
            name='DE01',
            public_access='rw------'
        )
        assert s1.identifier() == u"'DE01'"

        s2 = ShareableObject(
            obj_type='dataElements',
            uid='abc',
            name=None,
            code='CODE3000',
            public_access='rw------'
        )
        assert s2.identifier() == u"'CODE3000'"

        s3 = ShareableObject(
            obj_type='dataElements',
            uid='abc',
            name=None,
            public_access='rw------'
        )
        assert s3.identifier() == u""


@pytest.mark.parametrize('version, argument, expected', [
    (22, 'name:like:ABC', ('&&', 'AND')),
    (22, 'name:like:ABC&&code:eq:XYZ', ('&&', 'AND')),
    (25, None, (None, None)),
    (29, 'name:like:ABC||name:like:CDE', ('||', 'OR'))
])
def test_set_delimiter(version, argument, expected):
    assert set_delimiter(version, argument) == expected


@pytest.mark.parametrize('version, argument', [
    (29, 'name:^like:ABC'),
    (29, 'name:like:||&&'),
    (29, 'name:like:ABC||name:like:CDE&&name:like:XYZ'),
    (24, 'name:like:ABC||name:like:XYZ')
])
def test_set_delimiter_raises(version, argument):
    with pytest.raises(PKClientException):
        set_delimiter(version, argument)

class TestValidateArgs(object):
    Arguments = namedtuple('args', 'public_access extend groups')
    def test_extend_usergroups_required(self):
        api_version = 32
        args = self.Arguments(public_access=None, extend=True, groups=None)
        with pytest.raises(PKClientException):
            validate_args(args, api_version)

    def test_extend_usergroups_not_required_with_publicaccess(self):
        api_version = 32
        args = self.Arguments(public_access='readwrite', extend=True, groups=None)
        validate_args(args, api_version)

    def test_public_access_required_when_none(self):
        api_version = 32
        args = self.Arguments(public_access=None, extend=False, groups=None)
        with pytest.raises(PKClientException):
            validate_args(args, api_version)

    def test_public_access_incorrect_count(self):
        api_version = 32
        args = self.Arguments(public_access=['readwrite', 'none', 'readonly'], extend=False, groups=None)
        with pytest.raises(PKClientException):
            validate_args(args, api_version)


class TestValidateDataAccess(object):
    pass

class TestUserGroupAccessMerge(object):

    def test_usergroupaccessmerge_sets(self):
        ug1 = UserGroupAccessMerge(uid='abc', permission='rw------')
        ug2 = UserGroupAccessMerge(uid='abc', permission='rw------')
        ug3 = UserGroupAccessMerge(uid='abc', permission='r------')
        ug4 = UserGroupAccessMerge(uid='cde', permission='r------')
        ug5 = UserGroupAccessMerge(uid='abc ', permission='rw------')

        ug_set = set()
        ug_set.add(ug1)
        assert ug2 in ug_set
        assert ug3 in ug_set
        assert ug4 not in ug_set
        assert ug5 not in ug_set

    def test_inequality(self):
        uga1 = UserGroupAccessMerge(uid='abc', permission=Permission(metadata='readwrite', data='readwrite'))
        uga2 = UserGroupAccessMerge(uid='cde', permission=Permission(metadata='readwrite', data='readwrite'))
        assert uga1 != uga2

class TestMerge(object):

    @pytest.mark.parametrize('server_uga, local_uga, expected', [
        [ # user group accesses is retained
            {
                UserGroupAccess(uid='abc', permission=Permission(metadata='readwrite', data=None)),
                UserGroupAccess(uid='def', permission=Permission(metadata='readwrite', data=None))
            },
            {
                UserGroupAccess(uid='abc', permission=Permission(metadata='readwrite', data=None)),
                UserGroupAccess(uid='def', permission=Permission(metadata='readwrite', data=None))
            },
            {
                UserGroupAccess(uid='abc', permission=Permission(metadata='readwrite', data=None)),
                UserGroupAccess(uid='def', permission=Permission(metadata='readwrite', data=None))
            }
        ],
        [ # user group accesses have higher priority when supplied to what is already on the server
            {
                UserGroupAccess(uid='abc', permission=Permission(metadata='readwrite', data=None)),
                UserGroupAccess(uid='def', permission=Permission(metadata='readwrite', data='readonly'))
            },
            {
                UserGroupAccess(uid='abc', permission=Permission(metadata='readonly', data=None)),
            },
            {
                UserGroupAccess(uid='abc', permission=Permission(metadata='readonly', data=None)),
                UserGroupAccess(uid='def', permission=Permission(metadata='readwrite', data='readonly'))
            }
        ],
        [  # user group accesses are not overwritten with NONE
            {
                UserGroupAccess(uid='abc', permission=Permission(metadata='readwrite', data=None)),
                UserGroupAccess(uid='def', permission=Permission(metadata='readwrite', data=None))
            },
            {
                UserGroupAccess(uid='abc', permission=Permission(metadata='readwrite', data=None)),
                UserGroupAccess(uid='def', permission=Permission(metadata=None, data=None))
            },
            {
                UserGroupAccess(uid='abc', permission=Permission(metadata='readwrite', data=None)),
            }
        ],
        [  # no user groups present on server
            {},
            {
                UserGroupAccess(uid='abc', permission=Permission(metadata='readwrite', data=None)),
                UserGroupAccess(uid='def', permission=Permission(metadata='readwrite', data=None))
            },
            {
                UserGroupAccess(uid='abc', permission=Permission(metadata='readwrite', data=None)),
                UserGroupAccess(uid='def', permission=Permission(metadata='readwrite', data=None))
            }
        ],
        [  # no user groups present on server nor specified
            {},
            {},
            {}
        ],
        [  # ordering not important
            {},
            {
                UserGroupAccess(uid='abc', permission=Permission(metadata=None, data='readwrite')),
                UserGroupAccess(uid='def', permission=Permission(metadata='readwrite', data=None))
            },
            {
                UserGroupAccess(uid='def', permission=Permission(metadata='readwrite', data=None)),
                UserGroupAccess(uid='abc', permission=Permission(metadata=None, data='readwrite'))
            }
        ]
    ])
    def test_merge(self, server_uga, local_uga, expected):
        output = merge(server_uga, local_uga)
        assert output == expected

