#!/usr/bin/env python3
"""
AIsa Twitter API Client
Twitter/X read APIs for autonomous agents.

Read operations use GET with Authorization: Bearer AISA_API_KEY.

Usage (read):
    python twitter_client.py user-info --username <username>
    python twitter_client.py search --query <query> [--type Latest|Top]
    ...
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

import aisa_transport
import costs


REQUEST_TIMEOUT = 60


def _resolve_aisa_api_key() -> str:
    """Resolve AISA_API_KEY from the environment, then from known credential files.

    os.environ is not always populated. The plugin / OpenClaw install form has no
    profile .env to inherit from, and hermes' sandboxed code-execution path
    strips variables whose name contains "KEY". `~/.aisa/credentials` is the
    cross-harness convention AgentSpec already documents for exactly this case
    (plugin-core/inject.ts: "scripts resolve these as: env var ->
    ~/.aisa/credentials").

    Order: env -> ~/.aisa/credentials
           -> $HERMES_HOME/profiles/$HERMES_PROFILE/.env (when HERMES_PROFILE is set)
           -> $HERMES_HOME/.env

    Under `hermes --profile X`, HERMES_HOME *is* the profile directory and
    HERMES_PROFILE is unset, so the last candidate resolves to that profile's own
    .env; the middle one covers harnesses that identify the profile by name
    instead. Only the running profile is ever read, never a sibling's, so a host
    with several profiles cannot hand back the wrong tenant's key.

    Returns "" when nothing is found; never raises on an unreadable or
    undecodable file.

    Kept byte-identical across the AIsa skills that need it —
    financial/marketpulse/scripts/market_client.py is the canonical copy; change
    it there first, then propagate.
    """
    key = os.environ.get("AISA_API_KEY", "").strip()
    if key:
        return key

    home = os.path.expanduser("~")
    hermes_home = os.environ.get("HERMES_HOME") or os.path.join(home, ".hermes")

    candidates = [os.path.join(home, ".aisa", "credentials")]
    profile = os.environ.get("HERMES_PROFILE", "").strip()
    if profile:
        candidates.append(os.path.join(hermes_home, "profiles", profile, ".env"))
    candidates.append(os.path.join(hermes_home, ".env"))

    for path in candidates:
        try:
            # utf-8-sig drops a BOM; errors="replace" keeps a mis-encoded file
            # from raising UnicodeDecodeError (a ValueError, not an OSError).
            with open(path, encoding="utf-8-sig", errors="replace") as handle:
                lines = handle.readlines()
        except OSError:
            continue
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):].lstrip()
            name, sep, value = line.partition("=")
            if not sep or name.strip() != "AISA_API_KEY":
                continue
            value = value.strip()
            if value[:1] in ("'", '"'):
                # A quoted value ends at its closing quote; whatever follows is
                # a trailing comment, not part of the secret. Checking "starts
                # and ends with a quote" instead would miss `KEY="v" # note`
                # and hand back the value with its quotes still attached.
                end = value.find(value[0], 1)
                value = value[1:end] if end != -1 else value[1:]
            else:
                for marker in (" #", "\t#"):
                    if marker in value:
                        value = value.split(marker, 1)[0]
                value = value.strip()
            # U+FFFD only appears where bytes failed to decode, so the value is
            # corrupt and cannot be a real key — keep looking rather than send
            # garbage as a bearer token.
            if value and "�" not in value:
                return value
    return ""


class TwitterClient:
    """AIsa Twitter/X API client with explicit request accounting."""

    BASE_URL = "https://api.aisa.one/apis/v1"

    def __init__(self, api_key: Optional[str] = None, *, budget=None, quote_only: bool = False):
        """Initialize the client with an API key."""
        self.budget = budget
        self.quote_only = quote_only
        self.api_key = api_key or _resolve_aisa_api_key()
        if not self.api_key:
            raise ValueError(
                "AISA_API_KEY is required. Set the environment variable or add\n"
                "AISA_API_KEY=<key> to ~/.aisa/credentials."
            )

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send one quoted/accounted request; preserve provider data and costs."""
        values = {}
        for name, value in (params or {}).items():
            if value is None or (name == "cursor" and value == ""):
                continue
            if isinstance(value, str) and not value.strip():
                raise ValueError(f"{name} must not be blank")
            values[name] = value
        url = f"{self.BASE_URL}{endpoint}"
        if values:
            url += "?" + urllib.parse.urlencode(values)
        return aisa_transport.request(
            method, url, self.api_key, json_data=data, timeout=REQUEST_TIMEOUT,
            budget=self.budget, quote_only=self.quote_only,
        )

    # ==================== User Read APIs ====================

    def user_info(self, username: str) -> Dict[str, Any]:
        """Get Twitter user information by username."""
        return self._request("GET", "/twitter/user/info", params={"userName": username})

    def user_about(self, username: str) -> Dict[str, Any]:
        """Get user profile about page (account country, verification, etc.)."""
        return self._request("GET", "/twitter/user_about", params={"userName": username})

    def batch_user_info(self, user_ids: str) -> Dict[str, Any]:
        """Batch get user info by comma-separated user IDs."""
        return self._request("GET", "/twitter/user/batch_info_by_ids", params={"userIds": user_ids})

    def user_tweets(self, username: str, cursor: str = None) -> Dict[str, Any]:
        """Get latest tweets from a specific user."""
        return self._request("GET", "/twitter/user/last_tweets", params={"userName": username, "cursor": cursor})

    def user_mentions(self, username: str, cursor: str = None) -> Dict[str, Any]:
        """Get mentions of a user."""
        self._check_unverified_cursor(cursor, "mentions")
        return self._request("GET", "/twitter/user/mentions", params={"userName": username})

    def followers(self, username: str, cursor: str = None) -> Dict[str, Any]:
        """Get user followers."""
        return self._request("GET", "/twitter/user/followers", params={"userName": username, "cursor": cursor})

    def followings(self, username: str, cursor: str = None) -> Dict[str, Any]:
        """Get user followings."""
        return self._request("GET", "/twitter/user/followings", params={"userName": username, "cursor": cursor})

    def verified_followers(self, user_id: str, cursor: str = None) -> Dict[str, Any]:
        """Get verified followers of a user (requires user_id, not username)."""
        return self._request("GET", "/twitter/user/verifiedFollowers", params={"user_id": user_id, "cursor": cursor})

    def check_follow_relationship(self, source: str, target: str) -> Dict[str, Any]:
        """Check follow relationship between two users."""
        return self._request(
            "GET",
            "/twitter/user/check_follow_relationship",
            params={"source_user_name": source, "target_user_name": target},
        )

    def user_search(self, query: str, cursor: str = None) -> Dict[str, Any]:
        """Search for Twitter users by keyword."""
        self._check_unverified_cursor(cursor, "user-search")
        return self._request("GET", "/twitter/user/search", params={"query": query})

    # ==================== Tweet Read APIs ====================

    def search(self, query: str, query_type: str = "Latest", cursor: str = None) -> Dict[str, Any]:
        """Search for tweets matching a query."""
        self._check_query_type(query_type)
        return self._request(
            "GET",
            "/twitter/tweet/advanced_search",
            params={"query": query, "queryType": query_type, "cursor": cursor},
        )

    def tweet_detail(self, tweet_ids: str) -> Dict[str, Any]:
        """Get detailed information about tweets by IDs (comma-separated)."""
        return self._request("GET", "/twitter/tweets", params={"tweet_ids": tweet_ids})

    def tweet_replies(self, tweet_id: str, cursor: str = None) -> Dict[str, Any]:
        """Get replies to a tweet."""
        return self._request("GET", "/twitter/tweet/replies", params={"tweetId": tweet_id, "cursor": cursor})

    def tweet_quotes(self, tweet_id: str, cursor: str = None) -> Dict[str, Any]:
        """Get quotes of a tweet."""
        self._check_unverified_cursor(cursor, "quotes")
        return self._request("GET", "/twitter/tweet/quotes", params={"tweetId": tweet_id})

    def tweet_retweeters(self, tweet_id: str, cursor: str = None) -> Dict[str, Any]:
        """Get retweeters of a tweet."""
        return self._request("GET", "/twitter/tweet/retweeters", params={"tweetId": tweet_id, "cursor": cursor})

    def tweet_thread(self, tweet_id: str, cursor: str = None) -> Dict[str, Any]:
        """Get the full thread context of a tweet."""
        return self._request("GET", "/twitter/tweet/thread_context", params={"tweetId": tweet_id, "cursor": cursor})

    def article(self, tweet_id: str) -> Dict[str, Any]:
        """Get article content by tweet ID."""
        return self._request("GET", "/twitter/article", params={"tweet_id": tweet_id})

    # ==================== Trends, Lists, Communities, Spaces ====================

    def trends(self, woeid: int = 1) -> Dict[str, Any]:
        """Get current Twitter trending topics by WOEID (1 = worldwide)."""
        if type(woeid) is not int or woeid < 1:
            raise ValueError("woeid must be a positive integer")
        return self._request("GET", "/twitter/trends", params={"woeid": woeid})

    def list_members(self, list_id: str, cursor: str = None) -> Dict[str, Any]:
        """Get members of a Twitter list."""
        return self._request("GET", "/twitter/list/members", params={"list_id": list_id, "cursor": cursor})

    def list_followers(self, list_id: str, cursor: str = None) -> Dict[str, Any]:
        """Get followers of a Twitter list."""
        return self._request("GET", "/twitter/list/followers", params={"list_id": list_id, "cursor": cursor})

    def community_info(self, community_id: str) -> Dict[str, Any]:
        """Get community info by ID."""
        return self._request("GET", "/twitter/community/info", params={"community_id": community_id})

    def community_members(self, community_id: str, cursor: str = None) -> Dict[str, Any]:
        """Get community members."""
        return self._request(
            "GET", "/twitter/community/members", params={"community_id": community_id, "cursor": cursor}
        )

    def community_moderators(self, community_id: str, cursor: str = None) -> Dict[str, Any]:
        """Get community moderators."""
        return self._request(
            "GET", "/twitter/community/moderators", params={"community_id": community_id, "cursor": cursor}
        )

    def community_tweets(self, community_id: str, cursor: str = None) -> Dict[str, Any]:
        """Get community tweets."""
        return self._request(
            "GET", "/twitter/community/tweets", params={"community_id": community_id, "cursor": cursor}
        )

    def community_search(self, query: str, cursor: str = None, query_type: str = "Latest") -> Dict[str, Any]:
        """Search tweets from all communities."""
        self._check_query_type(query_type)
        return self._request(
            "GET",
            "/twitter/community/get_tweets_from_all_community",
            params={"query": query, "queryType": query_type, "cursor": cursor},
        )

    def space_detail(self, space_id: str) -> Dict[str, Any]:
        """Get Space detail by ID."""
        return self._request("GET", "/twitter/spaces/detail", params={"space_id": space_id})

    @staticmethod
    def _check_query_type(query_type: str) -> None:
        if query_type not in {"Latest", "Top"}:
            raise ValueError("query type must be Latest or Top")

    @staticmethod
    def _check_unverified_cursor(cursor: Optional[str], command: str) -> None:
        if cursor:
            raise ValueError(f"{command} cursor support is not declared by the current API contract; no request sent")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AIsa Twitter/X read APIs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    aisa_transport.add_cost_arguments(parser)
    parser.set_defaults(quote=False)
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # ---- User Read Commands ----

    p = subparsers.add_parser("user-info", help="Get user information")
    p.add_argument("--username", "-u", required=True)

    p = subparsers.add_parser("user-about", help="Get user profile about")
    p.add_argument("--username", "-u", required=True)

    p = subparsers.add_parser("batch-users", help="Batch get users by IDs")
    p.add_argument("--user-ids", required=True, help="Comma-separated user IDs")

    p = subparsers.add_parser("tweets", help="Get user's latest tweets")
    p.add_argument("--username", "-u", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("mentions", help="Get user mentions")
    p.add_argument("--username", "-u", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("followers", help="Get user followers")
    p.add_argument("--username", "-u", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("followings", help="Get user followings")
    p.add_argument("--username", "-u", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("verified-followers", help="Get verified followers")
    p.add_argument("--user-id", required=True, help="User ID (not username)")
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("check-follow", help="Check follow relationship")
    p.add_argument("--source", required=True, help="Source username")
    p.add_argument("--target", required=True, help="Target username")

    # ---- Search & Discovery ----

    p = subparsers.add_parser("search", help="Search tweets")
    p.add_argument("--query", "-q", required=True)
    p.add_argument("--type", "-t", choices=["Latest", "Top"], default="Latest")
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("user-search", help="Search users")
    p.add_argument("--query", "-q", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("trends", help="Get trending topics")
    p.add_argument("--woeid", "-w", type=int, default=1)

    # ---- Tweet Detail Commands ----

    p = subparsers.add_parser("detail", help="Get tweets by IDs")
    p.add_argument("--tweet-ids", required=True, help="Comma-separated tweet IDs")

    p = subparsers.add_parser("replies", help="Get tweet replies")
    p.add_argument("--tweet-id", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("quotes", help="Get tweet quotes")
    p.add_argument("--tweet-id", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("retweeters", help="Get tweet retweeters")
    p.add_argument("--tweet-id", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("thread", help="Get tweet thread context")
    p.add_argument("--tweet-id", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("article", help="Get article by tweet ID")
    p.add_argument("--tweet-id", required=True)

    # ---- List Commands ----

    p = subparsers.add_parser("list-members", help="Get list members")
    p.add_argument("--list-id", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("list-followers", help="Get list followers")
    p.add_argument("--list-id", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    # ---- Community Commands ----

    p = subparsers.add_parser("community-info", help="Get community info")
    p.add_argument("--community-id", required=True)

    p = subparsers.add_parser("community-members", help="Get community members")
    p.add_argument("--community-id", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("community-moderators", help="Get community moderators")
    p.add_argument("--community-id", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("community-tweets", help="Get community tweets")
    p.add_argument("--community-id", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("community-search", help="Search all community tweets")
    p.add_argument("--query", "-q", required=True)
    p.add_argument("--type", "-t", choices=["Latest", "Top"], default="Latest")
    p.add_argument("--cursor", help="Pagination cursor")

    # ---- Spaces ----

    p = subparsers.add_parser("space-detail", help="Get Space detail")
    p.add_argument("--space-id", required=True)

    for command_parser in subparsers.choices.values():
        aisa_transport.add_cost_arguments(command_parser)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        return _run_command(args)
    except (ValueError, costs.CostControlError, OSError) as exc:
        print(json.dumps({"success": False, "ok": False, "error": {"code": "INPUT_OR_COST_ERROR", "message": str(exc)}}))
        return 1


def _run_command(args):
    # Validate command input before loading credentials, creating a ledger, or I/O.
    if args.command in {"mentions", "user-search", "quotes"}:
        TwitterClient._check_unverified_cursor(getattr(args, "cursor", None), args.command)
    for name in ("username", "query", "user_id", "user_ids", "tweet_id", "tweet_ids",
                 "list_id", "community_id", "space_id", "source", "target"):
        value = getattr(args, name, None)
        if isinstance(value, str) and not value.strip():
            raise ValueError(f"{name} must not be blank")
    if args.command == "trends" and args.woeid < 1:
        raise ValueError("woeid must be a positive integer")
    if args.command == "space-detail":
        raise ValueError("Space detail has no verified quote/admission capability; no request sent")
    client = TwitterClient(quote_only=args.quote)
    client.budget = aisa_transport.budget_from_args(args)

    result = None
    cmd = args.command

    if cmd == "user-info":
        result = client.user_info(args.username)
    elif cmd == "user-about":
        result = client.user_about(args.username)
    elif cmd == "batch-users":
        result = client.batch_user_info(args.user_ids)
    elif cmd == "tweets":
        result = client.user_tweets(args.username, getattr(args, "cursor", None))
    elif cmd == "mentions":
        result = client.user_mentions(args.username, getattr(args, "cursor", None))
    elif cmd == "followers":
        result = client.followers(args.username, getattr(args, "cursor", None))
    elif cmd == "followings":
        result = client.followings(args.username, getattr(args, "cursor", None))
    elif cmd == "verified-followers":
        result = client.verified_followers(args.user_id, getattr(args, "cursor", None))
    elif cmd == "check-follow":
        result = client.check_follow_relationship(args.source, args.target)
    elif cmd == "search":
        result = client.search(args.query, args.type, getattr(args, "cursor", None))
    elif cmd == "user-search":
        result = client.user_search(args.query, getattr(args, "cursor", None))
    elif cmd == "trends":
        result = client.trends(args.woeid)
    elif cmd == "detail":
        result = client.tweet_detail(args.tweet_ids)
    elif cmd == "replies":
        result = client.tweet_replies(args.tweet_id, getattr(args, "cursor", None))
    elif cmd == "quotes":
        result = client.tweet_quotes(args.tweet_id, getattr(args, "cursor", None))
    elif cmd == "retweeters":
        result = client.tweet_retweeters(args.tweet_id, getattr(args, "cursor", None))
    elif cmd == "thread":
        result = client.tweet_thread(args.tweet_id, getattr(args, "cursor", None))
    elif cmd == "article":
        result = client.article(args.tweet_id)
    elif cmd == "list-members":
        result = client.list_members(args.list_id, getattr(args, "cursor", None))
    elif cmd == "list-followers":
        result = client.list_followers(args.list_id, getattr(args, "cursor", None))
    elif cmd == "community-info":
        result = client.community_info(args.community_id)
    elif cmd == "community-members":
        result = client.community_members(args.community_id, getattr(args, "cursor", None))
    elif cmd == "community-moderators":
        result = client.community_moderators(args.community_id, getattr(args, "cursor", None))
    elif cmd == "community-tweets":
        result = client.community_tweets(args.community_id, getattr(args, "cursor", None))
    elif cmd == "community-search":
        result = client.community_search(args.query, getattr(args, "cursor", None), args.type)
    elif cmd == "space-detail":
        result = client.space_detail(args.space_id)

    output = json.dumps(result, indent=2, ensure_ascii=False)
    try:
        print(output)
    except UnicodeEncodeError:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    return 1 if aisa_transport.is_failure(result) else 0


if __name__ == "__main__":
    raise SystemExit(main())
