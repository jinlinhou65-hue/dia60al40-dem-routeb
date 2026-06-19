from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PdfEvidence:
    page: int
    evidence: str
    reproduction_use: str
    current_status: str


PAPER_PDF_EVIDENCE: dict[str, list[PdfEvidence]] = {
    "zhang": [
        PdfEvidence(
            page=1,
            evidence=(
                "Paper defines a DEM study of macro stress, meso force chains, "
                "micro contact force, Gini, participation, D1, and D2."
            ),
            reproduction_use="Scope of multi-scale stress/contact inhomogeneity metrics.",
            current_status="Implemented with explicit multiscale metrics and real DEM stage-series gates.",
        ),
        PdfEvidence(
            page=3,
            evidence=(
                "2D die is 10 mm x 15 mm with 3000 iron particles; diameter "
                "148-296 um, mean 222 um, density 7800 kg/m3, E=209 GPa, nu=0.25, "
                "friction 0.25, punch speed 0.2 m/s, endpoint about 600 MPa."
            ),
            reproduction_use="Reference scale and target pressure for solver backend calibration.",
            current_status="Route-B demo uses a reduced particle count but preserves staged DEM workflow.",
        ),
        PdfEvidence(
            page=4,
            evidence=(
                "Gini coefficient and participation number quantify contact-force "
                "inhomogeneity; force chains require force above mean, at least "
                "three particles, and angle threshold 180 degrees divided by mean coordination."
            ),
            reproduction_use="Contact Gini, participation, and force-chain D1 acceptance gates.",
            current_status="Implemented with strong-contact threshold, force-chain count, strength, and D1 outputs.",
        ),
        PdfEvidence(
            page=5,
            evidence=(
                "Local stress is averaged in measurement circles and normalized "
                "standard deviation D2 quantifies local y-stress inhomogeneity."
            ),
            reproduction_use="Local stress inhomogeneity metric and expected decreasing trend.",
            current_status="Implemented with measurement-circle local stress mean, standard deviation, and D2 proxy.",
        ),
    ],
    "yuan": [
        PdfEvidence(
            page=18,
            evidence=(
                "DEM model is 0.016 m wide and 0.020 m high, initial porosity 0.22, "
                "E=80 GPa, nu=0.29, friction 0.20, wall stiffness 2e12 N/m, "
                "punch speed 2 cm/s until 600 MPa."
            ),
            reproduction_use="Discrete-element setup and pressure endpoint for arch-bridge route.",
            current_status="Route-B LIGGGHTS demo uses equivalent staged compaction and handoff tables.",
        ),
        PdfEvidence(
            page=19,
            evidence="DEM Heckel fit is reported as ln(1/(1-rho_v)) = 0.0015 P + 1.9752 with R2=0.9784.",
            reproduction_use="Heckel pressure-density fit target for validation.",
            current_status="Heckel fit is generated for both proxy data and real stage series.",
        ),
        PdfEvidence(
            page=22,
            evidence=(
                "MPFEM model uses 160 round particles, 300-400 um, Abaqus plane strain, "
                "0.01 mm mesh, Johnson-Cook parameters, friction 0.2, speed 2 cm/s, "
                "and 600 MPa endpoint."
            ),
            reproduction_use="Higher-fidelity deformable-particle backend specification.",
            current_status="Documented as next backend; current open-source run uses LIGGGHTS DEM.",
        ),
        PdfEvidence(
            page=40,
            evidence=(
                "Arch criteria require more than two particles, the main arch particle "
                "above abutment particles, gravity line crossing the abutment line, "
                "and minimum mean-square separation selection."
            ),
            reproduction_use="Arch extraction algorithm design.",
            current_status="Implemented as connected strong-contact arch candidates; exact MPFEM topology remains next step.",
        ),
        PdfEvidence(
            page=42,
            evidence="Arch length, strength, buckling angle, and direction angle are defined by equations 4-2 to 4-5.",
            reproduction_use="Arch metric output schema.",
            current_status="Implemented in yuan count, length, obstruction, strength, direction, and buckling outputs.",
        ),
        PdfEvidence(
            page=49,
            evidence=(
                "Lower aspect-ratio strip powder reaches higher density and reduces "
                "arch obstruction; arch count rises then fluctuates, strength growth "
                "slows after about 100 MPa, direction stays near 90 degrees."
            ),
            reproduction_use="Shape and pressure trend acceptance gates.",
            current_status="Implemented with count-peak, length-fluctuation, strength-slowdown, direction, and shape gates; clump/polygon DEM remains next step.",
        ),
    ],
    "liu": [
        PdfEvidence(
            page=2,
            evidence=(
                "The paper is a cross-scale review of compaction and sintering, "
                "covering nonlinear elastic, rigid-plastic compressible, and generalized plastic models."
            ),
            reproduction_use="Treat as a workflow/specification paper rather than a single raw dataset.",
            current_status="Implemented as compaction fits plus electrothermal-sintering coupling scaffold.",
        ),
        PdfEvidence(
            page=4,
            evidence="Huang, Heckel, and Kawakita equations are given for pressure-density compression fitting.",
            reproduction_use="Compaction curve fitting functions and fit CSV outputs.",
            current_status="Implemented in core compaction_fits and real DEM series_compaction_fits.",
        ),
        PdfEvidence(
            page=9,
            evidence=(
                "Compaction microstructure is the initial condition for sintering; "
                "density, pore network, residual stress, and diffusion paths should be mapped across processes."
            ),
            reproduction_use="DEM-to-sintering handoff fields and coupling rationale.",
            current_status="Implemented as density/contact/force/current/heat/neck proxy fields.",
        ),
        PdfEvidence(
            page=11,
            evidence=(
                "Early sintering neck growth laws are listed for volume diffusion, "
                "grain-boundary diffusion, and surface diffusion."
            ),
            reproduction_use="Diffusion-law neck-growth implementation and future material-constant calibration.",
            current_status="Implemented as normalized Wilson/Johnson/Kuczynski/Coble/Nabarro-Herring diffusion-law scaffold.",
        ),
        PdfEvidence(
            page=14,
            evidence=(
                "Referenced DEM sintering geometries include relative densities "
                "0.784, 0.836, 0.894, and 0.950 for neck-size comparison."
            ),
            reproduction_use="Density milestones for coupled compaction-sintering validation.",
            current_status="Route-B real DEM stage series reaches rho_total=0.95.",
        ),
    ],
    "li": [
        PdfEvidence(
            page=3,
            evidence=(
                "Cu20@Fe80 has more uniform internal stress than Fe; wall friction blocks densification; "
                "temperature raises relative density; higher pressing speed lowers density; "
                "Cu 20-25 percent gives lower stress and better plasticity."
            ),
            reproduction_use="Coated-powder sweep directions and acceptance gates.",
            current_status="Implemented in sweep and core-shell stress/plasticity proxy tables.",
        ),
        PdfEvidence(
            page=4,
            evidence="Diameter-height ratio near 2:1 gives Cu20@Fe80 relative density 96.45 percent; experiment trend is Cu30@Fe70 > Cu20@Fe80 > Cu10@Fe90 > Fe.",
            reproduction_use="Aspect-ratio and composition trend targets.",
            current_status="Implemented as aspect-ratio peak, stress-growth, and composition density-ranking gates.",
        ),
        PdfEvidence(
            page=41,
            evidence="Temperature raises relative density; after pressure exceeds 500 MPa the temperature effect weakens.",
            reproduction_use="Temperature sweep trend and high-pressure diminishing-effect note.",
            current_status="Implemented in temperature-pressure response and attenuation gates.",
        ),
        PdfEvidence(
            page=49,
            evidence="Increasing Cu content lowers Cu/Fe interface friction and Cu-wall friction, improving flow and density.",
            reproduction_use="Composition-to-friction coupling rule.",
            current_status="Implemented as interface-friction and wall-friction proxy gates.",
        ),
        PdfEvidence(
            page=52,
            evidence=(
                "PFC2D generates random particle coordinates with initial porosity 0.22; "
                "coordinates are imported into MSC.MARC for multi-particle core-shell FEM."
            ),
            reproduction_use="Hybrid DEM-to-FEM construction route.",
            current_status="Documented; Li proxy now exposes MPFEM-replaceable core-shell output schemas.",
        ),
        PdfEvidence(
            page=56,
            evidence="Above 500 MPa, 100-particle and 197-particle model densities converge; 197 particles is selected for efficiency and realism.",
            reproduction_use="Reduced-model adequacy criterion.",
            current_status="Implemented in Li particle-count convergence output and gate.",
        ),
        PdfEvidence(
            page=71,
            evidence="At 600 MPa, density rises then falls with diameter-height ratio and peaks near 2:1.",
            reproduction_use="Aspect-ratio sweep gate.",
            current_status="Implemented in Li aspect-ratio sweep.",
        ),
    ],
}


def get_pdf_evidence(keys: list[str] | None = None) -> dict[str, list[dict[str, object]]]:
    requested = PAPER_PDF_EVIDENCE.keys() if not keys or keys == ["all"] else keys
    return {
        key: [asdict(item) for item in PAPER_PDF_EVIDENCE[key]]
        for key in requested
        if key in PAPER_PDF_EVIDENCE
    }
