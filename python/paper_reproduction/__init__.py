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
from .network import (
    ArchBridge,
    Contact,
    Particle,
    arch_bridges,
    coupling_summary,
    infer_contacts,
    read_particles,
    run_electrothermal_network,
    summarize_contact_network,
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
    "compaction_fits",
    "contact_gini",
    "contact_participation",
    "coupling_summary",
    "fit_heckel",
    "fit_huang",
    "fit_kawakita",
    "generate_paper_report",
    "infer_contacts",
    "linear_fit",
    "Particle",
    "PAPER_TARGETS",
    "pearson",
    "process_stage_series",
    "read_particles",
    "build_manifest",
    "get_paper_targets",
    "render_manifest_markdown",
    "reproduce_all",
    "reproduce_li",
    "reproduce_liu",
    "reproduce_yuan",
    "reproduce_zhang",
    "run_electrothermal_network",
    "summarize_contact_network",
    "trend_direction",
    "validate_algorithm_reproduction",
    "validate_stage_series",
    "write_acceptance_outputs",
    "write_manifest_outputs",
]
