from __future__ import annotations

SNIPPET = """
from services.dungeons.donjon_generation_postprocess_hook import DonjonGenerationPostprocessHook

postprocess = DonjonGenerationPostprocessHook(project_root='.')
postprocess_result = postprocess.after_download(
    campaign_id=campaign_id,
    download_dir=download_dir,
    output_dir=bundle_dir,
    manifest_file=manifest_path,
    runtime_import=False,
    runtime_name=campaign_name,
    clear_rag=False,
)
logger.info('Donjon postprocess result: %s', postprocess_result)
"""

if __name__ == '__main__':
    print(SNIPPET)
