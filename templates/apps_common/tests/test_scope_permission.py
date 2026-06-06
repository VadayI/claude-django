"""HasScope unit checks: required scopes must be a subset of the token's scopes.

Pure unit tests — no DB, no live token issuance. ``request.auth`` is stubbed with
a mapping carrying a space-delimited ``scope`` claim (the simplejwt token shape).
"""

from types import SimpleNamespace

from apps.common.permissions import HasScope


class _ScopedView:
    """Minimal view stub declaring required scopes."""

    required_scopes = ["orders:read"]


def _request(scope):
    """Build a request stub whose ``auth`` carries the given ``scope`` claim."""
    auth = {"scope": scope} if scope is not None else None
    return SimpleNamespace(auth=auth)


def test_no_required_scopes_allows():
    """A view without required_scopes imposes no scope check."""
    assert HasScope().has_permission(_request("anything"), SimpleNamespace(required_scopes=[]))


def test_subset_granted_allows():
    """All required scopes present among granted scopes -> allowed."""
    assert HasScope().has_permission(_request("orders:read orders:write"), _ScopedView())


def test_missing_scope_denies():
    """A token lacking the required scope -> denied."""
    assert not HasScope().has_permission(_request("profile:read"), _ScopedView())


def test_no_token_denies_when_required():
    """No token at all, but the view requires a scope -> denied."""
    assert not HasScope().has_permission(_request(None), _ScopedView())
