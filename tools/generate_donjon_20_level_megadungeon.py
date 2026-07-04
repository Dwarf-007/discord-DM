from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Tuple



def slugify_folder_key(value: str) -> str:
    """Create a deterministic filesystem-safe folder key.

    Keeps lowercase ASCII-ish tokens, maps whitespace/punctuation to underscores,
    and avoids accidental empty folder names.
    """
    value = str(value or '').strip()
    normalized = unicodedata.normalize('NFKD', value)
    ascii_value = normalized.encode('ascii', 'ignore').decode('ascii')
    slug = re.sub(r'[^a-zA-Z0-9]+', '_', ascii_value).strip('_').lower()
    slug = re.sub(r'_+', '_', slug)
    return slug or 'campaign'


def folder_key_from_args(args: argparse.Namespace) -> str:
    """Folder naming priority.

    1. --folder-key if explicitly provided
    2. --name if --use-name-for-folders is enabled
    3. campaign_id
    """
    if getattr(args, 'folder_key', None):
        return slugify_folder_key(args.folder_key)
    if getattr(args, 'use_name_for_folders', False) and getattr(args, 'name', None):
        return slugify_folder_key(args.name)
    return slugify_folder_key(args.campaign_id)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Generate Donjon 5e dungeon levels 1-20 and optionally run the full post-download processing pipeline.'
    )
    parser.add_argument('campaign_id')
    parser.add_argument('--name')
    parser.add_argument('--theme', default='None')
    parser.add_argument('--output-dir', default=None, help='Donjon raw download/output directory. Default: campaigns/web/<folder_key>_levels_<start>_<end>')
    parser.add_argument('--bundle-dir', default=None, help='Processed bundle directory. Default: campaigns/<folder_key>_bundle_v3')
    parser.add_argument('--folder-key', default=None, help='Filesystem-safe folder key override. Highest priority for default output directories.')
    parser.add_argument('--use-name-for-folders', action='store_true', help='Use slug(--name) for default folder names when --folder-key is not provided.')
    parser.add_argument('--url', default='https://donjon.bin.sh/5e/dungeon/')
    parser.add_argument('--headed', action='store_true')
    parser.add_argument('--level-start', type=int, default=1)
    parser.add_argument('--level-end', type=int, default=20)
    parser.add_argument('--party-size', default='4')
    parser.add_argument('--room-size', default='Medium', choices=['Medium', 'Large'])
    parser.add_argument('--remove-deadends', default='Some', choices=['Some', 'None'])
    parser.add_argument('--seed')
    parser.add_argument('--delay', type=float, default=1.0)
    parser.add_argument('--result-timeout-ms', type=int, default=240000)
    parser.add_argument('--download-timeout-ms', type=int, default=30000)
    parser.add_argument('--download-exports', action='store_true', default=True)
    parser.add_argument('--no-download-exports', action='store_false', dest='download_exports')
    parser.add_argument('--use-back-to-settings', action='store_true', default=True)
    parser.add_argument('--no-back-to-settings', action='store_false', dest='use_back_to_settings')
    parser.add_argument('--postprocess', action='store_true', default=True, help='Run full Donjon processing after manifest is saved. Default: enabled.')
    parser.add_argument('--no-postprocess', action='store_false', dest='postprocess', help='Only generate/download Donjon files; skip processing pipeline.')
    parser.add_argument('--postprocess-strict', action='store_true', help='Return non-zero if postprocess pipeline reports ok=false.')
    parser.add_argument('--runtime-import', action='store_true', help='After processing, also import generated bundle into runtime DB.')
    parser.add_argument('--runtime-name', default=None, help='Runtime campaign display name. Default: --name or campaign_id.')
    parser.add_argument('--clear-rag', action='store_true', help='When --runtime-import is used, clear campaign RAG chunks before import.')
    parser.add_argument('--max-label-match-distance', type=int, default=2, help='Door label coordinate matching tolerance for postprocess pipeline.')
    return parser


def build_plan(args: argparse.Namespace):
    from services.generators.donjon_megadungeon_defaults import DonjonLevelSettings, DonjonMegaDungeonPlan

    settings = DonjonLevelSettings(
        motif=args.theme,
        party_size=str(args.party_size),
        room_size=args.room_size,
        remove_deadends=args.remove_deadends,
    )
    return DonjonMegaDungeonPlan(
        level_start=args.level_start,
        level_end=args.level_end,
        settings=settings,
    )


def default_raw_output_dir(args: argparse.Namespace) -> Path:
    key = folder_key_from_args(args)
    return Path(args.output_dir or f'campaigns/web/{key}_levels_{args.level_start}_{args.level_end}')


def default_bundle_dir(args: argparse.Namespace) -> Path:
    key = folder_key_from_args(args)
    return Path(args.bundle_dir or f'campaigns/{key}_bundle_v3')


def generate_and_download_levels(args: argparse.Namespace) -> Tuple[Path, Dict[str, Any]]:
    plan = build_plan(args)
    output_dir = default_raw_output_dir(args)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise SystemExit('Playwright is not installed. Run: pip install playwright && playwright install chromium') from exc

    manifest: Dict[str, Any] = {
        'campaign_id': args.campaign_id,
        'campaign_name': args.name or args.campaign_id,
        'folder_key': folder_key_from_args(args),
        'raw_output_dir': str(output_dir),
        'bundle_dir': str(default_bundle_dir(args)),
        'plan': plan.to_dict(),
        'levels': [],
    }

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not args.headed)
        context = browser.new_context(accept_downloads=True, viewport={'width': 1600, 'height': 1200})
        page = context.new_page()
        first = True
        try:
            for level in plan.levels():
                level_entry = generate_one_level(args, plan, page, output_dir, level, first)
                manifest['levels'].append(level_entry)
                first = False
                downloads = level_entry.get('downloads') or {}
                print(f"OK level {level}: ready={level_entry.get('ready')} downloads={list(downloads.keys())}")
        finally:
            context.close()
            browser.close()

    manifest_path = output_dir / 'donjon_megadungeon_manifest.json'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Manifest: {manifest_path}')
    return manifest_path, manifest


def generate_one_level(args: argparse.Namespace, plan: Any, page: Any, output_dir: Path, level: int, first: bool) -> Dict[str, Any]:
    from services.generators.donjon_dom_automation import DonjonDomAutomation

    level_dir = output_dir / f'level_{level:02d}'
    level_dir.mkdir(parents=True, exist_ok=True)

    if first or not args.use_back_to_settings:
        page.goto(args.url, wait_until='domcontentloaded', timeout=90000)
    else:
        if not DonjonDomAutomation.click_back_to_settings(page):
            page.goto(args.url, wait_until='domcontentloaded', timeout=90000)

    page.wait_for_timeout(1000)
    warnings: List[str] = []

    DonjonDomAutomation.set_by_label(page, 'Dungeon Name', f'{args.name or args.campaign_id} L{level:02d}')
    if args.seed:
        DonjonDomAutomation.set_by_label(page, 'Random Seed', f'{args.seed}-{level}')

    warnings.extend(DonjonDomAutomation.apply_form_settings(page, plan.settings.to_form_labels()))
    if not DonjonDomAutomation.set_by_label(page, 'Dungeon Level', str(level)):
        warnings.append(f'Could not set Dungeon Level={level}')

    (level_dir / 'before_construct.html').write_text(page.content(), encoding='utf-8')

    if not DonjonDomAutomation.click_construct_or_generate(page):
        page.screenshot(path=str(level_dir / 'selector_failure.png'), full_page=True)
        raise RuntimeError('Could not click Construct Dungeon. See selector_failure.png and before_construct.html')

    page.wait_for_timeout(max(500, int(args.delay * 1000)))
    ready_state = DonjonDomAutomation.wait_for_result_ready(page, timeout_ms=args.result_timeout_ms)
    ready = bool(ready_state.get('ready'))
    if not ready:
        warnings.append('Timed out waiting for Donjon result; current HTML/screenshot saved for diagnostics.')

    html_path = level_dir / 'donjon_result.html'
    screenshot_path = level_dir / 'donjon_result.png'
    html_path.write_text(page.content(), encoding='utf-8')
    page.screenshot(path=str(screenshot_path), full_page=True)

    downloads: Dict[str, str] = {}
    if ready and args.download_exports:
        downloads = DonjonDomAutomation.download_available_exports(
            page,
            level_dir,
            f'{args.campaign_id}_level_{level:02d}',
            timeout_ms=args.download_timeout_ms,
        )
        if 'json' not in downloads:
            warnings.append('JSON download not captured via Vue or menu fallback.')
        if 'pdf' not in downloads:
            warnings.append('PDF download not captured via Vue or menu fallback.')

    return {
        'level': level,
        'directory': str(level_dir),
        'html_file': str(html_path),
        'screenshot_file': str(screenshot_path),
        'downloads': downloads,
        'entry_anchor': plan.entry_anchor_for_level(level),
        'exit_anchor': plan.exit_anchor_for_level(level),
        'ready': ready,
        'ready_state': ready_state,
        'warnings': warnings,
    }


def run_postprocess(args: argparse.Namespace, manifest_path: Path) -> Dict[str, Any]:
    from services.dungeons.donjon_generation_postprocess_hook import DonjonGenerationPostprocessHook

    raw_output_dir = default_raw_output_dir(args)
    bundle_dir = default_bundle_dir(args)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    print(f'Folder key: {folder_key_from_args(args)}')
    print(f'Raw output dir: {raw_output_dir}')
    print(f'Bundle dir: {bundle_dir}')
    print('Starting Donjon post-processing pipeline...')

    postprocess = DonjonGenerationPostprocessHook(project_root='.')
    result = postprocess.after_download(
        campaign_id=args.campaign_id,
        download_dir=raw_output_dir,
        output_dir=bundle_dir,
        manifest_file=manifest_path,
        runtime_import=args.runtime_import,
        runtime_name=args.runtime_name or args.name or args.campaign_id,
        clear_rag=args.clear_rag,
    )
    print(json.dumps({'postprocess_result': result}, ensure_ascii=False, indent=2))
    return result


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    print(f'Using folder key: {folder_key_from_args(args)}')
    print(f'Raw Donjon output: {default_raw_output_dir(args)}')
    print(f'Processed bundle: {default_bundle_dir(args)}')

    manifest_path, _manifest = generate_and_download_levels(args)

    if args.postprocess:
        postprocess_result = run_postprocess(args, manifest_path)
        if args.postprocess_strict and not postprocess_result.get('ok'):
            return 2

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
