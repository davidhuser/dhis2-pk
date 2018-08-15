from pk.share import Permission, UserGroupAccess, ShareableObject

import pytest


class TestPermission(object):

    def test_symbolic_notation_unique(self):
        options = ('rw', 'r-', '--')
        assert len(Permission.symbolic_notation) == len(set(Permission.symbolic_notation))
        assert(len(options)**2 == len(Permission.symbolic_notation))

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
