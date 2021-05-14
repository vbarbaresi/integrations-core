# (C) Datadog, Inc. 2018-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from __future__ import unicode_literals

import os
import re

import pytest

from datadog_checks.redisdb import Redis

from .common import HOST, USERNAME, PASSWORD, PORT, PORT_ACL_INSTANCE

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("dd_environment")]


def test_redis_auth_ok(aggregator, redis_auth):
    """
    Test the check can authenticate and connect
    """
    instance = {'host': HOST, 'port': PORT, 'password': PASSWORD}
    redis = Redis('redisdb', {}, [instance])
    redis.check(instance)
    assert aggregator.metric_names, "No metrics returned"


def test_redis_auth_empty_pass(redis_auth):
    """
    Test the check providing an empty password
    """
    instance = {'host': HOST, 'port': PORT, 'password': ''}
    redis = Redis('redisdb', {}, [instance])

    with pytest.raises(Exception, match=re.compile('authentication required|operation not permitted', re.I)):
        redis.check(instance)


def test_redis_auth_wrong_pass(redis_auth):
    """
    Test the check providing the wrong password
    """
    instance = {'host': HOST, 'port': PORT, 'password': 'badpass'}
    redis = Redis('redisdb', {}, [instance])

    try:
        redis.check(instance)
        assert 0, "Check should raise an exception"
    except Exception as e:
        msg = str(e).lower()
        assert ("invalid password" in msg) or ("wrongpass" in msg)


@pytest.mark.skipif(os.environ.get('REDIS_VERSION') in ('3.2', '4.0'), reason="Test requires Redis > 6 for ACLs")
def test_redis_auth_acl_good(aggregator, redis_auth_acl):
    """
    Test the check with ACL without collect client metrics
    """
    instance = {'host': HOST, 'port': PORT_ACL_INSTANCE, 'username': USERNAME, 'password': PASSWORD, 'collect_client_metrics': False}
    redis = Redis('redisdb', {}, [instance])

    redis.check(instance)
    assert 'redis.net.commands' in aggregator.metric_names


@pytest.mark.skipif(os.environ.get('REDIS_VERSION') in ('3.2', '4.0'), reason="Test requires Redis > 6 for ACLs")
def test_redis_auth_acl_bad(aggregator, redis_auth_acl):
    """
    Test the check with ACL not allowing collect client metrics: should log an error and continue without raising
    """
    instance = {'host': HOST, 'port': PORT_ACL_INSTANCE, 'username': USERNAME, 'password': PASSWORD, 'collect_client_metrics': True}
    redis = Redis('redisdb', {}, [instance])

    redis.check(instance)  # should not raise
    assert 'redis.net.commands' in aggregator.metric_names
