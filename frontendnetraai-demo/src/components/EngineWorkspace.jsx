import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Upload, ScanEye, Image as ImageIcon, Activity, BrainCircuit,
  Layers3, ShieldCheck, FileText, ChevronRight, MousePointer2,
  Grid3X3, Flame, Crosshair, CheckCircle2, AlertTriangle
} from "lucide-react";

const API = "http://127.0.0.1:8000";
const STAGES = [
  { id:"input", label:"Acquire", icon:Upload, hint:"Upload or demo" },
  { id:"quality", label:"Quality", icon:Activity, hint:"Capture reliability" },
  { id:"global", label:"Global", icon:BrainCircuit, hint:"ICDR + RDR" },
  { id:"local", label:"Local", icon:Layers3, hint:"Tiles + lesions" },
  { id:"xai", label:"Explain", icon:Flame, hint:"Grad-CAM" },
  { id:"trust", label:"TRACE-DR", icon:ShieldCheck, hint:"P/T + concordance" },
  { id:"report", label:"Decision", icon:FileText, hint:"Routing + report" },
];

const REGIONS = [
  {id:"ul", label:"Upper-left field", x:0, y:0, w:50, h:50},
  {id:"ur", label:"Upper-right field", x:50, y:0, w:50, h:50},
  {id:"ll", label:"Lower-left field", x:0, y:50, w:50, h:50},
  {id:"lr", label:"Lower-right field", x:50, y:50, w:50, h:50},
  {id:"central", label:"Central retinal zone", x:30, y:28, w:40, h:44},
];

const GRADE_NAMES = ["No DR","Mild NPDR","Moderate NPDR","Severe NPDR","PDR"];
const LESION_LABELS = { MA:"Microaneurysms", HE:"Hemorrhages", EX:"Hard exudates", SE:"Soft exudates" };

const pct = (n, d=1) => `${(Number(n||0)*100).toFixed(d)}%`;
const clamp = (n,min,max) => Math.min(Math.max(n,min),max);

function Bar({label, value, max=100, suffix="", decimals=1}) {
  const n = Number(value||0);
  return <div className="nw-bar-row">
    <span>{label}</span>
    <div className="nw-bar-track"><i style={{width:`${clamp((n/max)*100,0,100)}%`}}/></div>
    <strong>{n.toFixed(decimals)}{suffix}</strong>
  </div>
}

function Score({label, value, sub}) {
  const n=Number(value||0);
  return <div className="nw-score">
    <div className="nw-score-ring" style={{"--score":`${clamp(n,0,100)*3.6}deg`}}><b>{n.toFixed(1)}</b><small>/100</small></div>
    <div><span>{label}</span>{sub && <p>{sub}</p>}</div>
  </div>
}

function getComponents(result) {
  const out=[];
  if (!result) return out;
  for (const key of ["MA","HE","EX","SE"]) {
    const arr = result?.lesions?.[key]?.components || result?.lesion_components?.[key] || [];
    for (const c of arr) out.push({...c, lesion:key});
  }
  return out;
}

function componentPoint(c, result) {
  const W = Number(result?.image_width || result?.image?.width || result?.source?.width || 1);
  const H = Number(result?.image_height || result?.image?.height || result?.source?.height || 1);
  let x = c.x ?? c.cx ?? c.centroid_x ?? c.centroid?.[0];
  let y = c.y ?? c.cy ?? c.centroid_y ?? c.centroid?.[1];
  if (x == null || y == null) return null;
  x=Number(x); y=Number(y);
  if (x>1 || y>1) { x=x/W; y=y/H; }
  return {x:clamp(x,0,1), y:clamp(y,0,1)};
}

function regionStats(result, region) {
  const comps=getComponents(result);
  const stats={MA:0,HE:0,EX:0,SE:0,total:0,area:0,confidence:[]};
  for (const c of comps) {
    const p=componentPoint(c,result); if(!p) continue;
    const xp=p.x*100, yp=p.y*100;
    if (xp>=region.x && xp<=region.x+region.w && yp>=region.y && yp<=region.y+region.h) {
      stats[c.lesion]++; stats.total++;
      stats.area += Number(c.area_px||c.area||0);
      const cf=Number(c.mean_confidence ?? c.confidence ?? c.score);
      if(Number.isFinite(cf)) stats.confidence.push(cf);
    }
  }
  stats.meanConfidence = stats.confidence.length ? stats.confidence.reduce((a,b)=>a+b,0)/stats.confidence.length : null;
  return stats;
}

export default function EngineWorkspace(){
  const [searchParams] = useSearchParams();
  const [stage,setStage]=useState("input");
  const [file,setFile]=useState(null);
  const [preview,setPreview]=useState("");
  const [result,setResult]=useState(null);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState("");
  const [layer,setLayer]=useState("original");
  const [hoverRegion,setHoverRegion]=useState(null);
  const [lockedRegion,setLockedRegion]=useState(null);
  const inputRef=useRef();

  const activeRegion=lockedRegion || hoverRegion;
  const activeRegionStats=useMemo(()=>activeRegion?regionStats(result,activeRegion):null,[activeRegion,result]);
  const hasLocalizedComponents=getComponents(result).length>0;

  useEffect(()=>{
    const demo=searchParams.get("demo");
    if (demo) loadDemo(`/demo/${demo}.png`,`${demo}.png`);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  },[]);

  async function loadDemo(path,name){
    try{
      setError(""); setResult(null);
      const r=await fetch(path); const blob=await r.blob();
      const f=new File([blob],name,{type:blob.type||"image/png"});
      setFile(f); setPreview(URL.createObjectURL(f)); setStage("input");
    }catch{ setError("Could not load the demo scan."); }
  }

  function chooseFile(e){
    const f=e.target.files?.[0]; if(!f) return;
    setFile(f); setPreview(URL.createObjectURL(f)); setResult(null); setError("");
  }

  async function analyze(){
    if(!file){setError("Choose a fundus image first.");return;}
    try{
      setLoading(true); setError("");
      const fd=new FormData(); fd.append("file",file);
      const r=await fetch(`${API}/api/analyze`,{method:"POST",body:fd});
      const data=await r.json(); if(!r.ok) throw new Error(data?.detail||"Analysis failed");
      setResult(data); setStage(data?.quality?.status==="UNGRADEABLE"?"quality":"quality");
    }catch(e){setError(e.message||"Could not reach the NetraAI backend.");}
    finally{setLoading(false);}
  }

  const artifact=(p)=>p?`${API}${p}`:"";
  const displayImage = layer==="lesions" ? artifact(result?.artifacts?.lesion_overlay) : layer==="gradcam" ? artifact(result?.artifacts?.gradcam) : preview;

  return <div className="nw-workspace">
    <aside className="nw-rail">
      <div className="nw-case-mini"><span>CASE</span><strong>{result?.case_id || "NEW SCREEN"}</strong><small>{result ? "Analysis available" : "Awaiting image"}</small></div>
      <nav>{STAGES.map(({id,label,icon:Icon,hint},i)=>{
        const enabled=id==="input" || !!result;
        return <button key={id} disabled={!enabled} className={stage===id?"active":""} onClick={()=>enabled&&setStage(id)}>
          <span className="nw-step-num">0{i+1}</span><Icon size={17}/><div><strong>{label}</strong><small>{hint}</small></div><ChevronRight size={14}/>
        </button>
      })}</nav>
      <div className="nw-rail-note"><ShieldCheck size={16}/><p><b>Safety:</b> ungradeable images are routed to recapture, never silently classified as normal.</p></div>
    </aside>

    <section className="nw-stage">
      <div className="nw-stage-head">
        <div><span>NETRAAI / {STAGES.find(s=>s.id===stage)?.label.toUpperCase()}</span><h1>{STAGES.find(s=>s.id===stage)?.hint}</h1></div>
        {result && <div className="nw-stage-status"><i/>{result.recommendation?.action?.replaceAll("_"," ") || "ANALYZED"}</div>}
      </div>

      {stage==="input" && <div className="nw-input-grid">
        <div className="nw-upload-panel">
          <div className="nw-upload-visual">{preview ? <img src={preview} alt="Selected fundus"/> : <ScanEye size={70}/>}</div>
          <div className="nw-upload-actions">
            <input ref={inputRef} type="file" accept="image/*" hidden onChange={chooseFile}/>
            <button className="nw-primary" onClick={()=>inputRef.current?.click()}><Upload size={17}/> Choose fundus image</button>
            <button className="nw-run" disabled={!file||loading} onClick={analyze}>{loading?"Running quality, global and local models…":"Run NetraAI analysis"}</button>
          </div>
          {error && <div className="nw-error">{error}</div>}
        </div>
        <div className="nw-demo-panel"><span>DEMO CASES</span><h2>Start with a real APTOS scan.</h2>
          {[['grade0','Grade 0','No apparent DR'],['grade1','Grade 1','Mild NPDR'],['grade2','Grade 2','Moderate NPDR']].map(([id,g,n])=><button key={id} onClick={()=>loadDemo(`/demo/${id}.png`,`${id}.png`)}><img src={`/demo/${id}.png`} alt=""/><div><strong>{g}</strong><span>{n}</span></div><ChevronRight size={15}/></button>)}
        </div>
      </div>}

      {stage==="quality" && result && <div className="nw-two-col">
        <div className="nw-hero-card"><span>CAPTURE RELIABILITY</span><div className="nw-big-status">{result.quality?.status}</div><p>NetraAI checks whether the image is reliable enough before allowing downstream DR classification.</p><div className="nw-bars"><Bar label="Focus" value={result.quality.focus*100}/><Bar label="Illumination" value={result.quality.illumination*100}/><Bar label="Contrast" value={result.quality.contrast*100}/><Bar label="Retinal FOV" value={result.quality.fov*100}/></div></div>
        <div className="nw-image-card"><img src={preview} alt="Fundus"/><div><span>QUALITY SCORE</span><strong>{(result.quality.score*100).toFixed(1)}%</strong><small>{result.quality.enhancement_applied?"Enhancement applied":"Original retained"}</small></div></div>
      </div>}

      {stage==="global" && result && <div className="nw-global-grid">
        <div className="nw-classification-card"><span>GLOBAL RETINAL CLASSIFIER</span><div className="nw-grade"><small>ICDR</small><b>G{result.prediction.icdr_grade}</b><div><h2>{result.prediction.grade_name}</h2><p>Global severity from the full retinal field.</p></div></div>
          <div className="nw-severity-rail">{GRADE_NAMES.map((g,i)=><div className={i===result.prediction.icdr_grade?"active":""} key={g}><i/><b>G{i}</b><span>{g}</span></div>)}</div>
        </div>
        <div className="nw-chart-card"><span>GRADE PROBABILITY</span><div className="nw-bars">{result.prediction.grade_probabilities.map((v,i)=><Bar key={i} label={`G${i} ${GRADE_NAMES[i]}`} value={v*100}/>)}</div><div className="nw-rdr"><div><span>REFERABLE DR</span><strong>{result.prediction.referable_dr?"POSITIVE":"NEGATIVE"}</strong></div><b>{pct(result.prediction.rdr_probability,2)}</b></div></div>
      </div>}

      {stage==="local" && result && <div className="nw-local-layout">
        <div className="nw-retina-workbench">
          <div className="nw-view-toolbar"><div>{[["original",ImageIcon,"Original"],["lesions",Layers3,"Lesions"],["gradcam",Flame,"Grad-CAM"]].map(([id,Icon,l])=><button key={id} className={layer===id?"active":""} onClick={()=>setLayer(id)}><Icon size={14}/>{l}</button>)}</div><span><Grid3X3 size={14}/> 512 × 512 overlapping tile logic</span></div>
          <div className="nw-retina-stage">
            {displayImage && <img src={displayImage} alt="Retinal analysis layer"/>}
            <div className="nw-slice-grid" aria-hidden="true">{Array.from({length:24}).map((_,i)=><i key={i}/>)}</div>
            {REGIONS.map(r=><button key={r.id} className={`nw-region ${activeRegion?.id===r.id?"active":""}`} style={{left:`${r.x}%`,top:`${r.y}%`,width:`${r.w}%`,height:`${r.h}%`}} onMouseEnter={()=>setHoverRegion(r)} onMouseLeave={()=>setHoverRegion(null)} onClick={()=>setLockedRegion(lockedRegion?.id===r.id?null:r)} aria-label={r.label}/>)}
            <div className="nw-crosshair"><Crosshair size={20}/></div>
          </div>
          <div className="nw-view-caption"><MousePointer2 size={14}/> Hover a retinal region for evidence inspection. Click to lock the region.</div>
        </div>
        <aside className="nw-inspector">
          <span>REGION INSPECTOR</span>
          {!activeRegion ? <><h2>Hover the retina</h2><p>Move the cursor across the retinal field to inspect local pathology evidence without leaving the analysis viewport.</p></> : <>
            <h2>{activeRegion.label}</h2>
            {hasLocalizedComponents ? <><div className="nw-region-total"><span>Localized components</span><b>{activeRegionStats.total}</b></div>{["MA","HE","EX","SE"].map(k=><div className="nw-region-lesion" key={k}><div><strong>{k}</strong><span>{LESION_LABELS[k]}</span></div><b>{activeRegionStats[k]}</b></div>)}<div className="nw-region-meta"><span>Component area</span><b>{activeRegionStats.area.toLocaleString()} px</b><span>Mean component confidence</span><b>{activeRegionStats.meanConfidence==null?"—":pct(activeRegionStats.meanConfidence,1)}</b></div></> : <div className="nw-localization-note"><AlertTriangle size={16}/><p>Regional geometry is interactive, but this backend result does not yet include lesion centroids. Overall lesion evidence is shown below rather than inventing regional counts.</p></div>}
          </>}
          <div className="nw-overall-lesions"><span>WHOLE-RETINA EVIDENCE</span>{Object.entries(result.lesions||{}).map(([k,v])=><div key={k}><strong>{k}</strong><i style={{width:`${Math.min((v.count||0),100)}%`}}/><b>{v.count}</b><small>{pct(v.mean_confidence,1)}</small></div>)}</div>
        </aside>
      </div>}

      {stage==="xai" && result && <div className="nw-two-col">
        <div className="nw-xai-image"><img src={artifact(result.artifacts?.gradcam)} alt="Grad-CAM"/><span>GLOBAL ATTRIBUTION MAP</span></div>
        <div className="nw-hero-card"><span>EXPLANATION INTEGRITY</span><Score label="XAI Integrity" value={result.xai_integrity.score} sub="Agreement between attribution location and retinal evidence."/><div className="nw-bars"><Bar label="Attribution in retinal FOV" value={result.xai_integrity.attribution_in_retinal_fov}/><Bar label="Attribution overlapping lesion evidence" value={result.xai_integrity.attribution_lesion_overlap}/></div><p>Grad-CAM is treated as an attribution aid, not as proof of pathology. Weak lesion overlap lowers explanation reliability instead of being hidden.</p></div>
      </div>}

      {stage==="trust" && result && <div className="nw-trust-grid">
        <div className="nw-score-card"><Score label="P-Score" value={result.p_score} sub="Prototype pathology evidence index."/><div className="nw-bars"><Bar label="MA contribution" value={(result.lesions.MA?.mean_confidence||0)*30} max={30}/><Bar label="HE contribution" value={(result.lesions.HE?.mean_confidence||0)*30} max={30}/><Bar label="EX contribution" value={(result.lesions.EX?.mean_confidence||0)*25} max={25}/><Bar label="SE contribution" value={(result.lesions.SE?.mean_confidence||0)*15} max={15}/></div></div>
        <div className="nw-score-card"><Score label="T-Score" value={result.t_score.score} sub={`${result.t_score.level} trustworthiness`}/><div className="nw-bars"><Bar label="Image reliability" value={result.quality.score*100}/><Bar label="Model confidence" value={result.prediction.grade_confidence*100}/><Bar label="Evidence concordance" value={result.concordance.score}/><Bar label="XAI integrity" value={result.xai_integrity.score}/><Bar label="Stability" value={90}/></div></div>
        <div className="nw-evidence-card"><span>PATHOLOGY CONCORDANCE</span><strong>{result.concordance.score}</strong><b>{result.concordance.status}</b><ul>{result.concordance.supporting_evidence?.map(x=><li key={x}><CheckCircle2 size={14}/>{x}</li>)}</ul>{result.concordance.conflicting_evidence?.length>0&&<div className="nw-conflicts">{result.concordance.conflicting_evidence.map(x=><p key={x}>{x}</p>)}</div>}</div>
      </div>}

      {stage==="report" && result && <div className="nw-decision-grid">
        <div className="nw-decision-card"><span>FINAL SCREENING ROUTE</span><h2>{result.recommendation.action.replaceAll("_"," ")}</h2><p>{result.recommendation.reason}</p><div className="nw-summary-ledger"><div><span>ICDR severity</span><b>Grade {result.prediction.icdr_grade} · {result.prediction.grade_name}</b></div><div><span>Referable DR</span><b>{result.prediction.referable_dr?"Positive":"Negative"}</b></div><div><span>Image quality</span><b>{result.quality.status}</b></div><div><span>P-Score</span><b>{result.p_score}</b></div><div><span>Concordance</span><b>{result.concordance.score} · {result.concordance.status}</b></div><div><span>T-Score</span><b>{result.t_score.score} · {result.t_score.level}</b></div></div></div>
        <div className="nw-report-card"><FileText size={36}/><span>EXPLAINABLE REPORT</span><h3>NetraAI detailed analysis</h3><p>Classification, lesion evidence, explainability, P/T scores and decision rationale.</p>{result.artifacts?.report?<a href={artifact(result.artifacts.report)} target="_blank" rel="noreferrer">Open detailed PDF report</a>:<small>Report artifact not available in this response.</small>}</div>
      </div>}
    </section>
  </div>
}
