from __future__ import annotations
from pathlib import Path
from typing import Optional
from services.generators.download_cache import DownloadCache
from services.generators.export_discovery import ExportDiscovery
from services.generators.selector_diagnostics import SelectorDiagnostics
try:
    from services.generators.donjon_web_provider import DonjonWebProvider
    from services.generators.web_automation_models import WebGenerationRequest, WebGenerationResult
except Exception:
    DonjonWebProvider=None
    from dataclasses import dataclass, field, asdict
    from typing import Dict, Any
    @dataclass(frozen=True)
    class WebGenerationRequest:
        campaign_id: str; campaign_name: str|None=None; output_dir: str='campaigns/web'; url: str=''; headless: bool=True; dungeon_name: str|None=None; theme: str|None=None; size: str|None=None; layout: str|None=None
        def to_dict(self): return asdict(self)
    @dataclass(frozen=True)
    class WebGenerationResult:
        campaign_id: str; campaign_name: str; provider: str; output_dir: str; page_url: str; json_file: str|None=None; pdf_file: str|None=None; html_file: str|None=None; screenshot_file: str|None=None; downloads: Dict[str,str]=field(default_factory=dict); warnings: list[str]=field(default_factory=list); metadata: Dict[str,Any]=field(default_factory=dict)
        def to_dict(self): return asdict(self)

class DonjonWebProviderV2:
    provider_name='donjon_web_v2'
    def __init__(self, provider: Optional[object]=None, cache: Optional[DownloadCache]=None, diagnostics: Optional[SelectorDiagnostics]=None, discovery: Optional[ExportDiscovery]=None):
        if provider is None and DonjonWebProvider is None: provider=None
        self.provider=provider or (DonjonWebProvider() if DonjonWebProvider else None); self.cache=cache or DownloadCache(); self.diagnostics=diagnostics or SelectorDiagnostics(); self.discovery=discovery or ExportDiscovery()
    def generate(self, request: WebGenerationRequest, use_cache: bool=True, refresh_cache: bool=False):
        req=request.to_dict(); cached=self.cache.find(self.provider_name, req) if use_cache and not refresh_cache else None
        if cached:
            out=self.cache.materialize(cached, request.output_dir)
            return WebGenerationResult(request.campaign_id, request.campaign_name or getattr(request,'dungeon_name',None) or request.campaign_id, self.provider_name, request.output_dir, str(cached.metadata.get('page_url', getattr(request,'url',''))), out.get('json'), out.get('pdf'), out.get('html'), out.get('screenshot'), out, ['Loaded from local generation cache.'], {'cache_key':cached.cache_key,'cached':True})
        if not self.provider: raise RuntimeError('DonjonWebProvider is unavailable. Install/apply Sprint 5 and Playwright, or use cache.')
        result=self.provider.generate(request); output=Path(request.output_dir); files={}
        if result.html_file:
            diag=self.diagnostics.analyze_file(result.html_file, output/'selector_diagnostics.json')
            disc=self.discovery.discover_file(result.html_file, result.page_url, output/'export_discovery.json')
            files['selector_diagnostics']=str(output/'selector_diagnostics.json'); files['export_discovery']=str(output/'export_discovery.json')
            if not result.json_file and disc.best_json(): result.warnings.append('JSON candidate discovered but not downloaded: '+disc.best_json().url)
            if diag.status!='OK': result.warnings.extend(diag.recommendations)
        for label, attr in [('json','json_file'),('pdf','pdf_file'),('html','html_file'),('screenshot','screenshot_file')]:
            val=getattr(result, attr, None)
            if val: files[label]=val
        rec=self.cache.store(self.provider_name, req, files, {'page_url': result.page_url, 'warnings': result.warnings})
        meta=dict(result.metadata); meta.update({'cache_key':rec.cache_key,'cached':False})
        return WebGenerationResult(result.campaign_id,result.campaign_name,self.provider_name,result.output_dir,result.page_url,result.json_file,result.pdf_file,result.html_file,result.screenshot_file,result.downloads,result.warnings,meta)
