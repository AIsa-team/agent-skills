"""Offline regressions for OAuth, explicit threads, and upload-then-post flows."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "twitter_oauth_client.py"
SPEC = importlib.util.spec_from_file_location("twitter_oauth_under_test", SCRIPT)
oauth = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oauth)
CONTRACTS = json.loads((ROOT / "tests" / "fixtures" / "provider_contracts.json").read_text())["operations"]
KEY = "test-placeholder-key"


class OAuthTests(unittest.TestCase):
    def setUp(self):
        self.budget = object()
        self.config = {"base_url": oauth.DEFAULT_BASE_URL, "aisa_api_key": KEY,
                       "timeout": 30, "budget": self.budget, "quote_only": False}

    def args(self, *arguments):
        return oauth.build_parser().parse_args(arguments)

    def command(self, *arguments, result=None, quote_only=False):
        config = {**self.config, "quote_only": quote_only}
        stdout = io.StringIO()
        args = self.args(*arguments)
        with patch.object(oauth, "load_config", return_value=config), \
             patch.object(oauth.get_transport(), "request", return_value=result) as request, \
             contextlib.redirect_stdout(stdout):
            code = 0
            try:
                args.func(args)
            except SystemExit as exc:
                code = exc.code
        return code, json.loads(stdout.getvalue()), request

    def test_current_and_legacy_authorization_success(self):
        example = CONTRACTS["authorize"]["response"]["example"]
        for result in (example, {"code": 200, "data": {"auth_url": example["auth_url"]}}):
            with self.subTest(result=result):
                code, output, request = self.command("authorize", result=result)
                self.assertEqual(code, 0)
                self.assertTrue(output["ok"])
                self.assertEqual(output["authorization_url"], example["auth_url"])
                self.assertNotIn(KEY, json.dumps(output))
                call = request.call_args
                self.assertEqual(call.args, ("POST", CONTRACTS["authorize"]["url"], KEY))
                self.assertEqual(call.kwargs["json_data"]["aisa_api_key"], KEY)
                self.assertEqual(call.kwargs["json_data"]["scopes"], ["tweet.read", "tweet.write", "users.read"])

    def test_media_scope_is_explicit_and_custom_scopes_are_preserved(self):
        result = CONTRACTS["authorize"]["response"]["example"]
        _, _, request = self.command("authorize", "--media", result=result)
        self.assertEqual(request.call_args.kwargs["json_data"]["scopes"],
                         ["tweet.read", "tweet.write", "users.read", "media.write"])
        _, _, request = self.command("authorize", "--scope", "tweet.read", result=result)
        self.assertEqual(request.call_args.kwargs["json_data"]["scopes"], ["tweet.read"])

    def test_authorization_failure_and_missing_url_never_open_browser(self):
        for result in ({"success": False, "error": {"code": 401}}, {"code": 200, "data": []},
                       {"auth_url": "javascript:alert(1)"}):
            with self.subTest(result=result), patch.object(oauth.webbrowser, "open") as browser:
                code, output, _ = self.command("authorize", "--open-browser", result=result)
                self.assertEqual(code, 1)
                self.assertFalse(output["ok"] if "ok" in output else output["success"])
                browser.assert_not_called()

    def test_authorize_quote_does_not_start_oauth_or_browser(self):
        with patch.object(oauth.webbrowser, "open") as browser:
            code, output, request = self.command("authorize", "--quote", quote_only=True,
                                                  result={"object": "cost_estimate"})
            self.assertEqual(code, 0)
            self.assertFalse(output["authorization_requested"])
            self.assertTrue(request.call_args.kwargs["quote_only"])
            browser.assert_not_called()

    def test_nested_and_encoded_secret_echoes_are_redacted(self):
        result = {"ok": False, "error": {"message": "Bearer " + KEY},
                  "provider_response": {"aisa_api_key": KEY, "nested": [KEY]}}
        code, output, _ = self.command("authorize", result=result)
        self.assertEqual(code, 1)
        self.assertNotIn(KEY, json.dumps(output))

    def test_parse_response_rejects_nonobjects_and_http_failures(self):
        for body in ("", "not-json", "[]", "null", "1", '"ok"'):
            with self.subTest(body=body):
                self.assertTrue(oauth.response_failed(oauth.parse_response_body(body, 200, "ok")))
        parsed = oauth.parse_response_body('{"code":200}', 401, "Unauthorized")
        self.assertTrue(oauth.response_failed(parsed))

    def test_json_and_multipart_delegate_to_single_transport_request(self):
        failure = {"ok": False, "success": False, "error": {"code": "NETWORK_ERROR"}}
        transport = oauth.get_transport()
        with patch.object(transport, "request", return_value=failure) as request:
            self.assertEqual(oauth.send_json_request(CONTRACTS["post"]["url"], {"content": "x"}, 30, KEY,
                                                    budget=self.budget), failure)
            request.assert_called_once()
            self.assertIs(request.call_args.kwargs["budget"], self.budget)
        media = {"field_name": "media_files", "filename": "x.png", "content_type": "image/png", "content": b"png"}
        with patch.object(transport, "request", return_value=failure) as request:
            self.assertEqual(oauth.send_multipart_request(CONTRACTS["upload-media"]["url"], {}, [media], 30, KEY,
                                                         budget=self.budget), failure)
            request.assert_called_once()
            self.assertIn(b'name="media_files"', request.call_args.kwargs["data"])

    def test_single_post_uses_current_json_fields_and_never_prints_key(self):
        code, output, request = self.command("post", "--text", "Hello", result={"code": 200, "data": {"tweet_id": "123"}})
        self.assertEqual(code, 0)
        self.assertEqual(output["confirmed_posts"], 1)
        self.assertNotIn(KEY, json.dumps(output))
        payload = request.call_args.kwargs["json_data"]
        self.assertEqual(payload, {"aisa_api_key": KEY, "content": "Hello"})
        self.assertTrue(set(payload) <= set(CONTRACTS["post"]["request"]["json_fields"]))

    def test_oversized_content_requires_thread_before_credentials_or_network(self):
        for text in ("a" * 281, "中" * 141, "https://example.com/" + "a" * 280):
            with self.subTest(text=text), patch.object(oauth, "load_config") as config, \
                 patch.object(oauth.get_transport(), "request") as request:
                with self.assertRaisesRegex(oauth.RelayConfigError, "single-post limit"):
                    oauth.command_post(self.args("post", "--text", text))
                config.assert_not_called()
                request.assert_not_called()

    def test_dry_run_has_no_credential_reads_network_or_ledger(self):
        with tempfile.TemporaryDirectory() as temporary:
            image = Path(temporary) / "image.png"
            image.write_bytes(b"local fixture")
            stdout = io.StringIO()
            with patch.object(oauth, "_resolve_aisa_api_key", side_effect=AssertionError("credentials read")), \
                 patch.object(oauth.get_transport(), "request", side_effect=AssertionError("network request")), \
                 patch.object(oauth.get_transport(), "budget_from_args", side_effect=AssertionError("ledger accessed")), \
                 contextlib.redirect_stdout(stdout):
                oauth.command_post(self.args("post", "--text", "a" * 281, "--thread", "--dry-run", "--media-file", str(image)))
            output = json.loads(stdout.getvalue())
            self.assertEqual(output["network_requests"], 0)
            self.assertEqual(output["total_chunks"], 2)
            self.assertEqual(output["chunks"][1]["relationship"], "reply")
            self.assertEqual(output["uploads"][0]["size_bytes"], len(b"local fixture"))

    def test_thread_first_quote_then_only_replies_and_first_media(self):
        with patch.object(oauth, "post_single_tweet", side_effect=[
            {"code": 200, "data": {"tweet_id": "101"}},
            {"code": 200, "data": {"id": "102"}},
            {"data": {"id": "103"}},
        ]) as post:
            result = oauth.publish_chunks(self.config, ["a", "b", "c"], media_ids=["55"],
                                           initial_parent_tweet_id="100", post_type="quote")
        self.assertTrue(result["ok"])
        self.assertEqual([call.kwargs["post_type"] for call in post.call_args_list], ["quote", "reply", "reply"])
        self.assertEqual([call.kwargs["parent_tweet_id"] for call in post.call_args_list], ["100", "101", "102"])
        self.assertEqual([call.kwargs["media_ids"] for call in post.call_args_list], [["55"], None, None])

    def test_partial_failure_and_missing_id_stop_without_replay(self):
        for failure in ({"ok": False, "success": False, "error": {"code": "NETWORK_ERROR"}},
                        {"code": 200, "data": {}}, []):
            with self.subTest(failure=failure), patch.object(oauth, "post_single_tweet", side_effect=[
                {"code": 200, "data": {"tweet_id": "101"}}, failure,
            ]) as post:
                result = oauth.publish_chunks(self.config, ["a", "b", "c"])
                self.assertFalse(result["ok"])
                self.assertEqual(result["confirmed_posts"], 1)
                self.assertEqual(result["failed_at_chunk"], 2)
                self.assertEqual(post.call_count, 2)
                self.assertNotIn(KEY, json.dumps(result))

    def test_quote_url_requires_complete_status_path(self):
        self.assertEqual(oauth.extract_tweet_id_from_url("https://x.com/name/status/123?s=20"), "123")
        self.assertEqual(oauth.extract_tweet_id_from_url("https://twitter.com/i/web/status/123"), "123")
        for value in ("https://x.com/name/status/123junk", "https://x.com/name/status/123/extra",
                      "https://x.com.evil.test/name/status/123", "https://x.com/name/status/１２３"):
            with self.subTest(value=value), self.assertRaises(oauth.RelayConfigError):
                oauth.extract_tweet_id_from_url(value)

    def test_invalid_inputs_fail_before_credentials_or_network(self):
        cases = [("--text", ""), ("--text", "x", "--media-id", "invalid"),
                 ("--text", "x", "--media-id", "123", "--media-file", "does-not-need-to-exist.png"),
                 ("--text", "x", "--type", "quote"),
                 ("--text", "x", "--media-id", "1", "--media-id", "2", "--media-id", "3", "--media-id", "4", "--media-id", "5"),
                 ("--text", "x", "--in-reply-to-tweet-id", "abc"),
                 ("--text", "x", "--quote-tweet-url", "https://x.com/u/status/123", "--media-id", "123"),
                 ("--text", "x", "--dry-run", "--quote")]
        for arguments in cases:
            with self.subTest(arguments=arguments), patch.object(oauth, "load_config") as config:
                with self.assertRaises(oauth.RelayConfigError):
                    oauth.command_post(self.args("post", *arguments))
                config.assert_not_called()

    def test_reply_without_parent_cannot_become_a_top_level_post(self):
        for mode in ([], ["--dry-run"], ["--quote"], ["--thread"]):
            with self.subTest(mode=mode), patch.object(oauth, "load_config") as config, \
                    patch.object(oauth, "publish_chunks") as publish:
                with self.assertRaisesRegex(oauth.RelayConfigError, "requires --in-reply-to-tweet-id"):
                    oauth.command_post(self.args("post", "--text", "A reply", "--type", "reply", *mode))
                config.assert_not_called()
                publish.assert_not_called()

    def test_cost_flags_are_accepted_before_and_after_command(self):
        before = self.args("--quote", "authorize")
        after = self.args("authorize", "--quote")
        self.assertTrue(before.quote)
        self.assertTrue(after.quote)

    def test_quote_only_thread_is_explicitly_partial_and_never_publishes(self):
        code, output, request = self.command("post", "--text", "a" * 281, "--thread", "--quote",
                                              result={"object": "cost_estimate"}, quote_only=True)
        self.assertEqual(code, 0)
        self.assertFalse(output["post_attempted"])
        self.assertTrue(output["partial_quote"])
        self.assertEqual(output["remaining_chunks_unquoted"], 1)
        request.assert_called_once()
        self.assertTrue(request.call_args.kwargs["quote_only"])

    def test_upload_then_post_uses_media_ids_and_shared_budget(self):
        with tempfile.TemporaryDirectory() as temporary:
            image = Path(temporary) / "image.png"
            image.write_bytes(b"image fixture")
            args = self.args("post", "--text", "Hello", "--media-file", str(image))
            stdout = io.StringIO()
            results = [CONTRACTS["upload-media"]["response"]["example"], {"code": 200, "data": {"tweet_id": "123"}}]
            with patch.object(oauth, "load_config", return_value=self.config), \
                 patch.object(oauth.get_transport(), "request", side_effect=results) as request, \
                 contextlib.redirect_stdout(stdout):
                oauth.command_post(args)
            self.assertTrue(json.loads(stdout.getvalue())["ok"])
            upload_call, post_call = request.call_args_list
            self.assertEqual(upload_call.args[1], CONTRACTS["upload-media"]["url"])
            self.assertEqual(post_call.args[1], CONTRACTS["post"]["url"])
            self.assertEqual(post_call.kwargs["json_data"]["media_ids"], ["2099415764780605440"])
            self.assertNotIn("media_files", post_call.kwargs["json_data"])
            self.assertIs(upload_call.kwargs["budget"], self.budget)
            self.assertIs(post_call.kwargs["budget"], self.budget)

    def test_unconfirmed_upload_prevents_post(self):
        media = {"field_name": "media_files", "filename": "x.png", "content_type": "image/png", "content": b"x"}
        for response in ({"ok": False, "error": {"code": "NETWORK_ERROR"}}, {"data": {}}):
            with self.subTest(response=response), patch.object(oauth, "send_multipart_request", return_value=response) as upload:
                result = oauth.upload_media(self.config, [media, media])
                self.assertFalse(result["ok"])
                self.assertFalse(result["post_attempted"])
                upload.assert_called_once()

    def test_media_quotes_report_post_cost_as_unknown(self):
        with tempfile.TemporaryDirectory() as temporary:
            image = Path(temporary) / "image.png"
            image.write_bytes(b"image fixture")
            code, output, request = self.command("post", "--media-file", str(image), "--quote",
                                                  result={"object": "cost_estimate"}, quote_only=True)
            self.assertEqual(code, 0)
            self.assertTrue(output["partial_quote"])
            self.assertEqual(output["unquoted_posts"], 1)
            self.assertFalse(output["post_attempted"])
            request.assert_called_once()
            self.assertEqual(request.call_args.args[1], CONTRACTS["upload-media"]["url"])

    def test_multipart_sanitizes_control_characters_and_keeps_unicode_filename(self):
        media = {"field_name": "media_files", "filename": '图像\r\nX-Bad: yes".png',
                 "content_type": "image/png", "content": b"image"}
        body, _ = oauth.encode_multipart_form_data({}, [media])
        self.assertNotIn(b"\r\nX-Bad:", body)
        self.assertIn(b"filename*=UTF-8''%E5%9B%BE", body)
        self.assertEqual(body.count(b'name="media_files"'), 1)

    def test_media_validation_and_path_deduplication(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image, video, empty = root / "a.png", root / "b.mp4", root / "empty.png"
            image.write_bytes(b"image")
            video.write_bytes(b"video")
            empty.write_bytes(b"")
            self.assertEqual(len(oauth.load_media_files([str(image), str(root / "." / "a.png")])), 1)
            for paths in ([str(image), str(video)], [str(empty)], [str(root / "missing.png")]):
                with self.subTest(paths=paths), self.assertRaises(oauth.RelayConfigError):
                    oauth.load_media_files(paths)

    def test_shipped_entrypoint_works_from_unrelated_working_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            env = {"PATH": os.environ.get("PATH", ""), "HOME": temporary, "USERPROFILE": temporary,
                   "HERMES_HOME": temporary, "PYTHONDONTWRITEBYTECODE": "1"}
            result = subprocess.run([sys.executable, str(SCRIPT), "post", "--text", "preview", "--dry-run"],
                                    cwd=temporary, env=env, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["dry_run"])
            result = subprocess.run([sys.executable, str(SCRIPT), "post", "--text", "Hello"],
                                    cwd=temporary, env=env, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 1)
            self.assertFalse(json.loads(result.stdout)["ok"])
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
