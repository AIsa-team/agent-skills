#!/usr/bin/env python3
"""
Twitter engagement client for local like/unlike/follow/unfollow relay actions.

Commands:
    python twitter_engagement_client.py list-tweets --user "@elonmusk" --limit 10
    python twitter_engagement_client.py like-latest --user "@elonmusk"
    python twitter_engagement_client.py unlike-latest --user "@elonmusk"
    python twitter_engagement_client.py like-tweet --tweet-id 123 --label "Tweet #2" --username elonmusk
    python twitter_engagement_client.py unlike-tweet --tweet-id 123 --label "Tweet #2" --username elonmusk
    python twitter_engagement_client.py follow-user --user "@elonmusk"
    python twitter_engagement_client.py unfollow-user --user "@elonmusk"
    python twitter_engagement_client.py follow-user-id --target-user-id 44196397 --username elonmusk
    python twitter_engagement_client.py unfollow-user-id --target-user-id 44196397 --username elonmusk
    python twitter_engagement_client.py status
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, Optional

from twitter_client import TwitterClient
from twitter_oauth_client import RelayConfigError, load_config, send_json_request


MAX_LIST_LIMIT = 20
DEFAULT_LIST_LIMIT = 10


def is_success_response(payload: Dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return False
    status = str(payload.get("status", "")).lower()
    if status == "success":
        return True
    if payload.get("success") is True:
        return True
    code = payload.get("code")
    return code in {0, 200}


def emit_json(payload: Dict[str, Any]) -> None:
    output = json.dumps(payload, indent=2, ensure_ascii=False)
    try:
        print(output)
    except UnicodeEncodeError:
        print(json.dumps(payload, indent=2, ensure_ascii=True))


def fail(message: str, *, action: str, target: Optional[Dict[str, Any]] = None, **extra: Any) -> None:
    response = {
        "ok": False,
        "action": action,
        "message": message,
    }
    if target is not None:
        response["target"] = target
    response.update(extra)
    emit_json(response)
    sys.exit(1)


def build_target(kind: str, value: str, **extra: Any) -> Dict[str, Any]:
    target = {"type": kind, "value": value}
    target.update({key: val for key, val in extra.items() if val not in (None, "")})
    return target


def normalize_user_input(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise RelayConfigError("User must not be empty.")
    if normalized.startswith("@"):
        normalized = normalized[1:]
    return normalized.strip()


def normalize_for_match(value: Optional[str]) -> str:
    return (value or "").strip().casefold()


def extract_resolved_user_from_info(response: Dict[str, Any]) -> Optional[Dict[str, str]]:
    data = response.get("data") if isinstance(response, dict) else None
    if not isinstance(data, dict):
        return None
    user_id = str(data.get("id") or "").strip()
    username = str(data.get("userName") or data.get("screen_name") or "").strip()
    display_name = str(data.get("name") or username or user_id).strip()
    if not user_id or not username:
        return None
    return {
        "user_id": user_id,
        "username": username,
        "display_name": display_name,
    }


def score_user_candidate(query: str, candidate: Dict[str, Any]) -> int:
    normalized_query = normalize_for_match(query)
    screen_name = normalize_for_match(candidate.get("screen_name") or candidate.get("userName") or candidate.get("username"))
    display_name = normalize_for_match(candidate.get("name"))

    score = 0
    if normalized_query == screen_name:
        score = max(score, 400)
    if normalized_query == display_name:
        score = max(score, 350)
    if screen_name.startswith(normalized_query) and normalized_query:
        score = max(score, 250)
    if display_name.startswith(normalized_query) and normalized_query:
        score = max(score, 225)
    if normalized_query and normalized_query in screen_name:
        score = max(score, 150)
    if normalized_query and normalized_query in display_name:
        score = max(score, 125)
    if candidate.get("verified") or candidate.get("isBlueVerified"):
        score += 10
    return score


def candidate_summary(candidate: Dict[str, Any]) -> Dict[str, str]:
    username = str(candidate.get("screen_name") or candidate.get("userName") or candidate.get("username") or "").strip()
    display_name = str(candidate.get("name") or username).strip()
    user_id = str(candidate.get("id") or "").strip()
    return {
        "user_id": user_id,
        "username": username,
        "display_name": display_name,
        "label": f"{display_name} (@{username})" if username else display_name,
    }


def resolve_user(client: TwitterClient, raw_user: str) -> Dict[str, Any]:
    normalized_user = normalize_user_input(raw_user)
    info_result = client.user_info(normalized_user)
    if is_success_response(info_result):
        resolved = extract_resolved_user_from_info(info_result)
        if resolved:
            return {
                "ok": True,
                "mode": "direct",
                "resolved_user": resolved,
                "raw_response": info_result,
            }

    search_result = client.user_search(normalized_user)
    users = search_result.get("users") if isinstance(search_result, dict) else None
    if not is_success_response(search_result) and not isinstance(users, list):
        return {
            "ok": False,
            "message": "Target user not found. Try a different username or a more specific account name.",
            "raw_response": search_result,
            "candidates": [],
        }

    ranked: list[tuple[int, Dict[str, Any]]] = []
    for user in users or []:
        if not isinstance(user, dict):
            continue
        score = score_user_candidate(normalized_user, user)
        if score <= 0:
            continue
        ranked.append((score, user))

    ranked.sort(key=lambda item: item[0], reverse=True)
    if not ranked:
        return {
            "ok": False,
            "message": "Target user not found. Try a different username or a more specific account name.",
            "raw_response": search_result,
            "candidates": [],
        }

    top_score = ranked[0][0]
    top_group = [candidate for score, candidate in ranked if score == top_score]
    if len(top_group) > 1:
        return {
            "ok": False,
            "message": "I found multiple possible accounts. Please confirm which user you mean.",
            "raw_response": search_result,
            "candidates": [candidate_summary(item) for item in top_group[:3]],
        }

    best = ranked[0][1]
    summary = candidate_summary(best)
    if not summary["user_id"] or not summary["username"]:
        return {
            "ok": False,
            "message": "The user search result is missing required fields, so the action cannot continue right now.",
            "raw_response": search_result,
            "candidates": [summary],
        }

    return {
        "ok": True,
        "mode": "search",
        "resolved_user": {
            "user_id": summary["user_id"],
            "username": summary["username"],
            "display_name": summary["display_name"],
        },
        "raw_response": search_result,
    }


def extract_tweets(response: Dict[str, Any], limit: int) -> list[Dict[str, Any]]:
    data = response.get("data") if isinstance(response, dict) else None
    tweets = data.get("tweets") if isinstance(data, dict) else None
    items: list[Dict[str, Any]] = []
    for index, tweet in enumerate((tweets or [])[:limit], start=1):
        if not isinstance(tweet, dict):
            continue
        author = tweet.get("author") if isinstance(tweet.get("author"), dict) else {}
        tweet_id = str(tweet.get("id") or "").strip()
        if not tweet_id:
            continue
        items.append(
            {
                "index": index,
                "tweet_id": tweet_id,
                "text": str(tweet.get("text") or "").strip(),
                "created_at": str(tweet.get("createdAt") or "").strip(),
                "author_id": str(author.get("id") or "").strip(),
                "author_username": str(author.get("userName") or "").strip(),
                "author_name": str(author.get("name") or author.get("userName") or "").strip(),
                "tweet_url": str(tweet.get("url") or tweet.get("twitterUrl") or "").strip(),
            }
        )
    return items


def fetch_latest_tweets(client: TwitterClient, username: str, limit: int) -> Dict[str, Any]:
    result = client.user_tweets(username)
    if not is_success_response(result):
        return {
            "ok": False,
            "message": "Tweet lookup failed. Please try again later.",
            "raw_response": result,
            "tweets": [],
        }
    tweets = extract_tweets(result, limit)
    if not tweets:
        return {
            "ok": False,
            "message": f"@{username} does not have any tweets available for this action right now.",
            "raw_response": result,
            "tweets": [],
        }
    return {
        "ok": True,
        "raw_response": result,
        "tweets": tweets,
    }


def relay_action(config: Dict[str, Any], endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return send_json_request(
        f"{config['base_url']}{endpoint}",
        payload,
        timeout=config["timeout"],
        aisa_api_key=config["aisa_api_key"],
    )


def format_action_message(action: str, *, username: Optional[str] = None, label: Optional[str] = None, msg: Optional[str] = None) -> str:
    username_text = f"@{username}" if username else "that user"
    label_text = label or "that tweet"
    if action == "like_latest":
        return f"Liked the latest tweet from {username_text}."
    if action == "unlike_latest":
        return f"Removed the like from the latest tweet by {username_text}."
    if action == "like_tweet":
        return f"Liked {label_text}."
    if action == "unlike_tweet":
        return f"Removed the like from {label_text}."
    if action == "follow_user":
        return f"Followed {username_text}."
    if action == "unfollow_user":
        return f"Unfollowed {username_text}."
    if action == "like_latest_failed":
        return f"Like failed: {msg or 'please try again later'}"
    if action == "unlike_latest_failed":
        return f"Unlike failed: {msg or 'please try again later'}"
    if action == "like_tweet_failed":
        return f"Like failed: {msg or 'please try again later'}"
    if action == "unlike_tweet_failed":
        return f"Unlike failed: {msg or 'please try again later'}"
    if action == "follow_user_failed":
        return f"Follow failed: {msg or 'please try again later'}"
    if action == "unfollow_user_failed":
        return f"Unfollow failed: {msg or 'please try again later'}"
    return msg or "Action completed."


def print_json(response: Dict[str, Any], exit_code: int = 0) -> None:
    emit_json(response)
    sys.exit(exit_code)


def command_list_tweets(args: argparse.Namespace) -> None:
    client = TwitterClient()
    user_resolution = resolve_user(client, args.user)
    if not user_resolution["ok"]:
        fail(
            user_resolution["message"],
            action="list_tweets",
            target=build_target("user_query", args.user),
            candidates=user_resolution.get("candidates", []),
            raw_response=user_resolution.get("raw_response"),
        )

    resolved_user = user_resolution["resolved_user"]
    tweets_result = fetch_latest_tweets(client, resolved_user["username"], args.limit)
    if not tweets_result["ok"]:
        fail(
            tweets_result["message"],
            action="list_tweets",
            target=build_target("user", resolved_user["username"], user_id=resolved_user["user_id"]),
            resolved_user=resolved_user,
            raw_response=tweets_result["raw_response"],
        )

    response = {
        "ok": True,
        "action": "list_tweets",
        "target": build_target("user", resolved_user["username"], user_id=resolved_user["user_id"]),
        "resolved_user": resolved_user,
        "tweets": tweets_result["tweets"],
        "message": f"Found {len(tweets_result['tweets'])} recent tweets from @{resolved_user['username']}.",
        "raw_response": tweets_result["raw_response"],
    }
    print_json(response)


def execute_tweet_action(
    args: argparse.Namespace,
    *,
    endpoint: str,
    action: str,
    tweet_id: str,
    username: Optional[str] = None,
    label: Optional[str] = None,
    resolved_tweet: Optional[Dict[str, Any]] = None,
) -> None:
    config = load_config(args)
    payload = {
        "aisa_api_key": config["aisa_api_key"],
        "tweet_id": tweet_id.strip(),
    }
    relay_result = relay_action(config, endpoint, payload)
    ok = relay_result.get("ok") is not False and is_success_response(relay_result)
    response = {
        "ok": ok,
        "action": action,
        "target": build_target("tweet", tweet_id, username=username, label=label),
        "message": format_action_message(
            action if ok else f"{action}_failed",
            username=username,
            label=label,
            msg=relay_result.get("msg"),
        ),
        "raw_response": relay_result,
    }
    if resolved_tweet:
        response["resolved_tweet"] = resolved_tweet
    print_json(response, exit_code=0 if ok else 1)


def execute_user_action(
    args: argparse.Namespace,
    *,
    endpoint: str,
    action: str,
    target_user_id: str,
    username: Optional[str] = None,
    resolved_user: Optional[Dict[str, Any]] = None,
) -> None:
    config = load_config(args)
    payload = {
        "aisa_api_key": config["aisa_api_key"],
        "target_user_id": target_user_id.strip(),
    }
    relay_result = relay_action(config, endpoint, payload)
    ok = relay_result.get("ok") is not False and is_success_response(relay_result)
    response = {
        "ok": ok,
        "action": action,
        "target": build_target("user", username or target_user_id, user_id=target_user_id),
        "message": format_action_message(
            action if ok else f"{action}_failed",
            username=username,
            msg=relay_result.get("msg"),
        ),
        "raw_response": relay_result,
    }
    if resolved_user:
        response["resolved_user"] = resolved_user
    print_json(response, exit_code=0 if ok else 1)


def command_like_latest(args: argparse.Namespace) -> None:
    client = TwitterClient()
    user_resolution = resolve_user(client, args.user)
    if not user_resolution["ok"]:
        fail(
            user_resolution["message"],
            action=args.command.replace("-", "_"),
            target=build_target("user_query", args.user),
            candidates=user_resolution.get("candidates", []),
            raw_response=user_resolution.get("raw_response"),
        )
    resolved_user = user_resolution["resolved_user"]
    tweets_result = fetch_latest_tweets(client, resolved_user["username"], 1)
    if not tweets_result["ok"]:
        fail(
            tweets_result["message"],
            action=args.command.replace("-", "_"),
            target=build_target("user", resolved_user["username"], user_id=resolved_user["user_id"]),
            resolved_user=resolved_user,
            raw_response=tweets_result["raw_response"],
        )
    latest_tweet = tweets_result["tweets"][0]
    execute_tweet_action(
        args,
        endpoint="/like_twitter" if args.command == "like-latest" else "/unlike_twitter",
        action="like_latest" if args.command == "like-latest" else "unlike_latest",
        tweet_id=latest_tweet["tweet_id"],
        username=resolved_user["username"],
        label="the latest tweet",
        resolved_tweet=latest_tweet,
    )


def command_like_tweet(args: argparse.Namespace) -> None:
    label = (args.label or "that tweet").strip()
    execute_tweet_action(
        args,
        endpoint="/like_twitter" if args.command == "like-tweet" else "/unlike_twitter",
        action="like_tweet" if args.command == "like-tweet" else "unlike_tweet",
        tweet_id=args.tweet_id,
        username=(args.username or "").strip() or None,
        label=label,
    )


def command_follow_user(args: argparse.Namespace) -> None:
    client = TwitterClient()
    user_resolution = resolve_user(client, args.user)
    if not user_resolution["ok"]:
        fail(
            user_resolution["message"],
            action=args.command.replace("-", "_"),
            target=build_target("user_query", args.user),
            candidates=user_resolution.get("candidates", []),
            raw_response=user_resolution.get("raw_response"),
        )
    resolved_user = user_resolution["resolved_user"]
    execute_user_action(
        args,
        endpoint="/follow_twitter" if args.command == "follow-user" else "/unfollow_twitter",
        action="follow_user" if args.command == "follow-user" else "unfollow_user",
        target_user_id=resolved_user["user_id"],
        username=resolved_user["username"],
        resolved_user=resolved_user,
    )


def command_follow_user_id(args: argparse.Namespace) -> None:
    execute_user_action(
        args,
        endpoint="/follow_twitter" if args.command == "follow-user-id" else "/unfollow_twitter",
        action="follow_user" if args.command == "follow-user-id" else "unfollow_user",
        target_user_id=args.target_user_id,
        username=(args.username or "").strip() or None,
    )


def command_status(args: argparse.Namespace) -> None:
    config = load_config(args)
    response = {
        "ok": True,
        "relay_base_url": config["base_url"],
        "aisa_api_key_present": bool(config["aisa_api_key"]),
        "timeout": config["timeout"],
        "supported_commands": [
            "list-tweets",
            "like-latest",
            "unlike-latest",
            "like-tweet",
            "unlike-tweet",
            "follow-user",
            "unfollow-user",
            "follow-user-id",
            "unfollow-user-id",
            "status",
        ],
        "supported_endpoints": [
            "/like_twitter",
            "/unlike_twitter",
            "/follow_twitter",
            "/unfollow_twitter",
        ],
    }
    print_json(response)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Twitter engagement client for local relay like/follow actions",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    list_tweets = subparsers.add_parser("list-tweets", help="List a user's latest tweets for follow-up actions")
    list_tweets.add_argument("--user", required=True, help="Twitter username or display name")
    list_tweets.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIST_LIMIT,
        help=f"How many tweets to return (1-{MAX_LIST_LIMIT}, default: {DEFAULT_LIST_LIMIT})",
    )
    list_tweets.set_defaults(func=command_list_tweets)

    like_latest = subparsers.add_parser("like-latest", help="Like the user's latest tweet")
    like_latest.add_argument("--user", required=True, help="Twitter username or display name")
    like_latest.set_defaults(func=command_like_latest)

    unlike_latest = subparsers.add_parser("unlike-latest", help="Unlike the user's latest tweet")
    unlike_latest.add_argument("--user", required=True, help="Twitter username or display name")
    unlike_latest.set_defaults(func=command_like_latest)

    like_tweet = subparsers.add_parser("like-tweet", help="Like a specific tweet ID")
    like_tweet.add_argument("--tweet-id", required=True, help="Tweet ID resolved by OpenClaw context")
    like_tweet.add_argument("--username", help="Optional username for natural-language response")
    like_tweet.add_argument("--label", help='Optional label such as "Tweet #2"')
    like_tweet.set_defaults(func=command_like_tweet)

    unlike_tweet = subparsers.add_parser("unlike-tweet", help="Unlike a specific tweet ID")
    unlike_tweet.add_argument("--tweet-id", required=True, help="Tweet ID resolved by OpenClaw context")
    unlike_tweet.add_argument("--username", help="Optional username for natural-language response")
    unlike_tweet.add_argument("--label", help='Optional label such as "Tweet #5"')
    unlike_tweet.set_defaults(func=command_like_tweet)

    follow_user = subparsers.add_parser("follow-user", help="Follow a user by username or display name")
    follow_user.add_argument("--user", required=True, help="Twitter username or display name")
    follow_user.set_defaults(func=command_follow_user)

    unfollow_user = subparsers.add_parser("unfollow-user", help="Unfollow a user by username or display name")
    unfollow_user.add_argument("--user", required=True, help="Twitter username or display name")
    unfollow_user.set_defaults(func=command_follow_user)

    follow_user_id = subparsers.add_parser("follow-user-id", help="Follow a user by resolved user ID")
    follow_user_id.add_argument("--target-user-id", required=True, help="User ID resolved by OpenClaw context")
    follow_user_id.add_argument("--username", help="Optional username for natural-language response")
    follow_user_id.set_defaults(func=command_follow_user_id)

    unfollow_user_id = subparsers.add_parser("unfollow-user-id", help="Unfollow a user by resolved user ID")
    unfollow_user_id.add_argument("--target-user-id", required=True, help="User ID resolved by OpenClaw context")
    unfollow_user_id.add_argument("--username", help="Optional username for natural-language response")
    unfollow_user_id.set_defaults(func=command_follow_user_id)

    status = subparsers.add_parser("status", help="Show current relay engagement configuration")
    status.set_defaults(func=command_status)

    return parser


def validate_args(args: argparse.Namespace) -> None:
    if getattr(args, "limit", DEFAULT_LIST_LIMIT) < 1:
        raise RelayConfigError("--limit must be at least 1.")
    if getattr(args, "limit", DEFAULT_LIST_LIMIT) > MAX_LIST_LIMIT:
        raise RelayConfigError(f"--limit must be at most {MAX_LIST_LIMIT}.")
    if getattr(args, "tweet_id", None) is not None and not str(args.tweet_id).strip():
        raise RelayConfigError("--tweet-id must not be empty.")
    if getattr(args, "target_user_id", None) is not None and not str(args.target_user_id).strip():
        raise RelayConfigError("--target-user-id must not be empty.")


def main() -> None:
    parser = build_parser()
    try:
        args = parser.parse_args()
        validate_args(args)
        args.func(args)
    except (RelayConfigError, ValueError) as exc:
        emit_json({"ok": False, "error": str(exc)})
        sys.exit(1)


if __name__ == "__main__":
    main()
