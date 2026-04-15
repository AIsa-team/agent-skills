#!/usr/bin/env python3
"""
OpenClaw Twitter - AIsa API Client
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
import unicodedata
from typing import Any, Dict, List, Optional


DEFAULT_RELAY_TIMEOUT = 30
TWITTER_MAX_WEIGHT = 280
TWITTER_URL_WEIGHT = 23
URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)


class TwitterClient:
    """OpenClaw Twitter - Twitter/X API Client."""

    BASE_URL = "https://api.aisa.one/apis/v1"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the client with an API key."""
        self.api_key = api_key or os.environ.get("AISA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "AISA_API_KEY is required. Set it via environment variable or pass to constructor."
            )

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the AIsa API."""
        url = f"{self.BASE_URL}{endpoint}"

        if params:
            query_string = urllib.parse.urlencode(
                {k: v for k, v in params.items() if v is not None}
            )
            url = f"{url}?{query_string}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "OpenClaw-Twitter/1.0",
        }

        request_data = None
        if method == "POST":
            request_data = json.dumps(data or {}).encode("utf-8")

        req = urllib.request.Request(url, data=request_data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            try:
                return json.loads(error_body)
            except json.JSONDecodeError:
                return {"success": False, "error": {"code": str(e.code), "message": error_body}}
        except urllib.error.URLError as e:
            return {"success": False, "error": {"code": "NETWORK_ERROR", "message": str(e.reason)}}

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
        return self._request("GET", "/twitter/user/mentions", params={"userName": username, "cursor": cursor})

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
        return self._request("GET", "/twitter/user/search", params={"query": query, "cursor": cursor})

    # ==================== Tweet Read APIs ====================

    def search(self, query: str, query_type: str = "Latest", cursor: str = None) -> Dict[str, Any]:
        """Search for tweets matching a query."""
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
        return self._request("GET", "/twitter/tweet/quotes", params={"tweetId": tweet_id, "cursor": cursor})

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

    def community_search(self, query: str, cursor: str = None) -> Dict[str, Any]:
        """Search tweets from all communities."""
        return self._request(
            "GET",
            "/twitter/community/get_tweets_from_all_community",
            params={"query": query, "cursor": cursor},
        )

    def space_detail(self, space_id: str) -> Dict[str, Any]:
        """Get Space detail by ID."""
        return self._request("GET", "/twitter/spaces/detail", params={"space_id": space_id})



def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="OpenClaw Twitter - Twitter/X read APIs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

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
    p.add_argument("--cursor", help="Pagination cursor")

    # ---- Spaces ----

    p = subparsers.add_parser("space-detail", help="Get Space detail")
    p.add_argument("--space-id", required=True)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        client = TwitterClient()
    except ValueError as e:
        print(json.dumps({"success": False, "error": {"code": "AUTH_ERROR", "message": str(e)}}))
        sys.exit(1)

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
        result = client.community_search(args.query, getattr(args, "cursor", None))
    elif cmd == "space-detail":
        result = client.space_detail(args.space_id)

    if result:
        output = json.dumps(result, indent=2, ensure_ascii=False)
        try:
            print(output)
        except UnicodeEncodeError:
            print(json.dumps(result, indent=2, ensure_ascii=True))
        sys.exit(0 if result.get("success", True) else 1)


if __name__ == "__main__":
    main()
