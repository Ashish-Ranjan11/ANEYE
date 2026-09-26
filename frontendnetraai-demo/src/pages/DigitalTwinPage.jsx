import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity, BrainCircuit, Camera, Eye, Network, Pause, Play,
  RefreshCw, ShieldCheck, Stethoscope, Wifi, Database,
  GitBranch, Layers3, Microscope, Gauge
} from "lucide-react";
import "./DigitalTwinPage.css";

const clamp = (v, a, b) => Math.min(b, Math.max(a, v));

const PIPELINE = [
  ["generator","PRIMARY SCREENING","Arrival generator",5,44,Activity],
  ["queue1","CAMERA QUEUE","Acquisition waiting",18,44,Layers3],
  ["camera","CAMERA POOL","Portable fundus capture",31,44,Camera],
  ["quality","QUALITY GATE","Focus · illumination · FOV",44,44,ShieldCheck],
  ["network","NETWORK","Store & forward",58,44,Wifi],
  ["ai","NETRAAI V3","Explainable DR engine",72,44,BrainCircuit],
  ["trace","TRACE ROUTER","Safety routing",85,44,GitBranch],
  ["review","SPECIALIST","Remote verification",95,44,Stethoscope],
];

export default function DigitalTwinPage() {
  const [running,setRunning] = useState(true);
  const [clock,setClock] = useState(0);
  const [cameras,setCameras] = useState(2);
  const [bandwidth,setBandwidth] = useState(10);
  const [recapture,setRecapture] = useState(5);
  const [showAI,setShowAI] = useState(true);

  useEffect(()=>{
    if(!running) return;
    const t=setInterval(()=>setClock(v=>v+1),800);
    return()=>clearInterval(t);
  },[running]);

  const M = useMemo(()=>{
    const interarrival=86.4;
    const lambda=1/interarrival;
    const p=recapture/100;
    const attempts=1/(1-p);

    const captureService=120;
    const payloadMB=5;
    const latency=.050;
    const aiService=3.38403;

    const networkService=(payloadMB*8)/bandwidth+latency;

    const lambdaCapture=lambda*attempts;
    const lambdaRecap=lambda*(p/(1-p));

    const cameraUtil=lambdaCapture/(cameras/captureService)*100;
    const networkUtil=lambda/(1/networkService)*100;
    const aiUtil=lambda/(1/aiService)*100;

    const ophth=lambda*.0995*30*100;
    const human=lambda*.0994*45*100;
    const recapPrep=lambdaRecap*20*100;

    const values=[
      cameraUtil,networkUtil,aiUtil,ophth,human,recapPrep
    ];

    return {
      attempts,
      networkService,
      camera:cameraUtil,
      network:networkUtil,
      ai:aiUtil,
      ophth,
      human,
      recapPrep,
      stable:values.every(v=>v<100)
    };
  },[cameras,bandwidth,recapture]);

  const cases=42864+clock*4;

  return (
    <main className="dt">

      <nav className="dt-product-nav">
        <Link to="/">NETRAAI</Link>

        <div>
          <Link to="/engine">CLINICAL WORKSTATION</Link>
          <Link className="active" to="/digital-twin">RURAL DIGITAL TWIN</Link>
          <a href="#architecture">SYSTEM ARCHITECTURE</a>
        </div>

        <span>SIH · RURAL DR SCREENING</span>
      </nav>

      <header className="dt-hero">
        <div>
          <span className="eyebrow">SIMULINK / SIMEVENTS DEPLOYMENT MODEL</span>

          <h1>
            Can NetraAI screen
            <em> 100,000+ patients/year?</em>
          </h1>

          <p>
            We model the healthcare pipeline—not only the neural network.
            Acquisition capacity, image recapture, rural bandwidth,
            AI processing and specialist workload are evaluated together.
          </p>
        </div>

        <div className={"dt-verdict "+(M.stable?"ok":"danger")}>
          <i/>
          <span>CURRENT CONFIGURATION</span>
          <strong>{M.stable ? "STABLE" : "RESOURCE SATURATION"}</strong>
          <small>
            {cameras} cameras · {bandwidth} Mbps · {recapture}% recapture
          </small>
        </div>
      </header>

      <section className="capacity-contract">
        <div className="contract-head">
          <div>
            <span>01 · CAPACITY CONTRACT</span>
            <h2>What does “100,000/year” actually assume?</h2>
          </div>

          <p>
            Inputs and operating assumptions used by the current
            R2026a SimEvents resource-sizing study.
          </p>
        </div>

        <div className="contract-grid">
          <Metric type="TARGET" value="100,000" label="annual screening cases"/>
          <Metric type="MODEL" value="86.4 s" label="primary interarrival"/>
          <Metric type="INPUT" value="120 s" label="fundus capture service"/>
          <Metric type="INPUT" value="5 MB" label="image payload"/>
          <Metric type="INPUT" value="50 ms" label="network latency"/>
          <Metric type="MODEL" value="3.384 s" label="AI service time"/>
          <Metric type="MODEL" value="30 s" label="ophthalmology service"/>
          <Metric type="MODEL" value="45 s" label="human review service"/>
          <Metric type="MODEL" value="20 s" label="recapture preparation"/>
        </div>

        <div className="contract-note">
          <ShieldCheck size={16}/>
          <p>
            Recapture percentage is an <b>engineering sensitivity variable</b>,
            not claimed as observed clinical or population prevalence.
          </p>
        </div>
      </section>

      <section className="experiment">
        <div className="section-title">
          <span>02 · RESOURCE-SIZING EXPERIMENT</span>
          <h2>147 deployment scenarios</h2>
        </div>

        <div className="experiment-equation">
          <div>
            <strong>3</strong>
            <span>camera configurations</span>
            <small>1 · 2 · 3</small>
          </div>

          <b>×</b>

          <div>
            <strong>7</strong>
            <span>bandwidth levels</span>
            <small>.5 · 1 · 2 · 5 · 10 · 20 · 50 Mbps</small>
          </div>

          <b>×</b>

          <div>
            <strong>7</strong>
            <span>recapture conditions</span>
            <small>0 · 5 · 10 · 20 · 30 · 40 · 50%</small>
          </div>

          <b>=</b>

          <div className="scenario-total">
            <strong>147</strong>
            <span>24-hour simulations</span>
            <small>resource sizing + stress analysis</small>
          </div>
        </div>
      </section>

      <section className="dt-controls">
        <label>
          <span>CAMERA POOL</span>
          <select value={cameras} onChange={e=>setCameras(+e.target.value)}>
            <option value="1">1 station</option>
            <option value="2">2 stations</option>
            <option value="3">3 stations</option>
          </select>
        </label>

        <label>
          <span>RURAL BANDWIDTH</span>
          <select value={bandwidth} onChange={e=>setBandwidth(+e.target.value)}>
            {[.5,1,2,5,10,20,50].map(x=>
              <option key={x} value={x}>{x} Mbps</option>
            )}
          </select>
        </label>

        <label>
          <span>RECAPTURE SENSITIVITY</span>
          <select value={recapture} onChange={e=>setRecapture(+e.target.value)}>
            {[0,5,10,20,30,40,50].map(x=>
              <option key={x} value={x}>{x}%</option>
            )}
          </select>
        </label>

        <button onClick={()=>setRunning(v=>!v)}>
          {running?<Pause size={15}/>:<Play size={15}/>}
          {running?"PAUSE LIVE FLOW":"RUN LIVE FLOW"}
        </button>
      </section>

      <section className="system-world">
        <div className="world-head">
          <div>
            <span className={"live "+(running?"on":"")}/>
            {running?"LIVE DISTRICT FLOW":"SIMULATION PAUSED"}
          </div>

          <span>24-HOUR SIMEVENTS MODEL</span>
        </div>

        <div className="world">
          <div className="floor"/>

          <svg viewBox="0 0 1000 520" preserveAspectRatio="none">
            <path className="flow" d="M70 250 L180 250 L310 250 L440 250 L580 250 L720 250 L850 250 L950 250"/>
            <path className="feedback" d="M450 290 C430 405 280 405 305 290"/>
            <path className="branch" d="M855 270 C860 345 910 360 950 325"/>
          </svg>

          {running && <>
            <i className="token t1"/>
            <i className="token t2"/>
            <i className="token t3"/>
            <i className="token t4"/>
          </>}

          {PIPELINE.map(([id,title,sub,x,y,Icon],i)=>
            <article
              key={id}
              className={"pipeline-node "+(id==="ai"?"clickable":"")}
              style={{left:`${x}%`,top:`${y}%`}}
              onClick={()=>id==="ai"&&setShowAI(v=>!v)}
            >
              <header>
                <span>{String(i+1).padStart(2,"0")}</span>
                <Icon size={17}/>
              </header>

              <strong>{title}</strong>
              <small>{sub}</small>

              <footer>
                <i className={running?"pulse":""}/>
                {id==="ai" ? "CLICK TO EXPAND" : "ACTIVE"}
              </footer>
            </article>
          )}

          <div className="recapture-loop">
            <RefreshCw size={15}/>
            <div>
              <b>RECAPTURE FEEDBACK</b>
              <span>Quality failure → preparation → camera queue</span>
            </div>
          </div>

          <div className="trace-branches">
            <span>TRACE ROUTING CONTRACT</span>
            <div><b>80.11%</b>ROUTINE</div>
            <div><b>9.95%</b>REFER</div>
            <div><b>9.94%</b>HUMAN REVIEW</div>
          </div>
        </div>
      </section>

      {showAI && (
        <section className="ai-stack" id="architecture">
          <div className="section-title">
            <span>03 · INSIDE NETRAAI V3</span>
            <h2>One screening decision. Multiple evidence networks.</h2>
            <p>
              The deployment model treats AI as one service resource;
              the clinical engine internally combines grading, pathology,
              anatomy, advanced evidence and trust analysis.
            </p>
          </div>

          <div className="ai-flow">

            <AINode
              icon={ShieldCheck}
              tag="SAFETY"
              title="QUALITY ENGINE"
              body="Focus · illumination · contrast · retinal FOV"
            />

            <Arrow/>

            <AINode
              icon={BrainCircuit}
              tag="GLOBAL"
              title="DR GRADING NETWORK"
              body="ICDR 0 · 1 · 2 · 3 · 4 + referable DR"
            />

            <Arrow/>

            <div className="parallel-networks">
              <AINode
                icon={Microscope}
                tag="LOCAL"
                title="LESION NETWORK"
                body="MA · HE · EX · SE"
              />

              <AINode
                icon={Eye}
                tag="STRUCTURE"
                title="ANATOMY"
                body="Optic disc · fovea · vessels"
              />

              <AINode
                icon={Activity}
                tag="ADVANCED"
                title="SAFETY EVIDENCE"
                body="VB/IRMA · NV · VH"
              />
            </div>

            <Arrow/>

            <AINode
              icon={Database}
              tag="CALIBRATION"
              title="RDR CALIBRATION"
              body="Calibrated referable-DR probability + locked threshold"
            />

            <Arrow/>

            <div className="parallel-networks trust">
              <AINode
                icon={Activity}
                tag="XAI"
                title="GRAD-CAM"
                body="Retinal attribution + lesion grounding"
              />

              <AINode
                icon={Gauge}
                tag="EVIDENCE"
                title="P-SCORE"
                body="Pathology evidence aggregation"
              />

              <AINode
                icon={GitBranch}
                tag="AGREEMENT"
                title="CONCORDANCE"
                body="Cross-evidence agreement and conflict"
              />

              <AINode
                icon={ShieldCheck}
                tag="ROBUSTNESS"
                title="STABILITY"
                body="Benign-transform consistency"
              />
            </div>

            <Arrow/>

            <AINode
              icon={ShieldCheck}
              tag="TRUST"
              title="T-SCORE → TRACE-DR"
              body="Trust synthesis · escalation · human routing"
            />
          </div>
        </section>
      )}

      <section className="resource-panel">
        <div className="section-title">
          <span>04 · CURRENT RESOURCE STATE</span>
          <h2>Where does the system saturate?</h2>
        </div>

        <div className="resource-grid">
          <Resource label="CAMERA" value={M.camera}/>
          <Resource label="NETWORK" value={M.network}/>
          <Resource label="AI" value={M.ai}/>
          <Resource label="OPHTHALMOLOGY" value={M.ophth}/>
          <Resource label="HUMAN REVIEW" value={M.human}/>
          <Resource label="RECAPTURE PREP" value={M.recapPrep}/>
        </div>

        <div className="derived-grid">
          <div>
            <span>NETWORK SERVICE</span>
            <strong>{M.networkService.toFixed(2)} s</strong>
            <small>(5 MB × 8 / bandwidth) + 50 ms</small>
          </div>

          <div>
            <span>EXPECTED CAPTURE ATTEMPTS</span>
            <strong>{M.attempts.toFixed(3)}</strong>
            <small>1 / (1 − recapture probability)</small>
          </div>

          <div>
            <span>LIVE VISUALIZED CASES</span>
            <strong>{cases.toLocaleString()}</strong>
            <small>demonstration counter, not SimEvents output</small>
          </div>

          <div>
            <span>CAPACITY VERDICT</span>
            <strong className={M.stable?"green":"red"}>
              {M.stable?"STABLE":"UNSTABLE"}
            </strong>
            <small>all six resource utilizations must remain &lt;100%</small>
          </div>
        </div>
      </section>

      <section className="baseline">
        <div>
          <span>05 · BASELINE CONFIGURATION</span>
          <h2>2 cameras · 10 Mbps · 5% recapture</h2>
        </div>

        <div className="baseline-numbers">
          <div><strong>73.1%</strong><span>camera utilization</span></div>
          <div><strong>4.69%</strong><span>network utilization</span></div>
          <div><strong>3.92%</strong><span>AI utilization</span></div>
          <div><strong>STABLE</strong><span>resource verdict</span></div>
        </div>
      </section>

      <footer className="dt-footer">
        Web visualization mirrors the NetraAI R2026a deployment model.
        Resource calculations follow the current SimEvents resource-sizing
        assumptions; the browser animation itself is not a MATLAB simulation.
      </footer>
    </main>
  );
}

function Metric({type,value,label}){
  return <article className="metric">
    <span>{type}</span>
    <strong>{value}</strong>
    <small>{label}</small>
  </article>
}

function AINode({icon:Icon,tag,title,body}){
  return <article className="ai-node">
    <header><span>{tag}</span><Icon size={17}/></header>
    <strong>{title}</strong>
    <small>{body}</small>
  </article>
}

function Arrow(){
  return <div className="ai-arrow">↓</div>
}

function Resource({label,value}){
  const v=clamp(value,0,100);
  return <article className="resource">
    <div><span>{label}</span><strong>{value.toFixed(1)}%</strong></div>
    <div className="bar"><i style={{width:`${v}%`}}/></div>
    <small>{value>=100?"SATURATED":value>=85?"NEAR CAPACITY":"HEADROOM AVAILABLE"}</small>
  </article>
}
