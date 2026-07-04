"""Procedural dungeon generator/importer provider package."""

try:
    from services.generators.generator_provider import GeneratorProvider, GenerationRequest
except Exception:
    GeneratorProvider = None
    GenerationRequest = None
try:
    from services.generators.donjon_json_importer import DonjonJsonImporter
except Exception:
    DonjonJsonImporter = None
try:
    from services.generators.campaign_bundle_builder import CampaignBundleBuilder
except Exception:
    CampaignBundleBuilder = None
try:
    from services.generators.campaign_enricher import CampaignEnricher
except Exception:
    CampaignEnricher = None
try:
    from services.generators.generation_orchestrator import GenerateCampaignRequest, GeneratedCampaignResult, GenerationOrchestrator
    from services.generators.generate_command_parser import GenerateCommandParser
    from services.generators.generation_admin_service import GenerationAdminService
except Exception:
    GenerateCampaignRequest = None
    GeneratedCampaignResult = None
    GenerationOrchestrator = None
    GenerateCommandParser = None
    GenerationAdminService = None

from services.generators.web_automation_models import WebGenerationRequest, WebGenerationResult
from services.generators.donjon_web_config import DonjonWebSelectors
from services.generators.donjon_web_provider import DonjonWebProvider
from services.generators.donjon_web_command_parser import DonjonWebCommandParser

try:
    from services.generators.donjon_web_pipeline import DonjonWebPipeline
except Exception:
    DonjonWebPipeline = None

__all__ = [
    "GeneratorProvider", "GenerationRequest", "DonjonJsonImporter", "CampaignBundleBuilder", "CampaignEnricher",
    "GenerateCampaignRequest", "GeneratedCampaignResult", "GenerationOrchestrator", "GenerateCommandParser", "GenerationAdminService",
    "WebGenerationRequest", "WebGenerationResult", "DonjonWebSelectors", "DonjonWebProvider", "DonjonWebCommandParser", "DonjonWebPipeline",
]
