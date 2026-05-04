import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.assets import (
    AssetManifest,
    AssetRequest,
    attach_assets_to_recipes,
    default_asset_requests,
    generate_assets_dry_run,
    generate_assets_with_provider,
    validate_asset_manifest,
    write_asset_plan,
)
from driverx.scenarios import MutationPolicy, generate_scenario_recipes, load_scenario_seeds


class GeneratedAssetPipelineTest(unittest.TestCase):
    def test_default_asset_requests_include_generation_metadata(self) -> None:
        requests = default_asset_requests()

        self.assertGreaterEqual(len(requests), 3)
        request = requests[0]
        self.assertTrue(request.prompt)
        self.assertIn("length", request.dimensions_m)
        self.assertIn("kind", request.collision_proxy)
        self.assertTrue(request.license)

    def test_dry_run_provider_writes_deterministic_manifests(self) -> None:
        manifests = generate_assets_dry_run(default_asset_requests())

        self.assertEqual(manifests[0].asset_id, "asset-fallen-cargo-sack")
        self.assertEqual(manifests[0].status, "planned")
        self.assertEqual(manifests[0].provider, "dry_run")
        self.assertIn("placeholder_carla_blueprint", manifests[0].metadata)
        self.assertEqual(validate_asset_manifest(manifests[0]), [])

    def test_manifest_validator_rejects_missing_scale_collision_and_license(self) -> None:
        bad = AssetManifest(
            asset_id="bad",
            provider="dry_run",
            status="planned",
            prompt="bad prop",
            semantic_tags=["bad"],
            dimensions_m={"length": 1.0},
            collision_proxy={"kind": "box"},
            intended_placement={},
            license="",
        )

        errors = validate_asset_manifest(bad)

        self.assertIn("bad: license is required", errors)
        self.assertIn("bad: dimensions_m.width must be positive", errors)
        self.assertIn("bad: collision_proxy.length must be positive", errors)
        self.assertIn("bad: intended_placement is required", errors)

    def test_meshy_provider_blocks_without_api_key(self) -> None:
        request = default_asset_requests()[0]
        manifests = generate_assets_with_provider([request], "meshy", api_key="")

        self.assertEqual(manifests[0].status, "blocked")
        self.assertIn("MESHY_API_KEY", manifests[0].setup_guidance or "")

    def test_scenario_recipes_can_reference_generated_asset_ids(self) -> None:
        seeds = load_scenario_seeds(Path("tests/fixtures/fail2drive_like/seeds.json"))
        recipes = generate_scenario_recipes(
            seeds,
            MutationPolicy(mutations=("visual_noise",)),
            count=2,
            random_seed=8,
        )
        manifests = generate_assets_dry_run(default_asset_requests())

        updated = attach_assets_to_recipes(recipes, manifests)

        self.assertIn("generated_asset_ids", updated[0].environment)
        self.assertEqual(updated[0].actors[-1]["kind"], "static_asset")
        self.assertIn(updated[0].actors[-1]["asset_id"], updated[0].memory_query)

    def test_write_asset_plan_artifacts(self) -> None:
        manifests = generate_assets_dry_run(default_asset_requests())
        with TemporaryDirectory() as tmp:
            summary = write_asset_plan(Path(tmp), manifests)
            payload = json.loads(Path(summary["summary_path"]).read_text(encoding="utf-8"))
            report = Path(summary["report_path"]).read_text(encoding="utf-8")

        self.assertEqual(payload["num_assets"], len(manifests))
        self.assertEqual(payload["validation_errors"], {})
        self.assertIn("# Asset Plan", report)

    def test_asset_request_round_trip(self) -> None:
        request = default_asset_requests()[1]

        round_tripped = AssetRequest.from_jsonable(request.to_jsonable())

        self.assertEqual(round_tripped.asset_id, request.asset_id)
        self.assertEqual(round_tripped.dimensions_m["height"], request.dimensions_m["height"])


if __name__ == "__main__":
    unittest.main()
