import { Link } from "react-router-dom";
import { ArrowRight, ScanEye, ShieldCheck, Layers3, BrainCircuit, Radar } from "lucide-react";
import RetinaStack from "../components/RetinaStack";
import ProofNumbers from "../components/ProofNumbers";
import LandingFooter from "../components/LandingFooter";

const caseMetrics = [
  ["Quality", "61.7", "Gradeable"],
  ["ICDR", "G2", "Moderate NPDR"],
  ["RDR", "99.3%", "Referable"],
  ["P-Score", "76.6", "Pathology evidence"],
  ["Concordance", "90.1", "High"],
  ["T-Score", "76.2", "Moderate trust"],
];

export default function LandingPage() {
  return (
    <div className="judge-page">
      <nav className="judge-nav">
        <Link to="/" className="judge-logo"><img src="/netraai-logo.png" alt="NetraAI" /></Link>
        <div className="judge-links">
          <a href="#why">Why NetraAI</a>
          <a href="#case">Live case</a>
          <a href="#architecture">Architecture</a>
        </div>
        <Link className="judge-cta" to="/engine"><ScanEye size={16}/> Run engine</Link>
      </nav>

      <section className="judge-hero">
        <div className="judge-hero-copy">
          <div className="micro-label"><span/> SIH26038 · EXPLAINABLE DR SCREENING</div>
          <h1>Not another<br/><em>black-box</em><br/>retinal classifier.</h1>
          <p className="hero-lead">NetraAI shows the image quality, the global grade, the local pathology, the explanation integrity and the trust behind every referral decision.</p>
          <div className="hero-actions">
            <Link to="/engine" className="primary-action">Open screening engine <ArrowRight size={17}/></Link>
            <a href="#case" className="secondary-action">See one real case</a>
          </div>
          <div className="hero-rule" />
          <div className="hero-capsules">
            <span>ICDR 0–4</span><span>RDR ≥ 2</span><span>MA · HE · EX · SE</span><span>TRACE-DR</span>
          </div>
        </div>
        <div className="judge-hero-visual"><RetinaStack />

      </div>
      </section>

      <section id="why" className="manifesto section-shell">
        <div className="manifesto-index">01</div>
        <div className="manifesto-copy">
          <span className="micro-label">THE DIFFERENCE</span>
          <h2>A grade is not enough.<br/>We expose the evidence chain.</h2>
        </div>
        <div className="manifesto-grid">
          <article><BrainCircuit/><strong>Global disease context</strong><p>ICDR severity and referable-DR screening from the whole fundus.</p></article>
          <article><Layers3/><strong>Local pathology evidence</strong><p>Overlapping high-resolution retinal tiles preserve tiny lesion signals.</p></article>
          <article><Radar/><strong>Explanation integrity</strong><p>Grad-CAM is checked against the retinal field and independent lesion evidence.</p></article>
          <article><ShieldCheck/><strong>Reliability-aware routing</strong><p>Image reliability, confidence, concordance and XAI integrity drive review or referral.</p></article>
        </div>
      </section>

      

      <ProofNumbers />

<section id="case" className="case-story section-shell">
        <div className="case-head">
          <div>
            <span className="micro-label">REAL SYSTEM CASE · APTOS 2019</span>
            <h2>Case 000c1434d8d7</h2>
            <p>Dataset label: Grade 2. The values below are the actual NetraAI integrated output for this case.</p>
          </div>
          <Link to="/engine?demo=grade2" className="primary-action">Run this case live <ArrowRight size={17}/></Link>
        </div>

        <div className="case-grid">
          <div className="case-image-panel">
            <img src="/demo/grade2.png" alt="APTOS Grade 2 fundus" />
            <div className="case-image-tags"><span>Original fundus</span><span>APTOS · G2</span></div>
          </div>
          <div className="case-metrics">
            {caseMetrics.map(([label,value,sub]) => (
              <div className="case-metric" key={label}><span>{label}</span><strong>{value}</strong><small>{sub}</small></div>
            ))}
          </div>
        </div>

        <div className="evidence-chain">
          <div><b>QUALITY</b><span>Focus · illumination · contrast · FOV</span></div><i>→</i>
          <div><b>GLOBAL</b><span>Grade 2 · RDR positive</span></div><i>→</i>
          <div><b>LOCAL</b><span>MA 26 · HE 9 · EX 90</span></div><i>→</i>
          <div><b>TRACE-DR</b><span>P 76.6 · T 76.2</span></div><i>→</i>
          <div className="decision-node"><b>ACTION</b><span>Refer ophthalmology</span></div>
        </div>
      </section>

      <section id="architecture" className="architecture-editorial section-shell">
        <div className="architecture-copy">
          <span className="micro-label">SYSTEM ARCHITECTURE</span>
          <h2>Global context and local evidence meet only after independent inference.</h2>
          <p>That separation is deliberate: the lesion branch is not used as decoration. It acts as an independent evidence channel for concordance and reliability.</p>
        </div>
        <div className="architecture-board">
          <div className="arch-source">FUNDUS IMAGE</div>
          <div className="arch-down">↓</div>
          <div className="arch-node arch-wide">QUALITY GATE + BOUNDED RESTORATION</div>
          <div className="arch-down">↓</div>
          <div className="arch-split">
            <div><b>GLOBAL RETINA</b><span>EfficientNet-B0</span><small>ICDR 0–4 · RDR · Grad-CAM</small></div>
            <div><b>LOCAL TILES</b><span>IDRiD U-Net</span><small>MA · HE · EX · SE</small></div>
          </div>
          <div className="arch-down">↓</div>
          <div className="arch-node arch-wide">P-SCORE + CONCORDANCE + XAI INTEGRITY</div>
          <div className="arch-down">↓</div>
          <div className="arch-node arch-final">T-SCORE → CLINICAL ROUTING</div>
        </div>
      </section>

      <section className="final-statement section-shell">
        <img src="/netraai-logo.png" alt="NetraAI" />
        <h2>Make the model show its work.</h2>
        <p>Explainable diabetic-retinopathy screening for rural workflows, built around evidence rather than confidence alone.</p>
        <Link to="/engine" className="primary-action">Launch NetraAI <ArrowRight size={17}/></Link>
      </section>
    
      <LandingFooter />

</div>
  );
}