"""Read-client contracts and CLI behavior; all requests are replaced by fixtures."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import twitter_client as client


class ReadClientTests(unittest.TestCase):
    def setUp(self):
        self.reader = client.TwitterClient('fixture-only', quote_only=True)

    def captured(self, method, *args, **kwargs):
        with patch.object(client.aisa_transport, 'request', return_value={'tweets': []}) as request:
            result = getattr(self.reader, method)(*args, **kwargs)
        self.assertEqual(result, {'tweets': []})
        self.assertEqual(request.call_count, 1)
        self.assertEqual(request.call_args.args[0], 'GET')
        self.assertTrue(request.call_args.kwargs['quote_only'])
        url = urlsplit(request.call_args.args[1])
        self.assertEqual(url.netloc, 'api.aisa.one')
        return url.path, parse_qs(url.query)

    def test_read_methods_use_current_paths_and_parameter_spelling(self):
        cases = [
            ('user_info', ('alice',), '/twitter/user/info', {'userName': ['alice']}),
            ('user_about', ('alice',), '/twitter/user_about', {'userName': ['alice']}),
            ('batch_user_info', ('123,456',), '/twitter/user/batch_info_by_ids', {'userIds': ['123,456']}),
            ('user_tweets', ('alice', 'opaque+/='), '/twitter/user/last_tweets', {'userName': ['alice'], 'cursor': ['opaque+/=']}),
            ('user_mentions', ('alice',), '/twitter/user/mentions', {'userName': ['alice']}),
            ('followers', ('alice',), '/twitter/user/followers', {'userName': ['alice']}),
            ('followings', ('alice',), '/twitter/user/followings', {'userName': ['alice']}),
            ('verified_followers', ('123',), '/twitter/user/verifiedFollowers', {'user_id': ['123']}),
            ('check_follow_relationship', ('alice', 'bob'), '/twitter/user/check_follow_relationship', {'source_user_name': ['alice'], 'target_user_name': ['bob']}),
            ('user_search', ('alpha beta',), '/twitter/user/search', {'query': ['alpha beta']}),
            ('search', ('alpha & beta', 'Top', 'opaque+/='), '/twitter/tweet/advanced_search', {'query': ['alpha & beta'], 'queryType': ['Top'], 'cursor': ['opaque+/=']}),
            ('tweet_detail', ('123,456',), '/twitter/tweets', {'tweet_ids': ['123,456']}),
            ('tweet_replies', ('123',), '/twitter/tweet/replies', {'tweetId': ['123']}),
            ('tweet_quotes', ('123',), '/twitter/tweet/quotes', {'tweetId': ['123']}),
            ('tweet_retweeters', ('123',), '/twitter/tweet/retweeters', {'tweetId': ['123']}),
            ('tweet_thread', ('123',), '/twitter/tweet/thread_context', {'tweetId': ['123']}),
            ('article', ('123',), '/twitter/article', {'tweet_id': ['123']}),
            ('trends', (1,), '/twitter/trends', {'woeid': ['1']}),
            ('list_members', ('123',), '/twitter/list/members', {'list_id': ['123']}),
            ('list_followers', ('123',), '/twitter/list/followers', {'list_id': ['123']}),
            ('community_info', ('123',), '/twitter/community/info', {'community_id': ['123']}),
            ('community_members', ('123',), '/twitter/community/members', {'community_id': ['123']}),
            ('community_moderators', ('123',), '/twitter/community/moderators', {'community_id': ['123']}),
            ('community_tweets', ('123',), '/twitter/community/tweets', {'community_id': ['123']}),
            ('community_search', ('alpha',), '/twitter/community/get_tweets_from_all_community', {'query': ['alpha'], 'queryType': ['Latest']}),
        ]
        for method, args, path, parameters in cases:
            with self.subTest(method=method):
                actual_path, actual_parameters = self.captured(method, *args)
                self.assertEqual(actual_path, '/apis/v1' + path)
                self.assertEqual(actual_parameters, parameters)
                snapshot = json.loads((Path(__file__).parent / 'fixtures/provider_contracts.json').read_text())
                contract = next(op for op in snapshot['operations'].values() if op['method'] == 'GET' and op['path'] == actual_path)
                declared = contract['query_parameters']
                self.assertLessEqual(set(actual_parameters), set(declared))
                self.assertLessEqual({name for name, spec in declared.items() if spec.get('required')}, set(actual_parameters))

    def test_community_search_has_required_query_type_and_preserves_cursor(self):
        _, parameters = self.captured('community_search', 'alpha', 'next', 'Top')
        self.assertEqual(parameters, {'query': ['alpha'], 'queryType': ['Top'], 'cursor': ['next']})

    def test_unverified_cursor_is_rejected_without_dispatch(self):
        with patch.object(client.aisa_transport, 'request') as request:
            for method in ('user_mentions', 'user_search', 'tweet_quotes'):
                with self.subTest(method=method), self.assertRaisesRegex(ValueError, 'cursor support'):
                    getattr(self.reader, method)('value', 'next')
            request.assert_not_called()

    def test_invalid_values_do_not_dispatch(self):
        with patch.object(client.aisa_transport, 'request') as request:
            for method, args in [('search', (' ',)), ('user_info', ('',)),
                                 ('search', ('alpha', 'Unexpected')), ('trends', (0,)), ('trends', (True,))]:
                with self.subTest(method=method, args=args), self.assertRaises(ValueError):
                    getattr(self.reader, method)(*args)
            request.assert_not_called()

    def run_cli(self, arguments, result=None):
        output = io.StringIO()
        with patch.object(sys, 'argv', ['twitter_client.py', *arguments]), contextlib.redirect_stdout(output), \
                patch.object(client, '_resolve_aisa_api_key', return_value='fixture-only'), \
                patch.object(client.aisa_transport, 'request', return_value=result or {'tweets': []}) as request:
            code = client.main()
        return code, json.loads(output.getvalue()), request

    def test_cli_returns_nonzero_for_http_error(self):
        code, result, request = self.run_cli(['search', '--query', 'alpha', '--quote'],
                                            {'success': False, 'ok': False, 'error': {'code': 'HTTP_ERROR', 'message': 'HTTP 401'}})
        self.assertEqual(code, 1)
        self.assertFalse(result['success'])
        self.assertEqual(request.call_count, 1)

    def test_cli_retains_provider_data_and_does_not_auto_paginate(self):
        code, result, request = self.run_cli(['search', '--query', 'alpha', '--quote'],
                                            {'tweets': [{'id': '123'}], 'next_cursor': 'next', 'has_next_page': True})
        self.assertEqual(code, 0)
        self.assertEqual(result['tweets'][0]['id'], '123')
        self.assertEqual(result['next_cursor'], 'next')
        self.assertEqual(request.call_count, 1)

    def test_invalid_cli_inputs_fail_before_auth_or_cost_ledger(self):
        for arguments in [['search', '--query', ' '], ['space-detail', '--space-id', '123'],
                          ['mentions', '--username', 'alice', '--cursor', 'next'], ['trends', '--woeid', '-1']]:
            with self.subTest(arguments=arguments), patch.object(sys, 'argv', ['twitter_client.py', *arguments]), \
                    patch.object(client, '_resolve_aisa_api_key') as credentials, \
                    patch.object(client.aisa_transport, 'budget_from_args') as ledger, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(client.main(), 1)
                credentials.assert_not_called()
                ledger.assert_not_called()

    def test_help_and_missing_credentials_from_unrelated_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            environment = {key: value for key, value in os.environ.items()
                           if key not in {'AISA_API_KEY', 'HERMES_HOME', 'HERMES_PROFILE', 'PYTHONPATH'}}
            environment['HOME'] = temp
            for arguments, expected in [(['--help'], 0), (['search', '--query', 'alpha', '--quote'], 1)]:
                result = subprocess.run([sys.executable, str(SCRIPTS / 'twitter_client.py'), *arguments],
                                        cwd=temp, env=environment, capture_output=True, text=True)
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertNotIn('Traceback', result.stderr)
                if expected:
                    self.assertFalse(json.loads(result.stdout)['success'])
                    self.assertFalse(json.loads(result.stdout)['ok'])


if __name__ == '__main__':
    unittest.main()
