import { useMemo, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { UploadCloud, Activity, FileText, RefreshCw, ShieldAlert } from 'lucide-react'

const API = 'http://127.0.0.1:8000'

function pct01(v, d = 1) {
  return `${(Number(v || 0) * 100).toFixed(d)}%`
}

function pct100(v, d = 1) {
  return `${Number(v || 0).toFixed(d)}%`
}

function Stat({ label, value, sub, tone = 'blue' }) {
  return (
    <div className={`stat-card stat-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {sub ? <small>{sub}</small> : null}
    </div>
  )
}

function Bar({ label, value, suffix = '%', tone = 'cyan' }) {
  const n = Math.max(0, Math.min(Number(value || 0), 100))
  return (
    <div className="metric-bar-row">
      <div className="metric-bar-label"><span>{label}</span><strong>{n.toFixed(1)}{suffix}</strong></div>
      <div className="metric-track"><div className={`metric-fill metric-${tone}`} style={{ width: `${n}%` }} /></div>
    </div>
  )
}

function GradeDistribution({ probs = [], selected }) {
  const labels = ['No DR', 'Mild', 'Moderate', 'Severe', 'PDR']
  return (
    <div className="grade-distribution">
      {labels.map((label, i) => {
        const value = Number(probs[i] || 0) * 100
        return (
          <div key={label} className={`grade-col ${selected === i ? 'grade-col-active' : ''}`}>
            <span>{value.toFixed(1)}%</span>
            <div className="grade-bar-shell"><div className="grade-bar-inner" style={{ height: `${Math.max(value, 1)}%` }} /></div>
            <b>G{i}</b><small>{label}</small>
          </div>
        )
      })}
    </div>
  )
}

function LesionTable({ lesions = {} }) {
  const names = { MA: 'Microaneurysm', HE: 'Hemorrhage', EX: 'Hard exudate', SE: 'Soft exudate' }
  return (
    <div className="lesion-table-pro">
      <div className="lesion-tr lesion-head"><span>Lesion</span><span>Regions</span><span>Area</span><span>Burden</span><span>Mean conf.</span></div>
      {['MA', 'HE', 'EX', 'SE'].map((key) => {
        const item = lesions[key] || {}
        return (
          <div className="lesion-tr" key={key}>
            <span><b>{key}</b><small>{names[key]}</small></span>
            <span>{item.count ?? 0}</span>
            <span>{Number(item.area_px || 0).toLocaleString()} px</span>
            <span>{(Number(item.retinal_area_fraction || 0) * 100).toFixed(4)}%</span>
            <span>{pct01(item.mean_confidence, 2)}</span>
          </div>
        )
      })}
    </div>
  )
}

function RegionalMap({ image, lesions }) {
  const total = Object.values(lesions || {}).reduce((sum, x) => sum + Number(x?.count || 0), 0)
  return (
    <div className="regional-map-wrap">
      <div className="regional-image-frame">
        {image ? <img src={image} alt="Regional lesion map" /> : <div className="image-empty">Regional overlay will appear after analysis</div>}
        <div className="region-grid-overlay">
          <span className="region-label r-st">Superior temporal</span>
          <span className="region-label r-sn">Superior nasal</span>
          <span className="region-label r-m">Macular region</span>
          <span className="region-label r-it">Inferior temporal</span>
          <span className="region-label r-in">Inferior nasal</span>
        </div>
      </div>
      <div className="regional-note">
        <strong>{total}</strong>
        <span>thresholded lesion regions across the retinal field</span>
        <p>Current API exposes full-retina lesion coordinates internally; this view presents the regional evidence overlay without inventing quadrant counts.</p>
      </div>
    </div>
  )
}

function ScoreRing({ label, value, level, color = '#22d3ee' }) {
  const n = Math.max(0, Math.min(Number(value || 0), 100))
  const style = { '--score': `${n * 3.6}deg`, '--ring': color }
  return (
    <div className="score-block">
      <div className="score-ring" style={style}>
        <div><strong>{n.toFixed(1)}</strong><span>/100</span></div>
      </div>
      <h4>{label}</h4>
      <small>{level}</small>
    </div>
  )
}

export default function Analyzer() {
  const inputRef = useRef()
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const artifact = (path) => path ? `${API}${path}` : ''

  const lesionOverlay = result ? artifact(result.artifacts?.lesion_overlay) : ''
  const gradcam = result ? artifact(result.artifacts?.gradcam) : ''
  const report = result ? artifact(result.artifacts?.report) : ''

  const pContrib = useMemo(() => {
    if (!result?.lesions) return []
    const w = { MA: 0.30, HE: 0.30, EX: 0.25, SE: 0.15 }
    return ['MA', 'HE', 'EX', 'SE'].map((k) => ({ key: k, value: Number(result.lesions[k]?.mean_confidence || 0) * w[k] * 100 }))
  }, [result])

  function choose(e) {
    const f = e.target.files?.[0]
    if (!f) return
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setResult(null)
    setError('')
  }

  async function analyze() {
    if (!file) return
    setLoading(true)
    setError('')
    try {
      const body = new FormData()
      body.append('file', file)
      const res = await fetch(`${API}/api/analyze`, { method: 'POST', body })
      const data = await res.json()
      if (!res.ok) throw new Error(data?.detail || 'Analysis failed')
      setResult(data)
      setTimeout(() => document.getElementById('analysis-results')?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 120)
    } catch (e) {
      setError(e.message || 'Could not connect to NetraAI backend')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="section analyzer-section" id="analyze">
      <div className="section-head">
        <div>
          <span className="section-kicker">LIVE MODEL WORKSPACE</span>
          <h2>Run the complete NetraAI pipeline.</h2>
        </div>
        <p>Upload one fundus image. The frontend calls the real FastAPI engine and renders quality, grading, lesion evidence, XAI integrity, P-Score, T-Score and routing.</p>
      </div>

      <div className="upload-console glass-card">
        <div className="upload-zone" onClick={() => inputRef.current?.click()}>
          <input ref={inputRef} type="file" accept="image/*" onChange={choose} hidden />
          <UploadCloud size={30} />
          <div><strong>{file ? file.name : 'Select retinal fundus image'}</strong><span>{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : 'PNG · JPG · TIFF · BMP'}</span></div>
        </div>
        <button className="run-analysis" onClick={analyze} disabled={!file || loading}>
          {loading ? <><RefreshCw size={17} className="spin" /> Running TRACE-DR…</> : <><Activity size={17} /> Run NetraAI analysis</>}
        </button>
        {error ? <div className="analysis-error"><ShieldAlert size={16} /> {error}</div> : null}
      </div>

      {loading ? (
        <div className="pipeline-loader glass-card">
          {['Quality gate', 'Restoration audit', 'ICDR + RDR', '512px tile inference', 'MA · HE · EX · SE', 'Grad-CAM', 'Concordance', 'Trust routing'].map((x, i) => (
            <motion.div key={x} initial={{ opacity: 0.25 }} animate={{ opacity: [0.25, 1, 0.25] }} transition={{ duration: 1.6, repeat: Infinity, delay: i * 0.12 }}><span>{String(i + 1).padStart(2, '0')}</span>{x}</motion.div>
          ))}
        </div>
      ) : null}

      {result ? (
        <div id="analysis-results" className="analysis-results">
          <div className="result-banner glass-card">
            <div><span className="section-kicker">SCREENING RESULT</span><h3>{result.prediction ? `ICDR Grade ${result.prediction.icdr_grade} · ${result.prediction.grade_name}` : 'Ungradeable image'}</h3><p>Analysis ID: {result.source?.analysis_id || result.case_id}</p></div>
            <div className={`routing-chip priority-${String(result.recommendation?.priority || '').toLowerCase()}`}><small>FINAL ROUTING</small><strong>{result.recommendation?.action?.replaceAll('_', ' ')}</strong></div>
          </div>

          {result.prediction ? <>
            <div className="stat-grid">
              <Stat label="RDR probability" value={pct01(result.prediction.rdr_probability, 2)} sub={result.prediction.referable_dr ? 'Referable DR positive' : 'Non-referable'} tone={result.prediction.referable_dr ? 'red' : 'green'} />
              <Stat label="Grade confidence" value={pct01(result.prediction.grade_confidence, 2)} sub="Raw confidence · calibration pending" />
              <Stat label="Image reliability" value={pct01(result.quality.score, 1)} sub={result.quality.status} tone="green" />
              <Stat label="P-Score" value={`${result.p_score} / 100`} sub="Pathology evidence summary" tone="cyan" />
              <Stat label="Concordance" value={`${result.concordance.score} / 100`} sub={result.concordance.status} tone="violet" />
              <Stat label="T-Score" value={`${result.t_score.score} / 100`} sub={`${result.t_score.level} trust`} tone="amber" />
            </div>

            <div className="three-view-grid">
              <article className="visual-panel glass-card"><div className="panel-title"><span>INPUT</span><h3>Original fundus</h3></div><div className="retina-image-stage">{preview && <img src={preview} alt="Original fundus" />}</div></article>
              <article className="visual-panel glass-card"><div className="panel-title"><span>LOCAL PATHOLOGY</span><h3>Lesion evidence overlay</h3></div><div className="retina-image-stage">{lesionOverlay && <img src={lesionOverlay} alt="Lesion overlay" />}</div></article>
              <article className="visual-panel glass-card"><div className="panel-title"><span>GLOBAL XAI</span><h3>Grad-CAM attention</h3></div><div className="retina-image-stage">{gradcam && <img src={gradcam} alt="Grad-CAM" />}</div></article>
            </div>

            <div className="two-col-analysis">
              <article className="analysis-card-pro glass-card"><div className="panel-title"><span>ICDR SEVERITY</span><h3>Grade probability distribution</h3></div><GradeDistribution probs={result.prediction.grade_probabilities} selected={result.prediction.icdr_grade} /><div className="severity-rail">{['0 No DR','1 Mild','2 Moderate','3 Severe','4 PDR'].map((x,i)=><div key={x} className={result.prediction.icdr_grade===i?'severity-active':''}>{x}</div>)}</div></article>
              <article className="analysis-card-pro glass-card"><div className="panel-title"><span>IMAGE RESTORATION</span><h3>Quality and acquisition reliability</h3></div><div className="quality-bars"><Bar label="Focus" value={result.quality.focus*100}/><Bar label="Illumination" value={result.quality.illumination*100}/><Bar label="Contrast" value={result.quality.contrast*100}/><Bar label="Retinal FOV" value={result.quality.fov*100}/></div><div className="restoration-note"><b>{result.quality.enhancement_applied ? 'Adaptive restoration applied' : 'Restoration not required'}</b><p>Borderline images can be enhanced with bounded CLAHE and re-audited. Ungradeable images are routed to recapture rather than silently classified.</p></div></article>
            </div>

            <div className="two-col-analysis lesion-block">
              <article className="analysis-card-pro glass-card"><div className="panel-title"><span>LESION DETECTORS</span><h3>MA · HE · EX · SE quantitative analysis</h3></div><LesionTable lesions={result.lesions} /></article>
              <article className="analysis-card-pro glass-card"><div className="panel-title"><span>REGIONAL RETINA</span><h3>Regional lesion context</h3></div><RegionalMap image={lesionOverlay} lesions={result.lesions} /></article>
            </div>

            <div className="score-lab glass-card">
              <div className="score-lab-head"><div><span className="section-kicker">PATHOLOGY → TRUST</span><h2>NetraAI evidence fusion</h2></div><p>P-Score summarizes local pathology evidence. T-Score summarizes system reliability. Neither score overwrites the predicted diagnosis.</p></div>
              <div className="score-lab-grid">
                <ScoreRing label="P-Score" value={result.p_score} level="Pathology evidence" color="#22d3ee" />
                <div className="score-breakdown"><h4>P-Score contribution view</h4>{pContrib.map(x=><Bar key={x.key} label={`${x.key} weighted evidence`} value={x.value} suffix=" pts" tone="cyan" />)}<small>Prototype transparent index; not an established clinical score.</small></div>
                <ScoreRing label="T-Score" value={result.t_score.score} level={`${result.t_score.level} trust`} color="#f59e0b" />
                <div className="score-breakdown"><h4>T-Score reliability components</h4><Bar label="Image reliability · 25%" value={result.quality.score*100} tone="green"/><Bar label="Model confidence · 25%" value={result.prediction.grade_confidence*100}/><Bar label="Evidence concordance · 30%" value={result.concordance.score} tone="cyan"/><Bar label="XAI integrity · 15%" value={result.xai_integrity.score} tone="violet"/><Bar label="Stability · 5%" value={90} tone="amber"/><small>Model confidence is currently raw/uncalibrated and is labeled accordingly.</small></div>
              </div>
            </div>

            <div className="two-col-analysis">
              <article className="analysis-card-pro glass-card"><div className="panel-title"><span>EXPLAINABILITY</span><h3>Grad-CAM integrity analysis</h3></div><div className="quality-bars"><Bar label="Attribution inside retinal FOV" value={result.xai_integrity.attribution_in_retinal_fov} tone="green"/><Bar label="Attribution overlapping lesions" value={result.xai_integrity.attribution_lesion_overlap} tone="amber"/><Bar label="Overall XAI integrity" value={result.xai_integrity.score} tone="violet"/></div><div className="explanation-callout"><p>Grad-CAM is treated as an attention signal, not proof of pathology. Low lesion overlap reduces trust instead of being hidden.</p></div></article>
              <article className="analysis-card-pro glass-card"><div className="panel-title"><span>BIOMARKER FUSION</span><h3>Retinal biomarker channel</h3></div><div className="biomarker-grid"><div><span>MA burden</span><strong>{(result.lesions.MA.retinal_area_fraction*100).toFixed(4)}%</strong></div><div><span>HE burden</span><strong>{(result.lesions.HE.retinal_area_fraction*100).toFixed(4)}%</strong></div><div><span>EX burden</span><strong>{(result.lesions.EX.retinal_area_fraction*100).toFixed(4)}%</strong></div><div><span>SE burden</span><strong>{(result.lesions.SE.retinal_area_fraction*100).toFixed(4)}%</strong></div><div className="biomarker-disabled"><span>Vessel density</span><strong>Context channel pending</strong></div><div className="biomarker-disabled"><span>Tortuosity / width</span><strong>Context channel pending</strong></div></div><p className="biomarker-honesty">Vessel biomarkers are not fabricated. Until the vessel context module is connected, the UI explicitly marks them unavailable.</p></article>
            </div>

            <div className="clinical-summary glass-card">
              <div className="summary-main"><span className="section-kicker">REVIEWER SUMMARY</span><h2>{result.recommendation.action.replaceAll('_',' ')}</h2><p>NetraAI predicts <b>Grade {result.prediction.icdr_grade} · {result.prediction.grade_name}</b> with RDR probability <b>{pct01(result.prediction.rdr_probability,2)}</b>. Pathology-grade concordance is <b>{result.concordance.score}/100 ({result.concordance.status})</b>, while XAI integrity is <b>{result.xai_integrity.score}/100</b>, producing a <b>{result.t_score.score}/100 {result.t_score.level}</b> trust assessment.</p><ul>{result.concordance.supporting_evidence?.map(x=><li key={x}>{x}</li>)}</ul></div>
              <div className="summary-action"><small>REASON</small><p>{result.recommendation.reason}</p>{report ? <a href={report} target="_blank" rel="noreferrer" className="report-link"><FileText size={17}/> Open detailed NetraAI PDF</a> : <span className="report-pending">Detailed PDF route not returned by API</span>}</div>
            </div>
          </> : <div className="ungradeable-panel glass-card"><ShieldAlert size={32}/><h3>Image requires recapture</h3><p>{result.recommendation?.reason}</p></div>}
        </div>
      ) : null}
    </section>
  )
}
