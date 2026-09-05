import { useEffect, useRef, useState } from "react";

const DATA = [
  {
    value: 19,
    suffix: "K+",
    title: "Retinal data samples",
    description:
      "Images and high-resolution training tiles handled across the retinal-development workflow.",
  },
  {
    value: 3,
    suffix: "",
    title: "Core retinal datasets",
    description:
      "APTOS 2019, IDRiD and ODIR-5K used across classification and lesion-development stages.",
  },
  {
    value: 93,
    suffix: "",
    title: "Tiles per demo retina",
    description:
      "High-resolution retinal tiles processed in the current Grade-2 demonstration case.",
  },
  {
    value: 2,
    suffix: "",
    title: "Specialist AI branches",
    description:
      "Whole-retina severity grading and local lesion segmentation operate as separate evidence streams.",
  },
];

function AnimatedNumber({ value, suffix }) {
  const ref = useRef(null);
  const [display, setDisplay] = useState(0);
  const [active, setActive] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setActive(true);
          observer.disconnect();
        }
      },
      { threshold: 0.3 }
    );

    observer.observe(el);

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!active) return;

    const duration = 1100;
    const start = performance.now();

    function frame(now) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 4);

      setDisplay(Math.round(value * eased));

      if (progress < 1) {
        requestAnimationFrame(frame);
      }
    }

    requestAnimationFrame(frame);
  }, [active, value]);

  return (
    <strong ref={ref} className="proof-number">
      {display}
      <span>{suffix}</span>
    </strong>
  );
}

export default function ProofNumbers() {
  return (
    <section className="proof-section">

      <div className="proof-intro">
        <span>NETRAAI BY THE NUMBERS</span>

        <h2>
          Built around multiple retinal
          evidence streams.
        </h2>

        <p>
          NetraAI combines whole-retina classification,
          high-resolution lesion analysis and explainability
          into a single screening workflow.
        </p>
      </div>

      <div className="proof-stat-grid">
        {DATA.map((item) => (
          <article className="proof-stat-card" key={item.title}>
            <AnimatedNumber
              value={item.value}
              suffix={item.suffix}
            />

            <h3>{item.title}</h3>

            <p>{item.description}</p>
          </article>
        ))}
      </div>

      <div className="proof-stack">

        <div className="proof-stack-label">
          MODEL STACK
        </div>

        <div className="proof-stack-items">

          <div>
            <strong>EfficientNet-B0</strong>
            <span>Global ICDR severity</span>
          </div>

          <i />

          <div>
            <strong>U-Net + EfficientNet-B0</strong>
            <span>Lesion segmentation</span>
          </div>

          <i />

          <div>
            <strong>Grad-CAM</strong>
            <span>Global attribution</span>
          </div>

          <i />

          <div>
            <strong>TRACE-DR</strong>
            <span>Evidence reliability</span>
          </div>

        </div>

      </div>

    </section>
  );
}
