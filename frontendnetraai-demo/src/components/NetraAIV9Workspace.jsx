import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, AlertTriangle, ArrowLeft, BrainCircuit, CheckCircle2, Eye, FileText, Focus, Layers3, Network, ScanEye, ShieldCheck, Sparkles, Target, Upload } from "lucide-react";
import "../v9-workstation.css";

const API = "http://127.0.0.1:8000";
const STEPS = [["Acquire",Upload],["Quality gate",Focus],["Enhance",Sparkles],["ICDR + RDR",BrainCircuit],["Lesions",Layers3],["Anatomy",Eye],["Explain",Activity],["Trust",ShieldCheck],["TRACE route",Target],["Report",FileText]];
const CLASSIC={MA:"Microaneurysms",HE:"Hemorrhages",EX:"Hard exudates",SE:"Soft exudates"};
const ADVANCED={VB_IRMA:"Venous beading / IRMA",NV:"Neovascularization",VH:"Vitreous hemorrhage"};
const pct=(v,d=1)=>((Number(v||0)*100).toFixed(d)+"%");
const artifact=p=>p?(API+p):"";

function Meter({label,value}){const n=Math.max(0,Math.min(100,Number(value||0)));return <div className="v9-meter"><div><span>{label}</span><b>{n.toFixed(1)}%</b></div><i><em style={{width:n+"%"}}/></i></div>}
function StatePill({state}){const s=String(state||"NOT AVAILABLE");return <span className={"v9-pill "+(s.includes("CONFIRM")?"ok":s.includes("ALERT")?"warn":"neutral")}>{s.replaceAll("_"," ")}</span>}
function advancedEvidence(result,key){const e=result?.advanced_evidence?.evidence?.[key]||result?.advanced_evidence?.[key]||result?.advanced?.[key];if(!e)return null;const raw=Number(e.raw_score??e.raw??e.score??0);const alert=Number(e.alert_threshold??e.alert??0);const confirm=Number(e.confirm_threshold??e.confirm??0);const state=e.state||(e.confirmed?"CONFIRMED":e.alerted||e.alert?"ALERT_ONLY":"BELOW_ALERT");return {raw,alert,confirm,state}}

export default function NetraAIV9Workspace(){
 const inputRef=useRef(); const [file,setFile]=useState(null); const [preview,setPreview]=useState(""); const [result,setResult]=useState(null); const [loading,setLoading]=useState(false); const [error,setError]=useState(""); const [view,setView]=useState("original");
 function choose(e){const f=e.target.files?.[0];if(!f)return;setFile(f);setPreview(URL.createObjectURL(f));setResult(null);setError("")}
 async function analyze(){if(!file){setError("Choose a fundus image first.");return}setLoading(true);setError("");try{const fd=new FormData();fd.append("file",file);const r=await fetch(API+"/api/analyze",{method:"POST",body:fd});const data=await r.json();if(!r.ok)throw new Error(data?.detail||"Analysis failed");setResult(data)}catch(e){setError(e.message||"Could not reach NetraAI backend.")}finally{setLoading(false)}}
 const q=result?.quality,pred=result?.prediction,rec=result?.recommendation; const blocked=q?.status==="UNGRADEABLE"||rec?.action==="RECAPTURE";
 const image=view==="lesions"?artifact(result?.artifacts?.lesion_overlay):view==="gradcam"?artifact(result?.artifacts?.gradcam):view==="structure"?artifact(result?.artifacts?.structural_overlay):view==="vessels"?artifact(result?.artifacts?.vessel_mask):preview;
 return <div className="v9-shell">
  <header className="v9-top"><Link to="/"><ArrowLeft size={17}/> Home</Link><div><b>NETRAAI V9</b><span>Quality-first explainable DR screening</span></div><span className="v9-live"><i/> MATLAB + AI + TRACE-DR workflow</span></header>
  <section className="v9-flow">{STEPS.map(([name,Icon],i)=><div key={name} className={blocked&&i>2?"blocked":""}><small>{String(i+1).padStart(2,"0")}</small><Icon size={17}/><b>{name}</b>{i<STEPS.length-1&&<span>→</span>}</div>)}</section>
  <main className="v9-main"><section className="v9-left">
   <div className="v9-card v9-upload"><div className="v9-title"><span>01 · ACQUISITION</span><h1>Clinical screening workspace</h1><p>Upload a fundus image. NetraAI checks capture reliability before any DR grading.</p></div>
    <div className="v9-image">{image?<img src={image} alt="Fundus analysis"/>:<ScanEye size={72}/>}</div>
    <div className="v9-tabs">{["original","lesions","gradcam","structure","vessels"].map(x=><button disabled={!result&&x!=="original"} className={view===x?"active":""} onClick={()=>setView(x)} key={x}>{x}</button>)}</div>
    <input ref={inputRef} hidden type="file" accept="image/*" onChange={choose}/><div className="v9-actions"><button onClick={()=>inputRef.current?.click()}><Upload size={16}/> Choose image</button><button className="primary" disabled={!file||loading} onClick={analyze}>{loading?"Running NetraAI pipeline…":"Run full screening"}</button></div>{error&&<div className="v9-error">{error}</div>}
   </div>
   {result&&<div className="v9-card"><div className="v9-section-head"><div><span>02 · IMAGE QUALITY GATE</span><h2>{q?.status||"UNKNOWN"}</h2></div><StatePill state={blocked?"RECAPTURE":q?.enhancement_applied?"ENHANCED_GRADEABLE":"PASSED"}/></div>
    <div className="v9-meters"><Meter label="Focus" value={Number(q?.focus)*100}/><Meter label="Illumination" value={Number(q?.illumination)*100}/><Meter label="Contrast" value={Number(q?.contrast)*100}/><Meter label="Retinal FOV" value={Number(q?.fov)*100}/></div>
    <div className="v9-quality-note"><Sparkles size={18}/><div><b>Adaptive enhancement</b><p>{q?.enhancement_applied?"CLAHE enhancement was accepted because the measured quality score improved.":"Original image retained. Borderline images are CLAHE-enhanced only when the measured quality score improves."}</p></div></div>
    {q?.reasons?.length>0&&<div className="v9-warning"><AlertTriangle size={17}/>{q.reasons.join(" · ")}</div>}{blocked&&<div className="v9-stop"><ShieldCheck size={19}/><b>Safety gate stopped classification.</b><span>Recapture is required; this image is not silently classified as normal.</span></div>}
   </div>}
   {result&&!blocked&&pred&&<div className="v9-card"><div className="v9-section-head"><div><span>03 · CLINICAL AI</span><h2>ICDR Grade {pred.icdr_grade} · {pred.grade_name}</h2></div><StatePill state={pred.referable_dr?"REFERABLE DR":"NON-REFERABLE"}/></div>
    <div className="v9-clinical"><div><small>RDR probability</small><strong>{pct(pred.calibrated_rdr_probability??pred.rdr_probability,2)}</strong></div><div><small>Grade confidence</small><strong>{pct(pred.calibrated_grade_confidence??pred.grade_confidence,2)}</strong></div><div><small>Decision threshold</small><strong>{pred.rdr_threshold!=null?Number(pred.rdr_threshold).toFixed(3):"—"}</strong></div></div>
    <div className="v9-probs">{(pred.grade_probabilities||[]).map((v,i)=><Meter key={i} label={"G"+i} value={Number(v)*100}/>)}</div>
   </div>}
   {result&&!blocked&&<div className="v9-card"><div className="v9-section-head"><div><span>04 · RETINAL EVIDENCE</span><h2>Lesions + advanced vascular evidence</h2></div></div>
    <div className="v9-evidence-grid">{Object.entries(CLASSIC).map(([k,name])=>{const x=result?.lesions?.[k];return <div key={k}><b>{k}</b><span>{name}</span><strong>{x?.count??0}</strong><small>mean confidence {x?pct(x.mean_confidence):"—"}</small></div>})}</div>
    <div className="v9-advanced">{Object.entries(ADVANCED).map(([k,name])=>{const e=advancedEvidence(result,k);return <div key={k}><div><b>{k}</b><span>{name}</span></div>{e?<><StatePill state={e.state}/><small>score {e.raw.toFixed(3)} · alert {e.alert.toFixed(3)} · confirm {e.confirm.toFixed(3)}</small></>:<><StatePill state="NOT RETURNED"/><small>Waiting for V3 advanced-evidence contract; no value is fabricated.</small></>}</div>})}</div>
    <p className="v9-disclaimer">Advanced evidence is a safety-routing signal. ALERT/CONFIRMED states are not autonomous diagnoses; VB/IRMA evidence is not treated as quadrant-aware 4-2-1 grading unless the backend explicitly provides that validation.</p>
   </div>}
  </section>
  <aside className="v9-right"><div className="v9-card"><span className="eyebrow">TRACE-DR REVIEW</span>
   {!result?<div className="v9-empty"><Network size={34}/><b>Awaiting analysis</b><p>Quality, evidence, XAI and routing will appear here.</p></div>:blocked?<div className="v9-route recapture"><AlertTriangle/><b>RECAPTURE</b><p>{rec?.reason||"Image failed quality gate."}</p></div>:<>
    <div className="v9-route"><Target/><b>{String(rec?.action||"REVIEW").replaceAll("_"," ")}</b><p>{rec?.reason}</p></div>
    <div className="v9-scores"><div><span>P-score</span><b>{typeof result.p_score==="object"?result.p_score.score:result.p_score??"—"}</b><small>pathology evidence index</small></div><div><span>T-score</span><b>{result?.t_score?.score??"—"}</b><small>{result?.t_score?.level||"trust index"}</small></div><div><span>Concordance</span><b>{result?.concordance?.score??"—"}</b><small>{result?.concordance?.status||"evidence agreement"}</small></div><div><span>XAI integrity</span><b>{result?.xai_integrity?.score??"—"}</b><small>attribution integrity</small></div><div><span>Stability</span><b>{result?.stability?.score??result?.stability_score??"—"}</b><small>{result?.stability?.level||"benign-transform test"}</small></div></div>
    <div className="v9-xai"><span>EXPLAINABILITY</span>{artifact(result?.artifacts?.gradcam)?<img src={artifact(result.artifacts.gradcam)} alt="Grad-CAM"/>:<p>Grad-CAM artifact not returned.</p>}<small>Attribution in retinal FOV: {result?.xai_integrity?.attribution_in_retinal_fov??"—"}%</small></div>
    <div className="v9-anatomy"><span>ANATOMY</span><p><CheckCircle2 size={14}/> Optic disc / fovea / vessel layer: {result?.structure?.status||(result?.structure?"available":"not returned")}</p></div>
   </>}
  </div>
  {result&&<div className="v9-card v9-ledger"><span className="eyebrow">CASE LEDGER</span><div><span>Case</span><b>{result.case_id}</b></div><div><span>Quality</span><b>{q?.status}</b></div><div><span>ICDR</span><b>{pred?("G"+pred.icdr_grade):"blocked"}</b></div><div><span>Priority</span><b>{rec?.priority||"—"}</b></div>{result?.timings?.total_ms!=null&&<div><span>Inference</span><b>{(Number(result.timings.total_ms)/1000).toFixed(2)} s</b></div>}{result?.artifacts?.report&&<a href={artifact(result.artifacts.report)} target="_blank" rel="noreferrer"><FileText size={16}/> Open annotated report</a>}</div>}
  </aside></main>
 </div>
}