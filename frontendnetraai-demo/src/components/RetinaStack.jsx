import {
  Activity,
  BrainCircuit,
  Layers3,
  Microscope,
  ShieldCheck,
} from "lucide-react";

const callouts = [
  {
    id: "quality",
    number: "01",
    title: "Quality Gate",
    description:
      "Checks focus, illumination, contrast and retinal field-of-view before disease grading.",
    icon: Activity,
  },
  {
    id: "global",
    number: "02",
    title: "Global DR Grading",
    description:
      "Predicts ICDR Grade 0–4 and the probability of referable diabetic retinopathy.",
    icon: BrainCircuit,
  },
  {
    id: "tiles",
    number: "03",
    title: "512×512 Retinal Slicing",
    description:
      "Overlapping high-resolution tiles preserve tiny pathological details that could disappear during whole-image resizing.",
    icon: Layers3,
  },
  {
    id: "local",
    number: "04",
    title: "Local Lesion Evidence",
    description:
      "Microaneurysms · Retinal Hemorrhages · Hard Exudates · Soft Exudates / Cotton-Wool Spots",
    icon: Microscope,
  },
  {
    id: "trace",
    number: "05",
    title: "TRACE-DR Reliability",
    description:
      "Combines image quality, model confidence, pathology concordance and explanation integrity before routing the case.",
    icon: ShieldCheck,
  },
];

export default function RetinaStack() {
  return (
    <section className="netra-hero-figure">
      <div className="netra-figure-kicker">
        <span>EXPLAINABLE RETINAL INTELLIGENCE</span>
        <i />
        <b>GLOBAL + LOCAL + TRUST</b>
      </div>

      <div className="netra-figure-stage">

        {/* SVG connectors remain crisp and readable */}
        <svg
          className="netra-connectors"
          viewBox="0 0 1200 720"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          <defs>
            <filter id="connectorGlow">
              <feGaussianBlur stdDeviation="2.4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            <linearGradient id="connectorGradient" x1="0" x2="1">
              <stop offset="0%" stopColor="#55dfff" stopOpacity="0.34" />
              <stop offset="45%" stopColor="#78e9ff" stopOpacity="0.95" />
              <stop offset="100%" stopColor="#55dfff" stopOpacity="0.45" />
            </linearGradient>
          </defs>

          <g
            fill="none"
            stroke="url(#connectorGradient)"
            strokeWidth="2"
            filter="url(#connectorGlow)"
          >
            <path d="M 446 270 C 350 270, 322 210, 210 210" />
            <path d="M 754 250 C 860 250, 890 178, 1010 178" />
            <path d="M 790 355 C 880 355, 900 355, 1015 355" />
            <path d="M 438 450 C 342 450, 310 525, 195 525" />
            <path d="M 755 475 C 858 475, 900 565, 1010 565" />
          </g>

          <g fill="#8cecff" filter="url(#connectorGlow)">
            <circle cx="446" cy="270" r="5" />
            <circle cx="754" cy="250" r="5" />
            <circle cx="790" cy="355" r="5" />
            <circle cx="438" cy="450" r="5" />
            <circle cx="755" cy="475" r="5" />
          </g>

          <g
            fill="none"
            stroke="#44cceb"
            strokeWidth="1"
            strokeDasharray="4 8"
            opacity="0.34"
          >
            <ellipse cx="600" cy="355" rx="286" ry="224" />
            <ellipse cx="600" cy="355" rx="350" ry="277" />
            <ellipse cx="600" cy="355" rx="420" ry="330" />
          </g>
        </svg>

        {/* Retina */}
        <div className="netra-retina-core">
          <div className="netra-retina-halo halo-one" />
          <div className="netra-retina-halo halo-two" />

          <div className="netra-retina-image-wrap">
            <img
              src="/demo/grade2.png"
              alt="Retinal fundus demonstration image"
            />

            <div className="netra-scan-line" />

            <div className="netra-core-label">
              <span>FUNDUS INPUT</span>
              <strong>RETINAL FIELD</strong>
            </div>
          </div>
        </div>

        {/* Real HTML labels — not canvas text */}
        <div className="netra-callout netra-callout-quality">
          <Callout item={callouts[0]} />
        </div>

        <div className="netra-callout netra-callout-global">
          <Callout item={callouts[1]} />
        </div>

        <div className="netra-callout netra-callout-tiles">
          <Callout item={callouts[2]} />
        </div>

        <div className="netra-callout netra-callout-local">
          <Callout item={callouts[3]} />
        </div>

        <div className="netra-callout netra-callout-trace">
          <Callout item={callouts[4]} />
        </div>
      </div>

      <div className="netra-figure-explanation">
        <div>
          <span>GLOBAL ANALYSIS</span>
          <p>
            The full retina is evaluated for diabetic-retinopathy severity
            and referable disease probability.
          </p>
        </div>

        <div>
          <span>LOCAL ANALYSIS</span>
          <p>
            High-resolution tiles preserve small lesions and map detected
            pathology back to the complete retinal image.
          </p>
        </div>

        <div>
          <span>EXPLAINABILITY</span>
          <p>
            Grad-CAM attribution and independent lesion evidence are compared
            rather than relying on a single opaque prediction.
          </p>
        </div>

        <div>
          <span>RELIABILITY</span>
          <p>
            TRACE-DR checks whether image quality, prediction and evidence
            agree before generating a screening route.
          </p>
        </div>
      </div>
    </section>
  );
}

function Callout({ item }) {
  const Icon = item.icon;

  return (
    <article className="netra-callout-card">
      <div className="netra-callout-top">
        <b>{item.number}</b>
        <Icon size={15} />
        <strong>{item.title}</strong>
      </div>

      <p>{item.description}</p>
    </article>
  );
}
