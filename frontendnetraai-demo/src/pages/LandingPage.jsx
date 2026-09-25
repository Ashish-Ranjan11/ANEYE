import { Link } from "react-router-dom";
import { ArrowRight, ScanEye, ShieldCheck, Layers3, BrainCircuit, Radar, Camera, RefreshCw, CheckCircle2, AlertTriangle } from "lucide-react";
import RetinaStack from "../components/RetinaStack";
import ProofNumbers from "../components/ProofNumbers";
import LandingFooter from "../components/LandingFooter";

const caseMetrics = [
  ["Quality", "61.7", "Gradeable"],
  ["ICDR", "G2", "Moderate NPDR"],
  ["RDR", "98.22%", "Calibrated · referable"],
  ["P-Score", "76.6", "Pathology evidence"],
  ["Concordance", "90.1", "High"],
  ["T-Score", "79.6", "Moderate trust"],
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
          <a href="#deployment">Deployment</a>
        </div>
        <Link className="judge-cta" to="/engine"><ScanEye size={16}/> Run engine</Link>
      </nav>

      <section className="judge-hero">
        <div className="judge-hero-copy">
          <div className="micro-label"><span/> SIH26038 · EXPLAINABLE DR SCREENING</div>
          <h1>Not another<br/><em>black-box</em><br/>retinal classifier.</h1>
          <p className="hero-lead">Built for rural screening workflows: NetraAI checks whether a portable-camera image is safe to grade, exposes the retinal evidence behind the result, and routes uncertain cases for recapture or specialist review.</p>
          <div className="hero-actions">
            <Link to="/engine" className="primary-action">Open screening engine <ArrowRight size={17}/></Link>
            <a href="#case" className="secondary-action">See one real case</a>
          </div>
          <div className="hero-rule" />
          <div className="hero-capsules">
            <span>QUALITY FIRST</span><span>ICDR 0–4</span><span>RDR ≥ 2</span><span>MA · HE · EX · SE</span><span>TRACE-DR</span>
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

      <section className="rural-demo section-shell" id="field-demo">
        <div className="rural-demo-head">
          <div>
            <span className="micro-label">RURAL FIELD WORKFLOW · QUALITY BEFORE CLASSIFICATION</span>
            <h2>Same screening system. Two very different safety decisions.</h2>
            <p>A field photograph is graded only when acquisition quality is adequate. Poor captures are stopped before disease inference and returned with recapture guidance.</p>
          </div>
          <Link to="/engine" className="primary-action">Try field screening <ArrowRight size={17}/></Link>
        </div>
        <div className="rural-compare">
          <article className="rural-case reject">
            <div className="rural-case-icon"><Camera size={22}/><AlertTriangle size={18}/></div>
            <span>FIELD CAPTURE A</span><h3>Poor-quality acquisition</h3>
            <div className="rural-checks"><b>Focus <i>FAIL</i></b><b>Illumination <i>CHECK</i></b><b>Retinal FOV <i>INSUFFICIENT</i></b></div>
            <strong>UNGRADEABLE · AI GRADING BLOCKED</strong>
            <p>Re-centre the retina, stabilise the camera/patient and reacquire a sharper image with sufficient field of view.</p>
            <div className="rural-route"><RefreshCw size={16}/> RECAPTURE</div>
          </article>
          <div className="rural-vs">VS</div>
          <article className="rural-case accept">
            <div className="rural-case-icon"><ScanEye size={22}/><CheckCircle2 size={18}/></div>
            <span>FIELD CAPTURE B</span><h3>Gradeable acquisition</h3>
            <div className="rural-checks"><b>Focus <i>PASS</i></b><b>Illumination <i>PASS</i></b><b>Retinal FOV <i>PASS</i></b></div>
            <strong>GRADEABLE · CONTINUE TO NETRAAI</strong>
            <p>Run ICDR + calibrated RDR inference, lesion evidence, Grad-CAM, trust checks and TRACE-DR routing.</p>
            <div className="rural-route"><ShieldCheck size={16}/> EXPLAIN → REVIEW → ROUTE</div>
          </article>
        </div>
        <div className="rural-flow"><span>Rural PHC / screening camp</span><i>→</i><span>Portable fundus capture</span><i>→</i><span>Quality gate</span><i>→</i><span>NetraAI V3</span><i>→</i><span>Human review / referral</span></div>
      </section>

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
          <div><b>TRACE-DR</b><span>P 76.6 · T 79.6 · Concordance 90.1</span></div><i>→</i>
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


      <section className="deployment-story section-shell" id="deployment">
        <div className="deployment-head">
          <div><span className="micro-label">SIMULINK DISTRICT DIGITAL TWIN</span><h2>From one retinal image to 100,000 screenings a year.</h2><p>The same quality-first workflow is stress-tested against acquisition capacity, recapture load and rural bandwidth before deployment.</p></div>
          <div className="deployment-status"><span>BASELINE</span><strong>STABLE</strong><small>2 stations · 10 Mbps · 5% recapture</small></div>
        </div>
        <div className="deployment-flow"><span>Rural screening</span><i>→</i><span>Acquisition</span><i>→</i><span>Quality / recapture</span><i>→</i><span>Store & forward</span><i>→</i><span>NetraAI V3</span><i>→</i><span>TRACE review</span></div>
        <div className="deployment-metrics">
          <article><span>ANNUAL TARGET</span><strong>100,000</strong><small>screenings / year</small></article>
          <article><span>ACQUISITION</span><strong>2</strong><small>fundus stations</small></article>
          <article><span>CAMERA UTIL.</span><strong>73.1%</strong><small>5% recapture baseline</small></article>
          <article><span>NETWORK UTIL.</span><strong>4.69%</strong><small>at 10 Mbps</small></article>
          <article><span>AI UTIL.</span><strong>3.92%</strong><small>baseline model</small></article>
        </div>
        <div className="deployment-insights">
          <article><b>RECAPTURE STRESS</b><p>One acquisition station is overloaded. Two remain stable through the baseline and approach saturation as recapture rises toward 30%; three provide additional resilience.</p></article>
          <article><b>BANDWIDTH STRESS</b><p>At 0.5 Mbps the network approaches saturation, while the 10 Mbps baseline leaves substantial transmission headroom for store-and-forward screening.</p></article>
          <article><b>WHY SIMULINK</b><p>The digital twin turns model accuracy into an operational question: how many cameras, how much bandwidth and how much review capacity are required for a district programme?</p></article>
        </div>
        <p className="deployment-note">Operational figures are outputs of the current NetraAI Simulink/SimEvents resource model and depend on its stated acquisition, transmission and routing assumptions.</p>
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