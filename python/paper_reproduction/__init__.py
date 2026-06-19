"""Solver-neutral algorithms for reproducing powder-compaction papers."""

from .core import (
    compaction_fits,
    contact_gini,
    contact_participation,
    fit_heckel,
    fit_huang,
    fit_kawakita,
    linear_fit,
    pearson,
)
from .cases import reproduce_all, reproduce_li, reproduce_liu, reproduce_yuan, reproduce_zhang
from .dem_evidence import validate_dem_evidence, write_dem_evidence_outputs
from .dem_backend_selection import (
    BACKEND_CANDIDATES,
    build_backend_selection_manifest,
    rank_backend_candidates,
    render_backend_selection_markdown,
    selected_backend,
    write_backend_selection_outputs,
)
from .network import (
    ArchBridge,
    Contact,
    contact_force_components,
    Particle,
    arch_bridges,
    coupling_summary,
    fabric_tensor_2d,
    infer_contacts,
    read_contacts,
    read_particles,
    run_electrothermal_network,
    summarize_contact_network,
    virial_stress_tensor_2d,
)
from .pdf_evidence import PAPER_PDF_EVIDENCE, get_pdf_evidence
from .sintering import (
    SINTERING_LAWS,
    SinteringLaw,
    blended_neck_ratio,
    sintering_neck_ratio,
)
from .registry import (
    PAPER_TARGETS,
    build_manifest,
    get_paper_targets,
    render_manifest_markdown,
    write_manifest_outputs,
)
from .report import generate_paper_report
from .series import process_stage_series
from .validation import (
    trend_direction,
    validate_algorithm_reproduction,
    validate_stage_series,
    write_acceptance_outputs,
)

__all__ = [
    "ArchBridge",
    "arch_bridges",
    "Contact",
    "contact_force_components",
    "compaction_fits",
    "contact_gini",
    "contact_participation",
    "coupling_summary",
    "fit_heckel",
    "fit_huang",
    "fit_kawakita",
    "fabric_tensor_2d",
    "generate_paper_report",
    "infer_contacts",
    "linear_fit",
    "Particle",
    "PAPER_PDF_EVIDENCE",
    "PAPER_TARGETS",
    "pearson",
    "process_stage_series",
    "read_particles",
    "read_contacts",
    "build_manifest",
    "BACKEND_CANDIDATES",
    "build_backend_selection_manifest",
    "get_paper_targets",
    "get_pdf_evidence",
    "rank_backend_candidates",
    "render_backend_selection_markdown",
    "render_manifest_markdown",
    "reproduce_all",
    "reproduce_li",
    "reproduce_liu",
    "reproduce_yuan",
    "reproduce_zhang",
    "run_electrothermal_network",
    "summarize_contact_network",
    "virial_stress_tensor_2d",
    "SINTERING_LAWS",
    "SinteringLaw",
    "blended_neck_ratio",
    "sintering_neck_ratio",
    "trend_direction",
    "selected_backend",
    "validate_algorithm_reproduction",
    "validate_dem_evidence",
    "validate_stage_series",
    "write_acceptance_outputs",
    "write_backend_selection_outputs",
    "write_dem_evidence_outputs",
    "write_manifest_outputs",
]
