# driverx.assets

## Purpose

Owns generated OOD asset requests, dry-run manifests, provider readiness checks,
and scenario recipe asset references.

## Public API

- `default_asset_requests()`
- `generate_assets_dry_run(requests)`
- `generate_assets_with_provider(requests, provider, api_key)`
- `validate_asset_manifest(manifest)`
- `attach_assets_to_recipes(recipes, manifests)`
- `write_asset_plan(run_dir, manifests, recipes=None)`

## Example

```bash
PYTHONPATH=src python3 -m driverx plan-assets --run-id task12-assets
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_assets
```
