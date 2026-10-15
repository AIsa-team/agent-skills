"""Offline regressions for the public CLI and runtime configuration."""

from contextlib import redirect_stderr, redirect_stdout
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
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
from lib import costs, env, pipeline, planner, providers

spec = importlib.util.spec_from_file_location("last30days_cli_runtime_test", SCRIPTS / "last30days.py")
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="last30days-runtime-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.process_env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": str(self.directory),
            "LAST30DAYS_CONFIG_DIR": "",
            "LAST30DAYS_PYTHON": sys.executable,
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        self.env_patch = patch.dict(os.environ, self.process_env, clear=True)
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)
        self.config_patch = patch.object(env, "CONFIG_FILE", None)
        self.config_patch.start()
        self.addCleanup(self.config_patch.stop)

    def invoke(self, *args, config=None):
        output, error = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", ["last30days", *args]), redirect_stdout(output), redirect_stderr(error):
            with patch.object(env, "get_config", return_value=config or {}) as config_loader:
                try:
                    status = cli.main()
                except SystemExit as exc:
                    status = exc.code
        return status, output.getvalue(), error.getvalue(), config_loader

    def run_child(self, script, *args, overrides=None):
        # Fail loudly on any accidental provider I/O, including in mock/setup paths.
        guard = self.directory / "sitecustomize.py"
        guard.write_text(
            "import socket\n"
            "def deny(*args, **kwargs): raise AssertionError('network disabled by runtime test')\n"
            "socket.create_connection = deny\n"
            "socket.socket.connect = deny\n"
        )
        child_env = {**self.process_env, "PYTHONPATH": str(self.directory), **(overrides or {})}
        command = ["bash", str(script), *args] if str(script).endswith(".sh") else [sys.executable, str(script), *args]
        return subprocess.run(command, cwd=self.directory, env=child_env, text=True, capture_output=True, timeout=20)

    def test_unknown_and_abbreviated_research_flags_fail_before_config(self):
        for flag in ("--max-usd=1", "--quik", "--bud=1", "--github"):
            with self.subTest(flag=flag):
                status, _, error, loader = self.invoke("topic", flag)
                self.assertEqual(status, 2)
                self.assertIn("unrecognized arguments", error)
                loader.assert_not_called()

    def test_mutually_exclusive_depth_fails_before_config(self):
        status, _, _, loader = self.invoke("topic", "--quick", "--deep")
        self.assertEqual(status, 2)
        loader.assert_not_called()

    def test_invalid_windows_fail_before_config(self):
        for days in ("0", "-1", "366", "bad"):
            with self.subTest(days=days):
                status, _, _, loader = self.invoke("topic", f"--lookback-days={days}")
                self.assertEqual(status, 2)
                loader.assert_not_called()

    def test_unsupported_retrieval_flags_fail_before_config(self):
        for flag in ("--deep-research", "--tiktok-hashtags=example", "--tiktok-creators=example", "--ig-creators="):
            with self.subTest(flag=flag):
                status, _, error, loader = self.invoke("topic", flag)
                self.assertEqual(status, 2)
                self.assertIn("unsupported", error)
                loader.assert_not_called()

    def test_invalid_plan_payloads_fail_before_config(self):
        plans = ["{", "[]", "{}", '{"subqueries":{}}', '{"subqueries":[{}]}',
                 '{"subqueries":[{"search_query":"x","ranking_query":"x","sources":"reddit"}]}',
                 '{"subqueries":[{"search_query":"x","ranking_query":"x","weight":NaN}]}']
        for plan in plans:
            with self.subTest(plan=plan):
                status, _, error, loader = self.invoke("topic", "--plan", plan)
                self.assertEqual(status, 2)
                self.assertIn("Invalid --plan", error)
                loader.assert_not_called()

    def test_external_plan_file_runs_without_internal_planner(self):
        plan = self.directory / "plan.json"
        plan.write_text(json.dumps({"subqueries": [{"search_query": "sample", "ranking_query": "sample", "sources": ["reddit"]}]}))
        with patch.object(planner, "plan_query", side_effect=AssertionError("internal planner must not run")):
            status, output, _, _ = self.invoke("sample", "--mock", "--search=reddit", "--plan", str(plan), "--emit=json")
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(output)["query_plan"]["subqueries"][0]["search_query"], "sample")

    def test_mock_autoresolve_stays_offline_with_ambient_key(self):
        from lib import resolve
        with patch.object(resolve, "auto_resolve", side_effect=AssertionError("mock must not discover")):
            status, output, _, _ = self.invoke("sample", "--mock", "--auto-resolve", "--quick", "--emit=json", config={"AISA_API_KEY": "fixture-only"})
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(output)["artifacts"]["costs"]["run_cost_micros_usd"], 0)

    def test_mock_setup_rejected_before_config(self):
        status, _, _, loader = self.invoke("setup", "--mock")
        self.assertEqual(status, 2)
        loader.assert_not_called()

    def test_mock_has_no_fictional_source_fixtures(self):
        status, _, error, loader = self.invoke("topic", "--mock", "--search=youtube")
        self.assertEqual(status, 2)
        self.assertIn("no fixture", error)
        loader.assert_not_called()

    def test_hosted_research_requires_budget_before_any_research(self):
        with patch.object(cli, "_run_research", side_effect=AssertionError("research must not start")):
            status, _, error, _ = self.invoke("sample", "--auto-resolve", config={"AISA_API_KEY": "fixture-only", "AISA_MODEL": "model"})
        self.assertEqual(status, 2)
        self.assertIn("requires --budget-usd", error)

    def test_explicit_public_sources_ignore_ambient_hosted_models(self):
        from lib import http
        def offline_stream(*, source, subquery, **kwargs):
            return pipeline._mock_stream_results(source, subquery)
        with patch.object(pipeline, "_retrieve_stream", side_effect=offline_stream), \
             patch.object(http, "request", side_effect=AssertionError("network must not be used")), \
             patch.object(providers.AIsaClient, "generate_text", side_effect=AssertionError("hosted reasoning must not be used")):
            status, output, error, _ = self.invoke(
                "sample", "--search=reddit,hackernews", "--quick", "--emit=json",
                config={"AISA_API_KEY": "fixture-only", "AISA_MODEL": "fixture-model"},
            )
        self.assertEqual(status, 0, error)
        report = json.loads(output)
        self.assertEqual(report["provider_runtime"]["reasoning_provider"], "local")
        self.assertEqual(report["artifacts"]["costs"]["run_request_count"], 0)
        self.assertIsNone(report["artifacts"]["costs"].get("ledger_path"))

    def test_public_sources_with_explicit_discovery_still_need_budget(self):
        status, _, error, _ = self.invoke(
            "sample", "--search=reddit,hackernews", "--auto-resolve",
            config={"AISA_API_KEY": "fixture-only", "AISA_MODEL": "fixture-model"},
        )
        self.assertEqual(status, 2)
        self.assertIn("requires --budget-usd", error)

    def test_budget_context_covers_autoresolve_and_failure_summary(self):
        from lib import resolve
        ledger = self.directory / "costs.json"
        def fail_inside_budget(*args):
            self.assertEqual(costs.current_budget().path, ledger)
            raise RuntimeError("synthetic discovery failure")
        with patch.object(resolve, "auto_resolve", side_effect=fail_inside_budget):
            status, _, error, _ = self.invoke(
                "sample", "--auto-resolve", "--budget-usd=0.25", "--cost-ledger", str(ledger),
                config={"AISA_API_KEY": "fixture-only", "AISA_MODEL": "model"},
            )
        self.assertEqual(status, 1)
        summary = json.loads(error.split("[last30days] costs ")[-1])
        self.assertEqual(summary["budget_micros_usd"], 250000)
        self.assertEqual(summary["run_request_count"], 0)
        self.assertTrue(ledger.exists())

    def test_clean_mode_does_not_read_project_config(self):
        project = self.directory / ".claude"
        project.mkdir()
        (project / "last30days.env").write_text("AISA_API_KEY=fixture-only\nAISA_MODEL=fixture-model\n")
        with patch.object(Path, "cwd", return_value=self.directory):
            config = env.get_config()
        self.assertIsNone(config["AISA_API_KEY"])
        self.assertIsNone(config["AISA_MODEL"])
        self.assertEqual(config["_CONFIG_SOURCE"], "env_only")

    def test_wrapper_preserves_callers_project_config(self):
        project = self.directory / ".claude"
        project.mkdir()
        config = project / "last30days.env"
        config.write_text("AISA_API_KEY=fixture-only\nAISA_MODEL=fixture-model\n")
        config.chmod(0o600)
        result = self.run_child(SCRIPTS / "run-last30days.sh", "--diagnose", overrides={"LAST30DAYS_CONFIG_DIR": str(self.directory / "global")})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["providers"]["aisa"])

    def test_interpreter_override_is_honored_and_bad_override_rejected(self):
        success = self.run_child(SCRIPTS / "dev-python.sh")
        self.assertEqual(success.returncode, 0, success.stderr)
        self.assertEqual(success.stdout.strip(), sys.executable)
        failure = self.run_child(SCRIPTS / "dev-python.sh", overrides={"LAST30DAYS_PYTHON": str(self.directory / "missing-python")})
        self.assertNotEqual(failure.returncode, 0)
        self.assertIn("LAST30DAYS_PYTHON", failure.stderr)

    def test_python_311_is_supported_and_310_is_rejected(self):
        cli.ensure_supported_python((3, 11, 0))
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            cli.ensure_supported_python((3, 10, 15))

    def test_model_array_response_falls_back_to_local_plan(self):
        class ArrayProvider(providers.ReasoningClient):
            def generate_text(self, *args, **kwargs):
                return "[]"
        with redirect_stderr(io.StringIO()):
            plan = planner.plan_query(topic="sample", available_sources=["reddit"], requested_sources=["reddit"], depth="quick", provider=ArrayProvider(), model="fixture-model")
        self.assertTrue(plan.subqueries)
        self.assertTrue(any("fallback-plan" in note for note in plan.notes))
        for value in ("[]", "null", '"string"', "42"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                providers.extract_json(value)

    def test_malformed_model_plan_structures_fall_back(self):
        class ShapeProvider:
            def generate_json(self, *args, **kwargs):
                return {"subqueries": {}, "source_weights": []}
        with redirect_stderr(io.StringIO()):
            plan = planner.plan_query(topic="sample", available_sources=["reddit"], requested_sources=None, depth="quick", provider=ShapeProvider(), model="fixture-model")
        self.assertTrue(plan.subqueries)

    def test_planner_cost_refusal_falls_back_without_retry(self):
        class RefusedProvider:
            calls = 0
            def generate_json(self, *args, **kwargs):
                self.calls += 1
                raise costs.CostControlError("variable quote requires explicit authorization")
        provider = RefusedProvider()
        with redirect_stderr(io.StringIO()):
            plan = planner.plan_query(topic="sample", available_sources=["reddit"], requested_sources=None, depth="quick", provider=provider, model="fixture-model")
        self.assertTrue(plan.subqueries)
        self.assertEqual(provider.calls, 1)
        self.assertIn("cost controls", plan.notes[0])

    def test_unpinned_models_use_local_reasoning_with_hosted_retrieval(self):
        runtime, provider = providers.resolve_runtime({"AISA_API_KEY": "fixture-only"}, "quick")
        self.assertIsNone(provider)
        self.assertEqual(runtime.reasoning_provider, "local")
        self.assertEqual(runtime.x_search_backend, "aisa")
        self.assertIn("x", pipeline.available_sources({"AISA_API_KEY": "fixture-only"}))
        with self.assertRaises(RuntimeError):
            providers.resolve_runtime({"LAST30DAYS_REASONING_PROVIDER": "unsupported"}, "quick")

    def test_cost_refusal_is_visible_in_report_warnings(self):
        with redirect_stderr(io.StringIO()):
            report = pipeline.run(topic="sample", config={}, depth="quick", mock=True)
        def refuse_then_return(*args):
            try:
                costs.current_budget()._refuse("unsupported hosted reasoning route")
            except costs.CostControlError:
                pass
            return report
        with patch.object(cli, "_run_research", side_effect=refuse_then_return):
            status, output, _, _ = self.invoke(
                "sample", "--budget-usd=0", "--cost-ledger", str(self.directory / "warning-costs.json"),
                "--emit=json", config={"AISA_API_KEY": "fixture-only"},
            )
        self.assertEqual(status, 0)
        self.assertTrue(any("unsupported hosted reasoning route" in warning for warning in json.loads(output)["warnings"]))

    def test_evaluator_help_and_no_live_default(self):
        help_result = self.run_child(SCRIPTS / "run-evaluate.sh", "--help")
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        rejected = self.run_child(SCRIPTS / "run-evaluate.sh")
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("historical scripts may lack cost controls", rejected.stderr)

    def test_wrapper_mock_is_offline_and_saves_in_caller_directory(self):
        result = self.run_child(SCRIPTS / "run-last30days.sh", "sample", "--mock", "--auto-resolve", "--quick", "--emit=json", "--save-dir=out")
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["artifacts"]["costs"]["run_request_count"], 0)
        self.assertTrue((self.directory / "out" / "sample-raw.json").exists())

    def test_mock_evaluator_cannot_call_a_hosted_judge(self):
        topics = self.directory / "topics.json"
        topics.write_text('[{"topic":"sample","query_type":"general"}]')
        result = self.run_child(
            SCRIPTS / "run-evaluate.sh", "--baseline=WORKTREE", "--candidate=WORKTREE",
            "--mock", "--quick", "--judge-model=fixture-model", "--topics-file", str(topics),
            "--output-dir", str(self.directory / "evaluation"),
            overrides={"AISA_API_KEY": "fixture-only"},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["failures"], 0)

    def test_evaluator_resolves_skill_directory_inside_revision_checkout(self):
        import evaluate_search_quality as evaluator
        repository = self.directory / "catalog"
        skill = repository / "search-research" / "last30days"
        checkout = self.directory / "revision"
        skill.mkdir(parents=True)
        checkout.mkdir()
        def git_command(command, **kwargs):
            if command[1] == "rev-parse":
                return subprocess.CompletedProcess(command, 0, stdout=str(repository) + "\n")
            if command[2] == "add":
                scripts = checkout / "search-research" / "last30days" / "scripts"
                scripts.mkdir(parents=True)
                (scripts / "last30days.py").write_text("# fixture\n")
            return subprocess.CompletedProcess(command, 0, stdout="")
        with patch.object(evaluator, "REPO_ROOT", skill), \
             patch.object(evaluator.tempfile, "mkdtemp", return_value=str(checkout)), \
             patch.object(evaluator.subprocess, "run", side_effect=git_command) as commands:
            resolved, temporary = evaluator.resolve_repo_dir("fixture-revision")
            self.assertTrue(temporary)
            self.assertTrue((resolved / "scripts" / "last30days.py").is_file())
            evaluator.remove_worktree(resolved)
        self.assertEqual(commands.call_args.args[0][-1], str(checkout))

    def test_saved_run_cost_is_this_run_not_whole_ledger(self):
        import store
        with redirect_stderr(io.StringIO()):
            report = pipeline.run(topic="sample", config={}, depth="quick", mock=True)
        report.artifacts["costs"] = {
            "spent_micros_usd": 900000, "run_cost_micros_usd": 125000, "ledger_path": "ledger.json",
        }
        with patch.object(store, "init_db"), patch.object(store, "add_topic", return_value={"id": 1}), \
             patch.object(store, "record_run", return_value=2) as record, \
             patch.object(store, "store_findings", return_value={"new": 1, "updated": 0}), \
             patch.object(store, "update_run") as update:
            cli.persist_report(report)
        self.assertEqual(record.call_args.kwargs["cost_micros_usd"], 125000)
        self.assertEqual(update.call_args.kwargs["cost_micros_usd"], 125000)
        self.assertEqual(update.call_args.kwargs["cost_status"], "reported")

    def test_unknown_run_cost_stays_unknown_when_saved(self):
        import store
        with redirect_stderr(io.StringIO()):
            report = pipeline.run(topic="sample", config={}, depth="quick", mock=True)
        report.artifacts["costs"] = {"run_cost_micros_usd": None, "ledger_path": "ledger.json"}
        with patch.object(store, "init_db"), patch.object(store, "add_topic", return_value={"id": 1}), \
             patch.object(store, "record_run", return_value=2), \
             patch.object(store, "store_findings", return_value={"new": 0, "updated": 0}), \
             patch.object(store, "update_run") as update:
            cli.persist_report(report)
        self.assertIsNone(update.call_args.kwargs["cost_micros_usd"])
        self.assertEqual(update.call_args.kwargs["cost_status"], "unknown")


if __name__ == "__main__":
    unittest.main()
