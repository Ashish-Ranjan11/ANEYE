import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Camera, ShieldCheck, Wifi, BrainCircuit, Stethoscope, GitBranch, Activity } from "lucide-react";
import "./DigitalTwinPage.css";

const stages=[
 ["01","PRIMARY SCREENING","Arrival generator",Activity,"RGB FUNDUS"],
 ["02","CAMERA QUEUE","Acquisition waiting",GitBranch,"IMAGE QUEUE"],
 ["03","CAMERA POOL","Portable fundus capture",Camera,"5 MB FRAME"],
 ["04","QUALITY GATE","Focus · illumination · FOV",ShieldCheck,"QUALITY VECTOR"],
 ["05","NETWORK","Store & forward",Wifi,"10 Mbps PAYLOAD"],
 ["06","NETRAAI V3","Explainable AI core",BrainCircuit,"EVIDENCE SIGNALS"],
 ["07","TRACE ROUTER","Safety routing",GitBranch,"ROUTING SIGNAL"],
 ["08","SPECIALIST","Remote verification",Stethoscope,"CLINICAL REVIEW"],
];

const modules=[
 ["QUALITY / PREPROCESS","Focus · illumination · contrast · FOV"],
 ["GLOBAL DR GRADING","ICDR 0–4 · referable DR"],
 ["LESION EVIDENCE","MA · HE · EX · SE"],
 ["ANATOMY","Disc · fovea · vessels"],
 ["ADVANCED SAFETY","VB/IRMA · NV · VH"],
 ["CALIBRATION","RDR probability + threshold"],
 ["XAI GROUNDING","Grad-CAM + lesion evidence"],
 ["TRUST FUSION","P-score · concordance · stability · T-score"],
];

export default function DigitalTwinPage(){
 const [openAI,setOpenAI]=useState(true);
 return <main className="rdt">
  <header className="rdt-top">
   <Link to="/"><ArrowLeft size={15}/> Home</Link>
   <div><b>NETRAAI</b><span>RURAL DIGITAL TWIN</span></div>
   <Link to="/engine">Clinical Workstation →</Link>
  </header>

  <section className="rdt-hero">
   <span className="rdt-kicker">DISTRICT-SCALE SCREENING & RESOURCE SIMULATION</span>
   <h1>Rural Digital Twin</h1>
   <p>Visualizing how retinal images, quality signals, AI evidence and referral decisions flow through a rural screening network.</p>
   <div className="rdt-baseline"><b>100,000+</b><span>screenings / year capacity target</span><i/> <b>147</b><span>resource scenarios</span><i/><b>24 h</b><span>simulation horizon / scenario</span></div>
  </section>

  <section className="rdt-world">
   <div className="rdt-grid"/>
   <div className="rdt-flow">
    {stages.map(([n,title,sub,Icon,signal],i)=><div className="rdt-stage-wrap" key={title}>
      <button className={"rdt-node "+(title==="NETRAAI V3"?"ai":"")} onClick={()=>title==="NETRAAI V3"&&setOpenAI(v=>!v)}>
       <small>{n}</small><Icon size={27}/><strong>{title}</strong><span>{sub}</span><em>● ACTIVE</em>
      </button>
      {i<stages.length-1&&<div className="rdt-wire"><span>{signal}</span><i/><i/><i/></div>}
    </div>)}
   </div>
   <div className="rdt-recapture"><b>↶ RECAPTURE SIGNAL</b><span>quality failure → reacquire → camera queue</span></div>
   <div className="rdt-route"><span>TRACE ROUTING CONTRACT</span><div><b>80.11%<small>ROUTINE</small></b><b>9.95%<small>REFER</small></b><b>9.94%<small>HUMAN REVIEW</small></b></div></div>
  </section>

  {openAI&&<section className="rdt-ai">
   <div className="rdt-section-head"><span>INSIDE NETRAAI V3</span><h2>Signals split into independent evidence modules, then merge into trust-aware routing.</h2></div>
   <div className="rdt-module-flow">
    {modules.map(([a,b],i)=><div className="rdt-module-wrap" key={a}><article><strong>{a}</strong><span>{b}</span></article>{i<modules.length-1&&<div className="rdt-signal"><i/><i/><i/></div>}</div>)}
   </div>
   <p className="rdt-note">These are functional AI/evidence modules, not a claim that every box is a literal neural-network layer.</p>
  </section>}

  <section className="rdt-resources">
   <div><span>CAMERA CONFIGURATION</span><b>2 stations</b><small>120 s modeled capture service</small></div>
   <div><span>RURAL LINK</span><b>10 Mbps</b><small>5 MB image payload</small></div>
   <div><span>RECAPTURE</span><b>5%</b><small>baseline engineering assumption</small></div>
   <div><span>AI SERVICE</span><b>3.384 s</b><small>simulation service input</small></div>
   <div><span>OPHTHALMOLOGY</span><b>30 s</b><small>capacity-model assumption</small></div>
   <div><span>HUMAN REVIEW</span><b>45 s</b><small>capacity-model assumption</small></div>
  </section>
 </main>
}