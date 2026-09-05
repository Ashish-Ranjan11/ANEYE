
import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  ChevronRight,
  CircleDot,
  Download,
  Eye,
  FileText,
  Focus,
  ImagePlus,
  Info,
  Layers3,
  Microscope,
  ScanEye,
  ShieldCheck,
  Sparkles,
  Target,
  Upload,
  X,
} from "lucide-react";
import "../mvp-workstation.css";

const API = "http://127.0.0.1:8000";

const LESION_META = {
  MA: {
    full: "Microaneurysms",
    short: "Tiny balloon-like outpouchings of retinal capillaries; often an early visible sign of diabetic retinopathy.",
    colorClass: "lesion-ma",
  },
  HE: {
    full: "Retinal Hemorrhages",
    short: "Areas of blood leakage inside the retina, suggesting damage to fragile retinal blood vessels.",
    colorClass: "lesion-he",
  },
  EX: {
    full: "Hard Exudates",
    short: "Bright lipid and protein deposits left behind when damaged retinal vessels leak fluid.",
    colorClass: "lesion-ex",
  },
  SE: {
    full: "Soft Exudates / Cotton-Wool Spots",
    short: "Fluffy pale lesions associated with focal retinal nerve-fiber ischemia and impaired blood flow.",
    colorClass: "lesion-se",
  },
};

const GRADE_META = [
  {
    grade: 0,
    title: "No apparent DR",
    explain: "No visible diabetic-retinopathy lesions are identified at the screening threshold.",
  },
  {
    grade: 1,
    title: "Mild NPDR",
    explain: "Microaneurysms are present, but more advanced retinal changes are not dominant.",
  },
  {
    grade: 2,
    title: "Moderate NPDR",
    explain: "More than microaneurysms are present, but the image does not meet severe NPDR criteria.",
  },
  {
    grade: 3,
    title: "Severe NPDR",
    explain: "Extensive non-proliferative retinal vascular damage is suspected and requires urgent specialist review.",
  },
  {
    grade: 4,
    title: "Proliferative DR",
    explain: "Advanced disease is suspected. NetraAI does not independently claim neovascularization without dedicated supervision.",
  },
];

const NAV_ITEMS = [
  ["input", "01", "Acquire", Upload],
  ["quality", "02", "Quality", Focus],
  ["global", "03", "Global", BrainCircuit],
  ["local", "04", "Local", Microscope],
  ["anatomy", "05", "Anatomy", Eye],
  ["xai", "06", "Explain", Sparkles],
  ["trust", "07", "TRACE-DR", ShieldCheck],
  ["decision", "08", "Decision", Target],
  ["report", "09", "Report", FileText],
];

const REGIONS = [
  { id: "sup-left", label: "Superior-left retinal sector", x: 0, y: 0, w: 33.333, h: 33.333 },
  { id: "sup-center", label: "Superior-central retinal sector", x: 33.333, y: 0, w: 33.333, h: 33.333 },
  { id: "sup-right", label: "Superior-right retinal sector", x: 66.666, y: 0, w: 33.334, h: 33.333 },
  { id: "mid-left", label: "Central-left retinal sector", x: 0, y: 33.333, w: 33.333, h: 33.333 },
  { id: "macular", label: "Central / macular screening sector", x: 33.333, y: 33.333, w: 33.333, h: 33.333 },
  { id: "mid-right", label: "Central-right retinal sector", x: 66.666, y: 33.333, w: 33.334, h: 33.333 },
  { id: "inf-left", label: "Inferior-left retinal sector", x: 0, y: 66.666, w: 33.333, h: 33.334 },
  { id: "inf-center", label: "Inferior-central retinal sector", x: 33.333, y: 66.666, w: 33.333, h: 33.334 },
  { id: "inf-right", label: "Inferior-right retinal sector", x: 66.666, y: 66.666, w: 33.334, h: 33.334 },
];

function clamp(v, lo = 0, hi = 100) {
  return Math.max(lo, Math.min(hi, Number(v || 0)));
}

function pct(v, digits = 1) {
  return `${(Number(v || 0) * 100).toFixed(digits)}%`;
}

function directPct(v, digits = 1) {
  return `${Number(v || 0).toFixed(digits)}%`;
}

function artifact(path) {
  return path ? `${API}${path}` : "";
}

function getComponents(result) {
  const out = [];
  if (!result) return out;
  for (const key of Object.keys(LESION_META)) {
    const arr =
      result?.lesions?.[key]?.components ||
      result?.lesion_components?.[key] ||
      [];
    for (const c of arr) out.push({ ...c, lesion: key });
  }
  return out;
}

function componentPoint(c, result) {
  const W = Number(
    result?.image_width ||
      result?.image?.width ||
      result?.source?.width ||
      1
  );
  const H = Number(
    result?.image_height ||
      result?.image?.height ||
      result?.source?.height ||
      1
  );

  let x = c.x ?? c.cx ?? c.centroid_x ?? c.centroid?.[0];
  let y = c.y ?? c.cy ?? c.centroid_y ?? c.centroid?.[1];
  if (x == null || y == null) return null;

  x = Number(x);
  y = Number(y);

  if (x > 1 || y > 1) {
    x /= W;
    y /= H;
  }

  return { x: clamp(x, 0, 1), y: clamp(y, 0, 1) };
}

function regionStats(result, region) {
  const stats = {
    MA: 0,
    HE: 0,
    EX: 0,
    SE: 0,
    total: 0,
    area: 0,
    confidences: [],
  };

  for (const c of getComponents(result)) {
    const p = componentPoint(c, result);
    if (!p) continue;

    const xp = p.x * 100;
    const yp = p.y * 100;

    if (
      xp >= region.x &&
      xp <= region.x + region.w &&
      yp >= region.y &&
      yp <= region.y + region.h
    ) {
      stats[c.lesion] += 1;
      stats.total += 1;
      stats.area += Number(c.area_px || c.area || 0);

      const cf = Number(c.mean_confidence ?? c.confidence ?? c.score);
      if (Number.isFinite(cf)) stats.confidences.push(cf);
    }
  }

  stats.meanConfidence = stats.confidences.length
    ? stats.confidences.reduce((a, b) => a + b, 0) /
      stats.confidences.length
    : null;

  return stats;
}

function Metric({ label, value, detail, status }) {
  return (
    <div className={`mvp-metric ${status ? `status-${status}` : ""}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {detail && <p>{detail}</p>}
    </div>
  );
}

function Bar({ label, value, max = 100, suffix = "%", note }) {
  const n = Number(value || 0);
  const width = clamp((n / max) * 100);
  return (
    <div className="mvp-bar-row">
      <div className="mvp-bar-head">
        <div>
          <strong>{label}</strong>
          {note && <small>{note}</small>}
        </div>
        <b>
          {Number.isInteger(n) ? n : n.toFixed(1)}
          {suffix}
        </b>
      </div>
      <div className="mvp-bar-track">
        <i style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}

function ScoreGauge({ label, value, subtitle, footnote }) {
  const n = clamp(value);
  return (
    <div className="mvp-score">
      <div
        className="mvp-score-ring"
        style={{ "--score-angle": `${n * 3.6}deg` }}
      >
        <div>
          <strong>{n.toFixed(1)}</strong>
          <span>/100</span>
        </div>
      </div>
      <div>
        <span>{label}</span>
        <h3>{subtitle}</h3>
        {footnote && <p>{footnote}</p>}
      </div>
    </div>
  );
}

function QualityRadar({ quality }) {
  const values = [
    clamp((quality?.focus || 0) * 100),
    clamp((quality?.illumination || 0) * 100),
    clamp((quality?.contrast || 0) * 100),
    clamp((quality?.fov || 0) * 100),
  ];

  const points = values
    .map((v, i) => {
      const angle = (-90 + i * 90) * (Math.PI / 180);
      const r = (v / 100) * 66;
      const x = 90 + Math.cos(angle) * r;
      const y = 90 + Math.sin(angle) * r;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <div className="mvp-radar">
      <svg viewBox="0 0 180 180" role="img" aria-label="Image quality fingerprint">
        {[1, 0.75, 0.5, 0.25].map((f) => (
          <polygon
            key={f}
            points={`90,${90 - 66 * f} ${90 + 66 * f},90 90,${90 + 66 * f} ${90 - 66 * f},90`}
            className="radar-grid"
          />
        ))}
        <line x1="90" y1="20" x2="90" y2="160" />
        <line x1="20" y1="90" x2="160" y2="90" />
        <polygon points={points} className="radar-value" />
        <text x="90" y="14" textAnchor="middle">FOCUS</text>
        <text x="168" y="94" textAnchor="end">ILLUMINATION</text>
        <text x="90" y="176" textAnchor="middle">CONTRAST</text>
        <text x="12" y="94">FOV</text>
      </svg>
    </div>
  );
}

function FundusSchematic() {
  return (
    <div className="fundus-schematic">
      <svg viewBox="0 0 620 410" role="img" aria-label="Educational fundus anatomy schematic">
        <defs>
          <radialGradient id="retinaGrad">
            <stop offset="0%" stopColor="#8f311f" />
            <stop offset="72%" stopColor="#4a160e" />
            <stop offset="100%" stopColor="#1c0807" />
          </radialGradient>
        </defs>

        <ellipse cx="300" cy="205" rx="245" ry="170" fill="url(#retinaGrad)" />
        <circle cx="402" cy="196" r="36" className="disc" />
        <circle cx="224" cy="214" r="22" className="macula" />
        <circle cx="224" cy="214" r="6" className="fovea" />

        <g className="vessels">
          <path d="M402 196 C350 180, 315 150, 264 110" />
          <path d="M402 196 C344 205, 310 245, 262 285" />
          <path d="M402 196 C456 172, 495 144, 526 115" />
          <path d="M402 196 C452 220, 492 249, 521 287" />
          <path d="M355 184 C322 166, 292 162, 250 157" />
          <path d="M352 207 C318 222, 284 229, 246 238" />
        </g>

        <g className="schematic-labels">
          <line x1="405" y1="150" x2="450" y2="92" />
          <text x="455" y="88">Optic disc</text>

          <line x1="220" y1="185" x2="174" y2="126" />
          <text x="105" y="121">Macula</text>

          <line x1="224" y1="214" x2="151" y2="215" />
          <text x="82" y="220">Fovea</text>

          <line x1="323" y1="155" x2="334" y2="100" />
          <text x="288" y="90">Retinal vessels</text>
        </g>
      </svg>
      <p>
        Educational anatomy schematic only. The current MVP does not claim
        patient-specific optic-disc, macula, or vessel segmentation unless a
        dedicated model supplies those outputs.
      </p>
    </div>
  );
}

function PdfPreview({ url, onClose }) {
  if (!url) return null;

  return (
    <div className="pdf-modal" role="dialog" aria-modal="true">
      <div className="pdf-modal-card">
        <div className="pdf-modal-head">
          <div>
            <span>NETRAAI DETAILED ANALYSIS REPORT</span>
            <h3>Explainable screening report preview</h3>
          </div>
          <button onClick={onClose} aria-label="Close PDF preview">
            <X size={18} />
          </button>
        </div>

        <iframe src={url} title="NetraAI PDF report preview" />

        <div className="pdf-modal-actions">
          <a href={url} target="_blank" rel="noreferrer">
            <Download size={16} />
            Open full PDF
          </a>
          <p>
            Contains screening summary, pathology evidence, model probability,
            Grad-CAM interpretation, TRACE-DR reliability and routing rationale.
          </p>
        </div>
      </div>
    </div>
  );
}


const STRUCTURE_API_BASE =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";


function structureArtifactUrl(path) {
  if (!path) return null;

  if (
    path.startsWith("http://") ||
    path.startsWith("https://") ||
    path.startsWith("blob:") ||
    path.startsWith("data:")
  ) {
    return path;
  }

  if (path.startsWith("/")) {
    return `${STRUCTURE_API_BASE}${path}`;
  }

  return `${STRUCTURE_API_BASE}/${path}`;
}


function structuralPercent(value, digits = 1) {
  const number = Number(value);

  if (!Number.isFinite(number)) {
    return "—";
  }

  return `${(number * 100).toFixed(digits)}%`;
}


function StructuralRetinaPanel({
  result,
  preview,
}) {
  const [view, setView] =
    useState("fundus");

  const structure =
    result?.structure || {};

  const opticDisc =
    structure?.optic_disc || null;

  const fovea =
    structure?.fovea || null;

  const vessels =
    structure?.vessels || null;

  const vesselMask =
    structureArtifactUrl(
      result?.artifacts?.vessel_mask
    );

  const structuralOverlay =
    structureArtifactUrl(
      result?.artifacts?.structural_overlay
    );

  const currentImage =
    view === "vessels"
      ? vesselMask
      : view === "overlay"
        ? structuralOverlay
        : preview;

  const failed =
    structure?.status ===
    "STRUCTURAL_ANALYSIS_FAILED";

  return (
    <section className="mvp-stage structural-stage">

      <div className="mvp-stage-title">

        <span>
          05 · STRUCTURAL RETINAL ANALYSIS
        </span>

        <h1>
          See the retinal structures behind
          the screening result.
        </h1>

        <p>
          NetraAI combines the original fundus
          photograph with prototype optic-disc
          localization, an estimated foveal landmark
          and retinal-vessel segmentation to provide
          anatomical context for lesion evidence.
        </p>

      </div>


      {failed ? (
        <div className="structural-error">

          <strong>
            Structural analysis unavailable
          </strong>

          <p>
            The main diabetic-retinopathy analysis
            completed, but the prototype structural
            branch could not process this image.
          </p>

        </div>
      ) : (
        <>

          <div className="structural-workbench">

            <div className="structural-viewer">

              <div className="structural-view-tabs">

                <button
                  type="button"
                  className={
                    view === "fundus"
                      ? "active"
                      : ""
                  }
                  onClick={() =>
                    setView("fundus")
                  }
                >
                  Original Fundus
                </button>

                <button
                  type="button"
                  className={
                    view === "vessels"
                      ? "active"
                      : ""
                  }
                  disabled={!vesselMask}
                  onClick={() =>
                    setView("vessels")
                  }
                >
                  Vessel Mask
                </button>

                <button
                  type="button"
                  className={
                    view === "overlay"
                      ? "active"
                      : ""
                  }
                  disabled={!structuralOverlay}
                  onClick={() =>
                    setView("overlay")
                  }
                >
                  Structural Overlay
                </button>

              </div>


              <div className="structural-image-stage">

                {currentImage ? (
                  <img
                    src={currentImage}
                    alt={
                      view === "fundus"
                        ? "Original retinal fundus"
                        : view === "vessels"
                          ? "Prototype retinal vessel mask"
                          : "Structural retinal overlay"
                    }
                  />
                ) : (
                  <div className="structural-empty">
                    Structural artifact unavailable
                  </div>
                )}

                <div className="structural-image-badge">
                  {view === "fundus"
                    ? "REAL INPUT"
                    : view === "vessels"
                      ? "COMPUTED VESSEL MASK"
                      : "COMPUTED STRUCTURAL OVERLAY"}
                </div>

              </div>


              <div className="structural-view-description">

                {view === "fundus" && (
                  <>
                    <strong>
                      Original analyzed fundus
                    </strong>

                    <p>
                      The same retinal photograph
                      supplied to the NetraAI
                      screening pipeline.
                    </p>
                  </>
                )}

                {view === "vessels" && (
                  <>
                    <strong>
                      Prototype retinal-vessel
                      segmentation
                    </strong>

                    <p>
                      Vessel candidates are extracted
                      using green-channel contrast,
                      CLAHE and multi-scale
                      morphological enhancement.
                    </p>
                  </>
                )}

                {view === "overlay" && (
                  <>
                    <strong>
                      Structural evidence overlay
                    </strong>

                    <p>
                      Combines the real fundus with
                      the vessel mask, prototype
                      optic-disc localization and
                      estimated foveal landmark.
                    </p>
                  </>
                )}

              </div>

            </div>


            <div className="structural-metric-column">

              <article className="structural-metric-card disc">

                <div className="structural-card-top">

                  <span>
                    STRUCTURE 01
                  </span>

                  <b>
                    OPTIC DISC
                  </b>

                </div>

                <h3>
                  Optic Disc Localized
                </h3>

                <p>
                  Bright retinal landmark where the
                  optic nerve exits the eye and major
                  retinal vessels converge.
                </p>

                <div className="structural-values">

                  <div>
                    <span>
                      Center X
                    </span>

                    <strong>
                      {opticDisc?.center_x ??
                        "—"}
                    </strong>
                  </div>

                  <div>
                    <span>
                      Center Y
                    </span>

                    <strong>
                      {opticDisc?.center_y ??
                        "—"}
                    </strong>
                  </div>

                  <div>
                    <span>
                      Radius
                    </span>

                    <strong>
                      {opticDisc?.radius_px
                        ? `${opticDisc.radius_px} px`
                        : "—"}
                    </strong>
                  </div>

                  <div>
                    <span>
                      Reliability
                    </span>

                    <strong>
                      {structuralPercent(
                        opticDisc?.confidence
                      )}
                    </strong>
                  </div>

                </div>

                <small>
                  Prototype brightness +
                  circularity localization
                </small>

              </article>


              <article className="structural-metric-card fovea">

                <div className="structural-card-top">

                  <span>
                    STRUCTURE 02
                  </span>

                  <b>
                    FOVEAL LANDMARK
                  </b>

                </div>

                <h3>
                  Estimated Foveal Landmark
                </h3>

                <p>
                  Approximate central-vision landmark
                  estimated relative to the localized
                  optic disc.
                </p>

                <div className="structural-values">

                  <div>
                    <span>
                      Center X
                    </span>

                    <strong>
                      {fovea?.center_x ??
                        "—"}
                    </strong>
                  </div>

                  <div>
                    <span>
                      Center Y
                    </span>

                    <strong>
                      {fovea?.center_y ??
                        "—"}
                    </strong>
                  </div>

                  <div>
                    <span>
                      Reliability
                    </span>

                    <strong>
                      {structuralPercent(
                        fovea?.confidence
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>
                      Method
                    </span>

                    <strong className="small-value">
                      Disc-relative
                    </strong>
                  </div>

                </div>

                <small>
                  Anatomical estimate —
                  not independent learned
                  fovea segmentation
                </small>

              </article>


              <article className="structural-metric-card vessels">

                <div className="structural-card-top">

                  <span>
                    STRUCTURE 03
                  </span>

                  <b>
                    RETINAL VASCULATURE
                  </b>

                </div>

                <h3>
                  Retinal Vessel Network
                </h3>

                <p>
                  Branching vascular structures
                  extracted from the retinal field
                  to provide structural context for
                  diabetic microvascular disease.
                </p>

                <div className="structural-values">

                  <div>
                    <span>
                      Vessel coverage
                    </span>

                    <strong>
                      {structuralPercent(
                        vessels?.density,
                        2
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>
                      Vessel pixels
                    </span>

                    <strong>
                      {Number.isFinite(
                        Number(
                          vessels?.pixel_count
                        )
                      )
                        ? Number(
                            vessels.pixel_count
                          ).toLocaleString()
                        : "—"}
                    </strong>
                  </div>

                  <div>
                    <span>
                      Reliability
                    </span>

                    <strong>
                      {structuralPercent(
                        vessels?.confidence
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>
                      Status
                    </span>

                    <strong className="small-value">
                      Prototype
                    </strong>
                  </div>

                </div>

                <small>
                  Vessel coverage is a prototype
                  image-processing measurement,
                  not a validated clinical biomarker.
                </small>

              </article>

            </div>

          </div>


          <div className="structural-context-strip">

            <div>
              <span>
                WHY THIS MATTERS
              </span>

              <h2>
                Structure gives pathology
                a retinal coordinate system.
              </h2>

              <p>
                Lesion evidence becomes more
                interpretable when it can be viewed
                alongside the retinal field,
                vascular network and anatomical
                landmarks.
              </p>
            </div>


            <div className="structural-context-flow">

              <article>
                <b>01</b>
                <strong>
                  Retina
                </strong>
                <span>
                  Real fundus input
                </span>
              </article>

              <i />

              <article>
                <b>02</b>
                <strong>
                  Structures
                </strong>
                <span>
                  Disc · foveal estimate · vessels
                </span>
              </article>

              <i />

              <article>
                <b>03</b>
                <strong>
                  Pathology
                </strong>
                <span>
                  MA · HE · EX · SE
                </span>
              </article>

              <i />

              <article>
                <b>04</b>
                <strong>
                  Severity
                </strong>
                <span>
                  ICDR 0–4 + RDR
                </span>
              </article>

              <i />

              <article>
                <b>05</b>
                <strong>
                  Trust
                </strong>
                <span>
                  TRACE-DR
                </span>
              </article>

            </div>

          </div>


          <div className="structural-evidence-grid">

            <article>

              <span>
                CURRENT MVP
              </span>

              <h3>
                Computed structural evidence
              </h3>

              <ul>
                <li>
                  Retinal field-of-view extraction
                </li>

                <li>
                  Prototype optic-disc localization
                </li>

                <li>
                  Estimated foveal landmark
                </li>

                <li>
                  Prototype vessel segmentation
                </li>

                <li>
                  Vessel pixel coverage
                </li>

                <li>
                  Structural overlay generation
                </li>
              </ul>

            </article>


            <article>

              <span>
                LOCAL PATHOLOGY
              </span>

              <h3>
                Trained lesion evidence
              </h3>

              <ul>
                <li>
                  Microaneurysm segmentation
                </li>

                <li>
                  Retinal hemorrhage segmentation
                </li>

                <li>
                  Hard-exudate segmentation
                </li>

                <li>
                  Soft-exudate segmentation
                </li>

                <li>
                  Connected-component coordinates
                </li>

                <li>
                  Regional lesion burden
                </li>
              </ul>

            </article>


            <article className="structural-boundary">

              <span>
                CLINICAL BOUNDARY
              </span>

              <h3>
                What remains separate
              </h3>

              <ul>
                <li>
                  Fovea remains a disc-relative
                  anatomical estimate
                </li>

                <li>
                  Vessel coverage is not yet a
                  validated clinical biomarker
                </li>

                <li>
                  Independent neovascularization
                  detection remains a future
                  pathology extension
                </li>

                <li>
                  NetraAI remains screening
                  decision support with human review
                </li>
              </ul>

            </article>

          </div>

        </>
      )}

    </section>
  );
}


export default function EngineWorkspaceMVP() {
  const [searchParams] = useSearchParams();
  const [stage, setStage] = useState("input");
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [viewMode, setViewMode] = useState("lesions");
  const [showTiles, setShowTiles] = useState(true);
  const [showRegions, setShowRegions] = useState(true);
  const [showNodes, setShowNodes] = useState(true);
  const [hoverRegion, setHoverRegion] = useState(null);
  const [lockedRegion, setLockedRegion] = useState(null);
  const [hoverNode, setHoverNode] = useState(null);
  const [showPdf, setShowPdf] = useState(false);
  const inputRef = useRef();

  const activeRegion = lockedRegion || hoverRegion;
  const components = useMemo(() => getComponents(result), [result]);
  const hasLocalizedComponents = components.length > 0;

  const activeRegionStats = useMemo(
    () => (activeRegion ? regionStats(result, activeRegion) : null),
    [activeRegion, result]
  );

  useEffect(() => {
    const demo = searchParams.get("demo");
    if (demo) {
      const map = {
        grade0: ["/demo/grade0.png", "aptos_grade0_demo.png"],
        grade1: ["/demo/grade1.png", "aptos_grade1_demo.png"],
        grade2: ["/demo/grade2.png", "aptos_grade2_demo.png"],
      };
      if (map[demo]) loadDemo(...map[demo]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadDemo(path, name) {
    try {
      setError("");
      setResult(null);
      const response = await fetch(path);
      const blob = await response.blob();
      const demoFile = new File([blob], name, {
        type: blob.type || "image/png",
      });

      setFile(demoFile);
      setPreview(URL.createObjectURL(demoFile));
      setStage("input");
    } catch {
      setError("Could not load the selected demonstration scan.");
    }
  }

  function chooseFile(e) {
    const selected = e.target.files?.[0];
    if (!selected) return;

    setFile(selected);
    setPreview(URL.createObjectURL(selected));
    setResult(null);
    setError("");
    setStage("input");
  }

  async function analyze() {
    if (!file) {
      setError("Choose a retinal fundus image first.");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const body = new FormData();
      body.append("file", file);

      const response = await fetch(`${API}/api/analyze`, {
        method: "POST",
        body,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.detail || "NetraAI analysis failed.");
      }

      setResult(data);
      setStage(data?.quality?.status === "UNGRADEABLE" ? "quality" : "global");
    } catch (err) {
      setError(err?.message || "Could not connect to the NetraAI backend.");
    } finally {
      setLoading(false);
    }
  }

  const stageAvailable = (id) => {
    if (id === "input") return true;
    return Boolean(result);
  };

  const displayedImage =
    viewMode === "gradcam"
      ? artifact(result?.artifacts?.gradcam)
      : viewMode === "lesions"
      ? artifact(result?.artifacts?.lesion_overlay)
      : preview;

  const reportUrl = artifact(result?.artifacts?.report);

  return (
    <div className="mvp-shell">
      <aside className="mvp-side">
        <div className="mvp-side-top">
          <Link to="/">
            <ArrowLeft size={15} />
            Home
          </Link>
          <span>SCREENING WORKFLOW</span>
        </div>

        <nav>
          {NAV_ITEMS.map(([id, number, label, Icon]) => (
            <button
              key={id}
              className={stage === id ? "active" : ""}
              disabled={!stageAvailable(id)}
              onClick={() => stageAvailable(id) && setStage(id)}
            >
              <span>{number}</span>
              <Icon size={16} />
              <strong>{label}</strong>
              <ChevronRight size={14} />
            </button>
          ))}
        </nav>

        <div className="mvp-side-foot">
          <ShieldCheck size={17} />
          <div>
            <strong>Safety contract</strong>
            <p>
              Ungradeable images route to recapture or review. They are never
              silently treated as normal.
            </p>
          </div>
        </div>
      </aside>

      <main className="mvp-main">
        <header className="mvp-topbar">
          <div>
            <span>NETRAAI · TRACE-DR</span>
            <strong>Explainable retinal screening workstation</strong>
          </div>

          <div className="mvp-engine-state">
            <i />
            ENGINE READY
          </div>
        </header>

        {stage === "input" && (
          <section className="mvp-stage stage-input">
            <div className="mvp-stage-title">
              <span>01 · ACQUIRE</span>
              <h1>Start with a retinal fundus image.</h1>
              <p>
                Upload a fundus photograph or use one of the real APTOS
                demonstration images below. The same backend inference pipeline
                is used in both cases.
              </p>
            </div>

            <div className="mvp-acquire-grid">
              <div className="mvp-upload-card">
                <div className="mvp-preview-frame">
                  {preview ? (
                    <img src={preview} alt="Selected retinal fundus" />
                  ) : (
                    <div className="mvp-empty-retina">
                      <ScanEye size={38} />
                      <strong>No retinal image selected</strong>
                      <span>JPG · PNG · BMP · TIFF</span>
                    </div>
                  )}
                </div>

                <input
                  ref={inputRef}
                  hidden
                  type="file"
                  accept="image/*"
                  onChange={chooseFile}
                />

                <div className="mvp-upload-actions">
                  <button
                    className="secondary"
                    onClick={() => inputRef.current?.click()}
                  >
                    <ImagePlus size={16} />
                    Choose image
                  </button>

                  <button
                    className="primary"
                    disabled={!file || loading}
                    onClick={analyze}
                  >
                    {loading ? (
                      <>
                        <Activity className="spin" size={16} />
                        Running NetraAI…
                      </>
                    ) : (
                      <>
                        <BrainCircuit size={16} />
                        Run full analysis
                      </>
                    )}
                  </button>
                </div>

                {error && <div className="mvp-error">{error}</div>}
              </div>

              <div className="mvp-acquire-info">
                <span className="section-label">WHAT HAPPENS NEXT</span>

                {[
                  ["A", "Quality gate", "Checks focus, illumination, contrast and retinal field-of-view."],
                  ["B", "Global grading", "Predicts ICDR Grade 0-4 and referable diabetic retinopathy."],
                  ["C", "High-resolution slicing", "Processes overlapping 512×512 retinal tiles to preserve small lesions."],
                  ["D", "Local pathology", "Detects microaneurysms, hemorrhages, hard exudates and soft exudates."],
                  ["E", "TRACE-DR fusion", "Combines pathology evidence, concordance, Grad-CAM integrity and trust routing."],
                ].map(([k, title, text]) => (
                  <div className="mvp-process-step" key={k}>
                    <b>{k}</b>
                    <div>
                      <strong>{title}</strong>
                      <p>{text}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="mvp-demo-strip">
              <div>
                <span>TRY A REAL DATASET IMAGE</span>
                <h3>Demonstration scans</h3>
                <p>
                  Dataset labels are shown for context only. NetraAI still
                  performs fresh inference on every selection.
                </p>
              </div>

              {[
                ["grade0", "No apparent DR", "APTOS label · Grade 0"],
                ["grade1", "Mild NPDR", "APTOS label · Grade 1"],
                ["grade2", "Moderate NPDR", "APTOS label · Grade 2"],
              ].map(([key, title, sub]) => (
                <button
                  key={key}
                  onClick={() =>
                    loadDemo(`/demo/${key}.png`, `aptos_${key}_demo.png`)
                  }
                >
                  <img src={`/demo/${key}.png`} alt="" />
                  <div>
                    <strong>{title}</strong>
                    <span>{sub}</span>
                  </div>
                </button>
              ))}
            </div>
          </section>
        )}

        {stage === "quality" && result && (
          <section className="mvp-stage">
            <div className="mvp-stage-title split">
              <div>
                <span>02 · QUALITY & RESTORATION</span>
                <h1>Is the image reliable enough to grade?</h1>
                <p>
                  NetraAI separates image reliability from disease prediction.
                  A poor acquisition should not be allowed to masquerade as a
                  confident normal result.
                </p>
              </div>

              <Metric
                label="Quality status"
                value={result.quality.status}
                detail={`Composite reliability ${(result.quality.score * 100).toFixed(1)}%`}
                status={
                  result.quality.status === "GRADEABLE"
                    ? "good"
                    : result.quality.status === "UNGRADEABLE"
                    ? "bad"
                    : "warn"
                }
              />
            </div>

            <div className="mvp-two-col">
              <div className="mvp-image-card">
                <span>SCREENING IMAGE</span>
                <img src={preview} alt="Fundus used for analysis" />
                <div className="mvp-image-caption">
                  {result.quality.enhancement_applied
                    ? "Bounded enhancement was applied before the final inference pass."
                    : "The original acquisition was used for the final inference pass."}
                </div>
              </div>

              <div className="mvp-panel">
                <div className="mvp-panel-head">
                  <div>
                    <span>QUALITY FINGERPRINT</span>
                    <h3>Four acquisition dimensions</h3>
                  </div>
                  <QualityRadar quality={result.quality} />
                </div>

                <Bar label="Focus" value={result.quality.focus * 100} note="Sharpness of retinal detail." />
                <Bar label="Illumination" value={result.quality.illumination * 100} note="Brightness suitability across the retinal field." />
                <Bar label="Contrast" value={result.quality.contrast * 100} note="Separation between vessels, lesions and retinal background." />
                <Bar label="Retinal field-of-view" value={result.quality.fov * 100} note="How much usable retinal area is present." />

                <div className="mvp-explainer">
                  <Info size={16} />
                  <p>
                    Prototype quality thresholds guide routing in this MVP.
                    They are not presented as clinically validated acquisition
                    thresholds.
                  </p>
                </div>
              </div>
            </div>
          </section>
        )}

        {stage === "global" && result && (
          <section className="mvp-stage">
            <div className="mvp-stage-title">
              <span>03 · GLOBAL RETINAL ANALYSIS</span>
              <h1>Whole-retina diabetic-retinopathy severity.</h1>
              <p>
                The global branch evaluates the complete fundus image for ICDR
                grade and referable diabetic retinopathy. This branch is kept
                separate from local lesion segmentation so the two evidence
                streams can later be checked for agreement.
              </p>
            </div>

            <div className="mvp-global-hero">
              <div className="mvp-grade-focus">
                <span>CURRENT ICDR SCREENING GRADE</span>
                <strong>Grade {result.prediction.icdr_grade}</strong>
                <h2>{result.prediction.grade_name}</h2>
                <p>
                  {
                    GRADE_META[result.prediction.icdr_grade]?.explain
                  }
                </p>
              </div>

              <div className="mvp-rdr-card">
                <span>REFERABLE DR</span>
                <strong>
                  {result.prediction.referable_dr ? "POSITIVE" : "NEGATIVE"}
                </strong>
                <b>{pct(result.prediction.rdr_probability, 2)}</b>
                <p>
                  In this prototype, Grade 2 or higher is treated as referable
                  diabetic retinopathy for screening workflow purposes.
                </p>
              </div>

              <div className="mvp-confidence-card">
                <span>RAW GRADE CONFIDENCE</span>
                <strong>{pct(result.prediction.grade_confidence, 2)}</strong>
                <p>
                  Temperature calibration has not yet been applied, so this
                  value is displayed explicitly as raw model confidence.
                </p>
              </div>
            </div>

            <div className="mvp-panel">
              <div className="mvp-panel-heading">
                <BarChart3 size={18} />
                <div>
                  <span>CLASS PROBABILITY PROFILE</span>
                  <h3>Why Grade {result.prediction.icdr_grade} dominates</h3>
                </div>
              </div>

              {result.prediction.grade_probabilities.map((p, i) => (
                <Bar
                  key={i}
                  label={`Grade ${i} · ${GRADE_META[i].title}`}
                  value={p * 100}
                  note={GRADE_META[i].explain}
                />
              ))}
            </div>

            <div className="mvp-grade-rail">
              {GRADE_META.map((g) => (
                <div
                  key={g.grade}
                  className={
                    result.prediction.icdr_grade === g.grade ? "active" : ""
                  }
                >
                  <b>G{g.grade}</b>
                  <strong>{g.title}</strong>
                  <p>{g.explain}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {stage === "local" && result && (
          <section className="mvp-stage local-stage">
            <div className="mvp-stage-title">
              <span>04 · LOCAL PATHOLOGY & RETINAL SLICING</span>
              <h1>Explore exactly where lesion evidence was detected.</h1>
              <p>
                The IDRiD lesion branch works on overlapping 512×512 retinal
                tiles. Connected components are projected back into the
                full-retina coordinate system, making local evidence
                inspectable rather than hidden inside a segmentation mask.
              </p>
            </div>

            <div className="mvp-local-toolbar">
              <div>
                <span>IMAGE VIEW</span>
                {[
                  ["original", "Original"],
                  ["lesions", "Lesion overlay"],
                  ["gradcam", "Grad-CAM"],
                ].map(([key, label]) => (
                  <button
                    key={key}
                    className={viewMode === key ? "active" : ""}
                    onClick={() => setViewMode(key)}
                  >
                    {label}
                  </button>
                ))}
              </div>

              <div>
                <span>ANALYSIS LAYERS</span>
                <button
                  className={showTiles ? "active" : ""}
                  onClick={() => setShowTiles((v) => !v)}
                >
                  512×512 slicing
                </button>
                <button
                  className={showRegions ? "active" : ""}
                  onClick={() => setShowRegions((v) => !v)}
                >
                  Regional grid
                </button>
                <button
                  className={showNodes ? "active" : ""}
                  onClick={() => setShowNodes((v) => !v)}
                >
                  Lesion nodes
                </button>
              </div>
            </div>

            <div className="mvp-local-grid">
              <div className="retina-workbench">
                <div className="retina-stage">
                  <img src={displayedImage} alt="Retinal analysis viewport" />

                  {showTiles && (
                    <div className="tile-overlay">
                      {Array.from({ length: 35 }).map((_, i) => (
                        <i key={i} />
                      ))}
                    </div>
                  )}

                  {showRegions && (
                    <div className="region-overlay">
                      {REGIONS.map((region) => (
                        <button
                          key={region.id}
                          title={region.label}
                          className={
                            lockedRegion?.id === region.id ? "locked" : ""
                          }
                          style={{
                            left: `${region.x}%`,
                            top: `${region.y}%`,
                            width: `${region.w}%`,
                            height: `${region.h}%`,
                          }}
                          onMouseEnter={() => setHoverRegion(region)}
                          onMouseLeave={() => setHoverRegion(null)}
                          onClick={() =>
                            setLockedRegion((old) =>
                              old?.id === region.id ? null : region
                            )
                          }
                        >
                          <span>{region.label}</span>
                        </button>
                      ))}
                    </div>
                  )}

                  {showNodes &&
                    components.map((c, idx) => {
                      const p = componentPoint(c, result);
                      if (!p) return null;

                      return (
                        <button
                          key={`${c.lesion}-${idx}`}
                          className={`lesion-node ${LESION_META[c.lesion].colorClass}`}
                          style={{
                            left: `${p.x * 100}%`,
                            top: `${p.y * 100}%`,
                          }}
                          title={`${LESION_META[c.lesion].full} · ${pct(
                            c.confidence ?? c.mean_confidence,
                            1
                          )}`}
                          onMouseEnter={() => setHoverNode({ ...c, p })}
                          onMouseLeave={() => setHoverNode(null)}
                        />
                      );
                    })}

                  {hoverNode && (
                    <div
                      className="node-tooltip"
                      style={{
                        left: `${hoverNode.p.x * 100}%`,
                        top: `${hoverNode.p.y * 100}%`,
                      }}
                    >
                      <strong>{LESION_META[hoverNode.lesion].full}</strong>
                      <span>
                        Confidence{" "}
                        {pct(
                          hoverNode.confidence ??
                            hoverNode.mean_confidence,
                          1
                        )}
                      </span>
                      <span>
                        Component area{" "}
                        {Number(
                          hoverNode.area_px || hoverNode.area || 0
                        ).toLocaleString()}{" "}
                        px
                      </span>
                    </div>
                  )}
                </div>

                <div className="retina-legend">
                  {Object.entries(LESION_META).map(([k, meta]) => (
                    <div key={k}>
                      <i className={meta.colorClass} />
                      <strong>{meta.full}</strong>
                    </div>
                  ))}
                </div>
              </div>

              <aside className="region-inspector">
                <span>REGION INSPECTOR</span>

                {!activeRegion ? (
                  <>
                    <h2>Hover a retinal region</h2>
                    <p>
                      Move the cursor across the retinal field to inspect local
                      pathology. Click a region to lock it while you compare
                      lesion types.
                    </p>
                  </>
                ) : (
                  <>
                    <h2>{activeRegion.label}</h2>

                    {hasLocalizedComponents ? (
                      <>
                        <div className="region-total">
                          <span>Localized lesion components</span>
                          <b>{activeRegionStats.total}</b>
                        </div>

                        {Object.entries(LESION_META).map(([k, meta]) => (
                          <div className="region-lesion" key={k}>
                            <div>
                              <strong>{meta.full}</strong>
                              <p>{meta.short}</p>
                            </div>
                            <b>{activeRegionStats[k]}</b>
                          </div>
                        ))}

                        <div className="region-meta">
                          <div>
                            <span>Combined component area</span>
                            <b>
                              {activeRegionStats.area.toLocaleString()} px
                            </b>
                          </div>
                          <div>
                            <span>Mean component confidence</span>
                            <b>
                              {activeRegionStats.meanConfidence == null
                                ? "—"
                                : pct(activeRegionStats.meanConfidence, 1)}
                            </b>
                          </div>
                        </div>
                      </>
                    ) : (
                      <div className="mvp-explainer warning">
                        <AlertTriangle size={16} />
                        <p>
                          Regional geometry is available, but this result does
                          not contain localized lesion components. Whole-retina
                          evidence is shown instead of inventing regional
                          values.
                        </p>
                      </div>
                    )}
                  </>
                )}

                <div className="region-note">
                  <Info size={15} />
                  <p>
                    Regions are screen-coordinate sectors for interactive
                    localization. Anatomical nasal/temporal naming requires
                    reliable eye laterality metadata and is not guessed here.
                  </p>
                </div>
              </aside>
            </div>

            <div className="lesion-education-grid">
              {Object.entries(LESION_META).map(([k, meta]) => {
                const v = result.lesions?.[k] || {};
                return (
                  <article key={k}>
                    <div className="lesion-title">
                      <i className={meta.colorClass} />
                      <div>
                        <span>{k}</span>
                        <h3>{meta.full}</h3>
                      </div>
                    </div>
                    <p>{meta.short}</p>

                    <div className="lesion-values">
                      <Metric label="Detected regions" value={v.count || 0} />
                      <Metric
                        label="Retinal burden"
                        value={`${((v.retinal_area_fraction || 0) * 100).toFixed(
                          4
                        )}%`}
                      />
                      <Metric
                        label="Mean confidence"
                        value={pct(v.mean_confidence, 1)}
                      />
                    </div>
                  </article>
                );
              })}
            </div>

            <div className="mvp-three-col">
              <div className="mvp-panel">
                <div className="mvp-panel-heading">
                  <BarChart3 size={17} />
                  <div>
                    <span>LESION COUNT GRAPH</span>
                    <h3>Number of connected lesion regions</h3>
                  </div>
                </div>
                {Object.entries(LESION_META).map(([k, meta]) => (
                  <Bar
                    key={k}
                    label={meta.full}
                    value={result.lesions?.[k]?.count || 0}
                    max={Math.max(
                      ...Object.keys(LESION_META).map(
                        (x) => result.lesions?.[x]?.count || 0
                      ),
                      1
                    )}
                    suffix=""
                  />
                ))}
              </div>

              <div className="mvp-panel">
                <div className="mvp-panel-heading">
                  <Layers3 size={17} />
                  <div>
                    <span>RETINAL BURDEN GRAPH</span>
                    <h3>Fraction of retinal area affected</h3>
                  </div>
                </div>
                {Object.entries(LESION_META).map(([k, meta]) => (
                  <Bar
                    key={k}
                    label={meta.full}
                    value={
                      (result.lesions?.[k]?.retinal_area_fraction || 0) * 100
                    }
                    max={Math.max(
                      ...Object.keys(LESION_META).map(
                        (x) =>
                          (result.lesions?.[x]?.retinal_area_fraction || 0) *
                          100
                      ),
                      0.01
                    )}
                    suffix="%"
                  />
                ))}
              </div>

              <div className="mvp-panel">
                <div className="mvp-panel-heading">
                  <Activity size={17} />
                  <div>
                    <span>LESION CONFIDENCE GRAPH</span>
                    <h3>Mean segmentation confidence</h3>
                  </div>
                </div>
                {Object.entries(LESION_META).map(([k, meta]) => (
                  <Bar
                    key={k}
                    label={meta.full}
                    value={(result.lesions?.[k]?.mean_confidence || 0) * 100}
                  />
                ))}
              </div>
            </div>

            <div className="slicing-explainer">
              <div>
                <span>WHY 512×512 SLICING?</span>
                <h3>Small lesions can disappear when an entire retina is aggressively resized.</h3>
                <p>
                  NetraAI preserves local detail by evaluating overlapping
                  high-resolution tiles. Predictions are projected back into
                  the full retinal coordinate system and overlap is reconciled
                  before connected lesion components are measured.
                </p>
              </div>

              <div className="slicing-graphic">
                {Array.from({ length: 20 }).map((_, i) => (
                  <i key={i}>
                    {i === 6 || i === 7 || i === 11 ? <CircleDot size={9} /> : null}
                  </i>
                ))}
              </div>
            </div>
          </section>
        )}

        {stage === "anatomy" && result && (
          <StructuralRetinaPanel
            result={result}
            preview={preview}
          />
        )}

        {stage === "xai" && result && (
          <section className="mvp-stage">
            <div className="mvp-stage-title">
              <span>06 · EXPLAINABILITY</span>
              <h1>Where did the global model pay attention?</h1>
              <p>
                Grad-CAM provides an attribution map for the global classifier.
                NetraAI does not treat the heatmap as pathology proof. Instead,
                the system checks whether attribution remains inside the retinal
                field and whether it overlaps independently detected lesion
                evidence.
              </p>
            </div>

            <div className="mvp-two-col">
              <div className="mvp-image-card xai-image">
                <span>GRAD-CAM ATTRIBUTION</span>
                <img src={artifact(result.artifacts?.gradcam)} alt="Grad-CAM attribution" />
                <div className="mvp-image-caption">
                  Warmer regions indicate stronger contribution to the global
                  classifier's selected class.
                </div>
              </div>

              <div className="mvp-panel">
                <ScoreGauge
                  label="XAI integrity"
                  value={result.xai_integrity.score}
                  subtitle="Explanation reliability"
                  footnote="A system-level integrity indicator; not a proof of causal faithfulness."
                />

                <Bar
                  label="Attribution inside retinal field-of-view"
                  value={result.xai_integrity.attribution_in_retinal_fov}
                  note="Checks whether the explanation remains focused on the retina."
                />
                <Bar
                  label="Attribution overlapping lesion evidence"
                  value={result.xai_integrity.attribution_lesion_overlap}
                  note="Checks agreement between global attention and independently segmented pathology."
                />

                <div className="mvp-explainer">
                  <Info size={16} />
                  <p>
                    Low lesion overlap does not automatically mean the
                    prediction is wrong. It lowers explanation integrity and
                    can increase the need for human review.
                  </p>
                </div>
              </div>
            </div>
          </section>
        )}

        {stage === "trust" && result && (
          <section className="mvp-stage">
            <div className="mvp-stage-title">
              <span>07 · TRACE-DR RELIABILITY FUSION</span>
              <h1>A prediction is not enough. Can its evidence be trusted?</h1>
              <p>
                TRACE-DR combines pathology evidence, model confidence, image
                reliability, evidence concordance and explanation integrity so
                NetraAI can route uncertain cases instead of hiding
                disagreement.
              </p>
            </div>

            <div className="trace-grid">
              <div className="mvp-panel">
                <ScoreGauge
                  label="P-Score"
                  value={result.p_score}
                  subtitle="Pathology Evidence Score"
                  footnote="Prototype pathology-evidence index, not an established clinical score."
                />

                <div className="formula-note">
                  30% Microaneurysm evidence + 30% Hemorrhage evidence + 25%
                  Hard-exudate evidence + 15% Soft-exudate evidence
                </div>

                {[
                  ["Microaneurysm contribution", "MA", 30],
                  ["Hemorrhage contribution", "HE", 30],
                  ["Hard-exudate contribution", "EX", 25],
                  ["Soft-exudate contribution", "SE", 15],
                ].map(([label, key, weight]) => (
                  <Bar
                    key={key}
                    label={label}
                    value={(result.lesions?.[key]?.mean_confidence || 0) * weight}
                    max={weight}
                    suffix=""
                  />
                ))}
              </div>

              <div className="mvp-panel">
                <ScoreGauge
                  label="T-Score"
                  value={result.t_score.score}
                  subtitle={`${result.t_score.level} trustworthiness`}
                  footnote="Prototype system trust index, not an established clinical score."
                />

                <Bar label="Image reliability" value={result.quality.score * 100} />
                <Bar label="Model confidence" value={result.prediction.grade_confidence * 100} />
                <Bar label="Evidence concordance" value={result.concordance.score} />
                <Bar label="XAI integrity" value={result.xai_integrity.score} />
                <Bar
                  label="Stability term"
                  value={90}
                  note="Current prototype stability term; should be returned explicitly by the backend in the next iteration."
                />
              </div>

              <div className="mvp-panel concordance-card">
                <span>PATHOLOGY CONCORDANCE</span>
                <strong>{result.concordance.score}</strong>
                <b>{result.concordance.status}</b>

                <p>
                  Concordance checks whether the predicted ICDR severity is
                  consistent with the lesion branch rather than blindly trusting
                  one model output.
                </p>

                <h4>Supporting evidence</h4>
                <ul>
                  {result.concordance.supporting_evidence?.map((x) => (
                    <li key={x}>
                      <CheckCircle2 size={14} />
                      {x}
                    </li>
                  ))}
                </ul>

                {result.concordance.conflicting_evidence?.length > 0 && (
                  <>
                    <h4>Conflicting evidence</h4>
                    <ul className="conflict-list">
                      {result.concordance.conflicting_evidence.map((x) => (
                        <li key={x}>
                          <AlertTriangle size={14} />
                          {x}
                        </li>
                      ))}
                    </ul>
                  </>
                )}
              </div>
            </div>

            <div className="trace-chain">
              {[
                ["T", "Triage quality", "Reject or enhance unreliable acquisitions."],
                ["R", "Retain evidence", "Keep lesion and model evidence instead of only a final label."],
                ["A", "Align clinically", "Check grade-versus-pathology concordance."],
                ["C", "Calibrate", "Expose uncertainty and confidence limitations."],
                ["E", "Escalate", "Route poor-quality or low-trust cases to recapture or human review."],
              ].map(([letter, title, text]) => (
                <article key={letter}>
                  <b>{letter}</b>
                  <strong>{title}</strong>
                  <p>{text}</p>
                </article>
              ))}
            </div>
          </section>
        )}

        {stage === "decision" && result && (
          <section className="mvp-stage decision-stage">
            <div className="mvp-stage-title">
              <span>08 · SCREENING DECISION</span>
              <h1>From evidence to an actionable route.</h1>
              <p>
                NetraAI's final output is a screening route, not an autonomous
                diagnosis. The system preserves the reason for that route so a
                reviewer can understand what drove escalation.
              </p>
            </div>

            <div className="decision-hero">
              <span>FINAL ROUTING</span>
              <strong>
                {result.recommendation.action.replaceAll("_", " ")}
              </strong>
              <b>{result.recommendation.priority} PRIORITY</b>
              <p>{result.recommendation.reason}</p>
            </div>

            <div className="decision-summary">
              <Metric
                label="ICDR severity"
                value={`Grade ${result.prediction.icdr_grade}`}
                detail={result.prediction.grade_name}
              />
              <Metric
                label="Referable DR"
                value={result.prediction.referable_dr ? "Positive" : "Negative"}
                detail={`Probability ${pct(result.prediction.rdr_probability, 2)}`}
              />
              <Metric
                label="Image quality"
                value={result.quality.status}
                detail={`${(result.quality.score * 100).toFixed(1)}% reliability`}
              />
              <Metric
                label="Pathology evidence"
                value={`${result.p_score}/100`}
                detail="P-Score"
              />
              <Metric
                label="Concordance"
                value={`${result.concordance.score}/100`}
                detail={result.concordance.status}
              />
              <Metric
                label="Trustworthiness"
                value={`${result.t_score.score}/100`}
                detail={result.t_score.level}
              />
            </div>

            <div className="decision-explanation">
              <ShieldCheck size={24} />
              <div>
                <strong>Reviewer-facing explanation</strong>
                <p>
                  NetraAI predicted{" "}
                  <b>
                    Grade {result.prediction.icdr_grade} ·{" "}
                    {result.prediction.grade_name}
                  </b>{" "}
                  with raw grade confidence{" "}
                  <b>{pct(result.prediction.grade_confidence, 1)}</b>. The
                  pathology branch detected{" "}
                  <b>{result.lesions?.MA?.count || 0} microaneurysm</b>,{" "}
                  <b>{result.lesions?.HE?.count || 0} hemorrhage</b>,{" "}
                  <b>{result.lesions?.EX?.count || 0} hard-exudate</b> and{" "}
                  <b>{result.lesions?.SE?.count || 0} soft-exudate</b>{" "}
                  components. Evidence concordance is{" "}
                  <b>{result.concordance.score}/100</b>, while XAI integrity is{" "}
                  <b>{result.xai_integrity.score}/100</b>. These signals produce
                  a prototype trustworthiness score of{" "}
                  <b>{result.t_score.score}/100</b>, leading to the route above.
                </p>
              </div>
            </div>

            {reportUrl && (
              <button className="report-preview-button" onClick={() => setShowPdf(true)}>
                <FileText size={18} />
                Preview detailed analysis report
              </button>
            )}
          </section>
        )}

        {stage === "report" && result && (
          <section className="mvp-stage">
            <div className="mvp-stage-title">
              <span>09 · EXPLAINABLE REPORT</span>
              <h1>A complete reviewer-facing record.</h1>
              <p>
                The report combines the screening decision with visual evidence
                and reliability context so the output is useful beyond a single
                probability score.
              </p>
            </div>

            {reportUrl ? (
              <div className="report-workspace">
                <div className="report-summary-list">
                  {[
                    ["Screening severity", `Grade ${result.prediction.icdr_grade} · ${result.prediction.grade_name}`],
                    ["Referable DR", result.prediction.referable_dr ? "Positive" : "Negative"],
                    ["P-Score", `${result.p_score}/100`],
                    ["Concordance", `${result.concordance.score}/100 · ${result.concordance.status}`],
                    ["XAI integrity", `${result.xai_integrity.score}/100`],
                    ["T-Score", `${result.t_score.score}/100 · ${result.t_score.level}`],
                    ["Routing", result.recommendation.action.replaceAll("_", " ")],
                  ].map(([a, b]) => (
                    <div key={a}>
                      <span>{a}</span>
                      <strong>{b}</strong>
                    </div>
                  ))}

                  <button onClick={() => setShowPdf(true)}>
                    <FileText size={17} />
                    Open report preview
                  </button>

                  <a href={reportUrl} target="_blank" rel="noreferrer">
                    <Download size={17} />
                    Open PDF in new tab
                  </a>
                </div>

                <iframe
                  className="inline-report-preview"
                  src={reportUrl}
                  title="NetraAI detailed analysis report"
                />
              </div>
            ) : (
              <div className="mvp-explainer warning">
                <AlertTriangle size={16} />
                <p>
                  The current backend response does not include a PDF report
                  artifact. Run the backend version with report generation
                  enabled to preview it here.
                </p>
              </div>
            )}
          </section>
        )}
      </main>

      {showPdf && reportUrl && (
        <PdfPreview url={reportUrl} onClose={() => setShowPdf(false)} />
      )}
    </div>
  );
}
