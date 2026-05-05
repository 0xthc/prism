import { useState, useEffect, useMemo } from 'react'
import { supabase } from './supabase.js'

// ── Helpers ──────────────────────────────────────────────────────────────────
function daysSince(d) { return Math.floor((Date.now() - new Date(d)) / 86400000) }
function fmt(d) { return new Date(d).toLocaleDateString('en-US', { month:'short', day:'numeric', year:'numeric' }) }
function norm(s) { return (s||'').toLowerCase().replace(/[^a-z0-9]/g,'') }

// ── Sample data ───────────────────────────────────────────────────────────────
const SAMPLE_SIGNALS = [
  { id:1, name:'PDRN Serum', type:'trend', category:'cosmetics', maturity:'heating', signal_strength:4, first_spotted:'2026-03-31', updated_at:'2026-04-28', sources:[{label:'Byrdie',url:'#'},{label:'Reddit r/SkincareAddiction',url:'#'}], notes:'Salmon DNA-derived regenerative ingredient. Huge in Korea, crossing over.', trajectory_description:'Search up 340% in 90 days. 3 new indie brands launched Q1 2026.', is_weekly_pick:true },
  { id:2, name:'Rucking Backpacks', type:'brand', category:'fitness', maturity:'heating', signal_strength:3, first_spotted:'2026-03-16', updated_at:'2026-04-25', sources:[{label:'GoRuck',url:'#'},{label:'r/Fitness',url:'#'}], notes:'Military-inspired weighted walking. GORUCK dominating but indie challengers appearing.', trajectory_description:'Strong Reddit community. Several DTC launches in past 60 days.', is_weekly_pick:false },
  { id:3, name:'Mushroom Chocolate', type:'trend', category:'food', maturity:'early', signal_strength:3, first_spotted:'2026-04-10', updated_at:'2026-04-27', sources:[{label:'Whole Foods',url:'#'},{label:'Substack',url:'#'}], notes:"Functional chocolate with lion's mane / reishi. Early shelf placement at Erewhon.", trajectory_description:'Few brands but search velocity accelerating. Watch for mainstream entry.', is_weekly_pick:true },
  { id:4, name:'Bakuchiol Serum', type:'trend', category:'cosmetics', maturity:'peaking', signal_strength:5, first_spotted:'2026-01-31', updated_at:'2026-04-20', sources:[{label:'Sephora',url:'#'},{label:'Allure',url:'#'},{label:'TikTok',url:'#'}], notes:'Plant-based retinol alternative. Now on Sephora homepage.', trajectory_description:'Mainstream arrival confirmed. Incumbent brands launching derivatives. Peak window.', is_weekly_pick:false },
  { id:5, name:'Barrel Fit Jeans', type:'trend', category:'lifestyle', maturity:'heating', signal_strength:4, first_spotted:'2026-04-15', updated_at:'2026-04-29', sources:[{label:'Lyst',url:'#'},{label:'Instagram',url:'#'}], notes:'Post-wide-leg silhouette shift. Gap + Madewell both dropped versions.', trajectory_description:'Strong social engagement. Retail adoption fast-following editorial.', is_weekly_pick:true },
  { id:6, name:'Beet Gummies', type:'brand', category:'wellness', maturity:'early', signal_strength:2, first_spotted:'2026-03-01', updated_at:'2026-04-10', sources:[{label:'DTC brand site',url:'#'}], notes:'Nitric oxide + beet root in gummy format. One brand so far.', trajectory_description:'Single-source signal. No retail placement yet. Too early to score.', is_weekly_pick:false },
]

const SAMPLE_INTEL = [
  { id:1, headline:'Unilever acquires Grüns for $1.2B', stream_type:'deals', category:'food & bev', deal_size_tier:'$1B+', context_line:'Validates gummy supplement DTC-to-exit playbook. Watch Church & Dwight and P&G next.', source_url:'#', source_name:'TechCrunch', published_at:'2026-04-29', notes:'' },
  { id:2, headline:'FDA schedules hearings on 12 synthetic peptides for 503A Bulks List', stream_type:'regulatory', category:'wellness', deal_size_tier:null, context_line:'Regulatory unlock for injectable peptide market. Hims already positioned. Watch Ro.', source_url:'#', source_name:'FDA.gov', published_at:'2026-04-23', notes:'' },
  { id:3, headline:'Henkel acquires Olaplex', stream_type:'deals', category:'beauty', deal_size_tier:'$1B+', context_line:'Prestige hair care consolidation accelerating. Indie brands in science-led hair are acquisition targets.', source_url:'#', source_name:'Bloomberg', published_at:'2026-03-26', notes:'' },
  { id:4, headline:'PDRN clinical trial for skin regeneration completes phase 2', stream_type:'research', category:'cosmetics', deal_size_tier:null, context_line:'Ingredient credentialing with clinical backing. Watch for brand launches citing this trial.', source_url:'#', source_name:'PubMed', published_at:'2026-04-15', notes:'' },
  { id:5, headline:'Laoban bao rolls into 1,500 Target stores', stream_type:'retail', category:'food & bev', deal_size_tier:null, context_line:'Asian comfort food crossing chasm to mass retail. Replicable playbook for dumplings, scallion pancakes.', source_url:'#', source_name:'Retail Dive', published_at:'2026-04-27', notes:'' },
]

const SAMPLE_METRICS = [
  { id:1, category:'Functional Food/Bev', deal_count:23, share_pct:31, prev_share_pct:23, saturation_status:'crowded', rotation_status:'rotating_in' },
  { id:2, category:'Beauty/Skincare', deal_count:18, share_pct:24, prev_share_pct:22, saturation_status:'active', rotation_status:'stable' },
  { id:3, category:'Wellness Supplements', deal_count:12, share_pct:16, prev_share_pct:19, saturation_status:'thinning', rotation_status:'rotating_out' },
  { id:4, category:'Mental Health/Wellness Tech', deal_count:8, share_pct:11, prev_share_pct:6, saturation_status:'active', rotation_status:'rotating_in' },
  { id:5, category:'Fashion/Apparel', deal_count:4, share_pct:5, prev_share_pct:9, saturation_status:'cold', rotation_status:'rotating_out' },
]

const SAMPLE_DEALS = [
  { id:1, fund_name:'Forerunner Ventures', company_name:'Grüns', category:'Functional Food/Bev', round_stage:'Acquisition', round_size_m:1200, deal_date:'2026-04-29' },
  { id:2, fund_name:'Imaginary Ventures', company_name:'Deux', category:'Beauty/Skincare', round_stage:'Series A', round_size_m:12, deal_date:'2026-03-15' },
  { id:3, fund_name:'Coefficient Capital', company_name:'Hiyo', category:'Functional Food/Bev', round_stage:'Series B', round_size_m:30, deal_date:'2026-02-10' },
  { id:4, fund_name:'True Beauty Ventures', company_name:'Youthforia', category:'Beauty/Skincare', round_stage:'Series A', round_size_m:8, deal_date:'2026-01-20' },
  { id:5, fund_name:'Collaborative Fund', company_name:'Hims & Hers', category:'Mental Health/Wellness Tech', round_stage:'Follow-on', round_size_m:50, deal_date:'2026-04-01' },
]

const FUNDS_REFERENCE = [
  { name:'Forerunner Ventures', thesis:'Next-gen consumer brands + commerce infrastructure' },
  { name:'Imaginary Ventures', thesis:'Premium consumer brands with cultural resonance' },
  { name:'Coefficient Capital', thesis:'Data-driven consumer brands, food & bev focus' },
  { name:'Collaborative Fund', thesis:'Consumer brands with positive social/cultural impact' },
  { name:'True Beauty Ventures', thesis:'Prestige + inclusive beauty brands' },
  { name:'L Catterton', thesis:'Global luxury + premium consumer growth equity' },
  { name:'Lerer Hippeau', thesis:'Early-stage consumer + media + commerce' },
  { name:'Selva Ventures', thesis:'Health, wellness, sustainability — food & beauty' },
  { name:'Silas Capital', thesis:'Luxury + premium consumer brands' },
  { name:'CircleUp', thesis:'Early-stage CPG + retail brands' },
  { name:'BFG Partners', thesis:'Better-for-you food, beverage, wellness' },
  { name:'VMG Catalyst', thesis:'Emerging CPG + consumer brands' },
  { name:'Monogram Capital', thesis:'Health & wellness consumer brands' },
  { name:'Willow Growth', thesis:'Sustainable consumer + food & bev' },
]

// ── Tag styles ────────────────────────────────────────────────────────────────
const TAG = {
  base: { fontSize:11, fontWeight:500, padding:'2px 8px', borderRadius:4, display:'inline-block', marginRight:4 },
  maturity: { early:{background:'#e3f2fd',color:'#1565c0'}, heating:{background:'#fff3e0',color:'#bf5000'}, peaking:{background:'#ffebee',color:'#b71c1c'} },
  stream: { deals:{background:'#e8f5e9',color:'#2e7d32'}, regulatory:{background:'#fce4ec',color:'#c2185b'}, research:{background:'#e3f2fd',color:'#1565c0'}, retail:{background:'#f3e5f5',color:'#7b1fa2'} },
  rotation: { rotating_in:{background:'#e8f5e9',color:'#2e7d32'}, rotating_out:{background:'#ffebee',color:'#b71c1c'}, stable:{background:'#f4f4f1',color:'#666'} },
  saturation: { crowded:{background:'#ffebee',color:'#b71c1c'}, active:{background:'#e8f5e9',color:'#2e7d32'}, thinning:{background:'#fff3e0',color:'#bf5000'}, cold:{background:'#f4f4f1',color:'#999'} },
}
function Tag({ type, value }) {
  const map = TAG[type] || {}
  const s = map[(value||'').toLowerCase()] || { background:'#eee', color:'#666' }
  return <span style={{...TAG.base,...s}}>{value}</span>
}

// ── Toast ─────────────────────────────────────────────────────────────────────
function Toast({ msg, onDone }) {
  useEffect(() => { const t = setTimeout(onDone, 2000); return () => clearTimeout(t) }, [onDone])
  if (!msg) return null
  return (
    <div style={{ position:'fixed', bottom:24, right:24, background: msg.ok ? '#2e7d32' : '#b71c1c', color:'#fff', padding:'10px 18px', borderRadius:6, fontSize:13, zIndex:9999 }}>
      {msg.ok ? '✓ ' : '✗ '}{msg.text}
    </div>
  )
}

// ── Modal ─────────────────────────────────────────────────────────────────────
function Modal({ title, children, onClose }) {
  return (
    <div style={{ position:'fixed', inset:0, background:'rgba(0,0,0,0.4)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:1000 }}>
      <div style={{ background:'#fff', borderRadius:10, padding:24, width:'100%', maxWidth:480, position:'relative' }}>
        <button onClick={onClose} style={{ position:'absolute', top:12, right:16, border:'none', background:'none', fontSize:18, cursor:'pointer', color:'#666' }}>×</button>
        <h3 style={{ margin:'0 0 16px', fontSize:15 }}>{title}</h3>
        {children}
      </div>
    </div>
  )
}
function Field({ label, children }) {
  return <div style={{ marginBottom:12 }}><label style={{ display:'block', fontSize:12, color:'#666', marginBottom:4 }}>{label}</label>{children}</div>
}
const inp = { width:'100%', padding:'6px 10px', border:'1px solid #ddd', borderRadius:5, fontSize:13 }
const btnPrimary = { background:'#1a1a1a', color:'#fff', border:'none', borderRadius:5, padding:'8px 18px', fontSize:13, cursor:'pointer', marginRight:8 }
const btnSecondary = { background:'none', border:'1px solid #ddd', borderRadius:5, padding:'8px 18px', fontSize:13, cursor:'pointer' }


// ── SIGNALS TAB ───────────────────────────────────────────────────────────────
function SignalsTab({ signals, onAdd }) {
  const [cat, setCat] = useState('all')
  const [mat, setMat] = useState('all')
  const [minStr, setMinStr] = useState(1)
  const [view, setView] = useState('digest')
  const [expanded, setExpanded] = useState(null)
  const [showModal, setShowModal] = useState(false)

  const filtered = useMemo(() => {
    let list = signals
    if (view === 'digest') list = list.filter(s => s.is_weekly_pick).sort((a,b) => new Date(b.updated_at)-new Date(a.updated_at)).slice(0,5)
    else {
      if (cat !== 'all') list = list.filter(s => s.category === cat)
      if (mat !== 'all') list = list.filter(s => s.maturity === mat)
      list = list.filter(s => s.signal_strength >= minStr)
    }
    return list
  }, [signals, view, cat, mat, minStr])

  const stages = ['early','heating','peaking']

  return (
    <div>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:16 }}>
        <div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
          <select style={inp} value={view} onChange={e=>setView(e.target.value)} disabled={false}>
            <option value="digest">Weekly Digest</option>
            <option value="all">All Signals</option>
          </select>
          {view==='all' && <>
            <select style={inp} value={cat} onChange={e=>setCat(e.target.value)}>
              {['all','food','cosmetics','wellness','fitness','lifestyle'].map(c=><option key={c} value={c}>{c==='all'?'All Categories':c}</option>)}
            </select>
            <select style={inp} value={mat} onChange={e=>setMat(e.target.value)}>
              <option value="all">All Maturity</option>
              <option value="early">Early</option>
              <option value="heating">Heating</option>
              <option value="peaking">Peaking</option>
            </select>
            <select style={inp} value={minStr} onChange={e=>setMinStr(Number(e.target.value))}>
              <option value={1}>Signal 1+</option>
              <option value={3}>Signal 3+</option>
              <option value={5}>Signal 5</option>
            </select>
          </>}
        </div>
        <button style={btnPrimary} onClick={()=>setShowModal(true)}>+ Add Signal</button>
      </div>

      {view==='digest' && <p style={{ fontSize:12, color:'#888', margin:'0 0 12px' }}>Top picks this week</p>}

      {filtered.map(s => {
        const isExp = expanded === s.id
        const dots = n => Array.from({length:5},(_,i)=><span key={i} style={{ color: i<n ? '#1a1a1a' : '#ddd', marginRight:1 }}>{i<n?'●':'○'}</span>)
        return (
          <div key={s.id} onClick={()=>setExpanded(isExp?null:s.id)}
            style={{ background:'#fff', border:'1px solid #e8e8e4', borderRadius:8, padding:16, marginBottom:10, cursor:'pointer' }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:8 }}>
              <div>
                <span style={{ fontWeight:600, fontSize:14, marginRight:8 }}>{s.name}</span>
                <Tag type="stream" value={s.type==='trend'?'research':'deals'} />
                <span style={{...TAG.base, background:'#f4f4f1', color:'#555'}}>{s.category}</span>
              </div>
              <Tag type="maturity" value={s.maturity} />
            </div>

            {/* Lifecycle bar */}
            <div style={{ display:'flex', gap:4, marginBottom:8, fontSize:11 }}>
              {stages.map(st => (
                <span key={st} style={{ padding:'2px 10px', borderRadius:3, fontSize:11,
                  background: s.maturity===st ? '#1a1a1a' : '#f0f0ee',
                  color: s.maturity===st ? '#fff' : '#888',
                  fontWeight: s.maturity===st ? 600 : 400 }}>
                  {st.charAt(0).toUpperCase()+st.slice(1)}
                </span>
              ))}
            </div>

            <div style={{ display:'flex', alignItems:'center', gap:16, marginBottom:8 }}>
              <div style={{ fontSize:12 }}>Signal: {dots(s.signal_strength)}</div>
              <div style={{ width:90, height:18, background:'#e8e8e4', borderRadius:3 }} title="Trajectory sparkline" />
            </div>

            <div style={{ fontSize:11, color:'#888' }}>First spotted {fmt(s.first_spotted)} · {daysSince(s.first_spotted)} days ago</div>

            {isExp && (
              <div style={{ marginTop:12, paddingTop:12, borderTop:'1px solid #f0f0ee' }}>
                {(s.sources||[]).length > 0 && (
                  <div style={{ marginBottom:8 }}>
                    <span style={{ fontSize:11, color:'#888', marginRight:6 }}>Sources:</span>
                    {s.sources.map((src,i)=>(
                      <a key={i} href={src.url} target="_blank" rel="noreferrer"
                        style={{...TAG.base, background:'#f4f4f1', color:'#333', textDecoration:'none', marginRight:4}}
                        onClick={e=>e.stopPropagation()}>{src.label}</a>
                    ))}
                  </div>
                )}
                {s.notes && <p style={{ fontSize:12, margin:'0 0 6px', color:'#444' }}>{s.notes}</p>}
                {s.trajectory_description && <p style={{ fontSize:12, margin:0, color:'#666', fontStyle:'italic' }}>{s.trajectory_description}</p>}
              </div>
            )}
          </div>
        )
      })}

      {filtered.length === 0 && <div style={{ textAlign:'center', color:'#aaa', padding:40 }}>No signals match your filters.</div>}

      {showModal && <SignalModal onClose={()=>setShowModal(false)} onAdd={onAdd} />}
    </div>
  )
}

function SignalModal({ onClose, onAdd }) {
  const [form, setForm] = useState({ name:'', type:'trend', category:'cosmetics', maturity:'early', signal_strength:3, notes:'', source_url:'' })
  const set = k => e => setForm(f=>({...f,[k]:e.target.value}))
  return (
    <Modal title="Add Signal" onClose={onClose}>
      <Field label="Name"><input style={inp} value={form.name} onChange={set('name')} /></Field>
      <Field label="Type">
        <select style={inp} value={form.type} onChange={set('type')}>
          <option value="trend">Trend</option><option value="brand">Brand</option>
        </select>
      </Field>
      <Field label="Category">
        <select style={inp} value={form.category} onChange={set('category')}>
          {['food','cosmetics','wellness','fitness','lifestyle'].map(c=><option key={c} value={c}>{c}</option>)}
        </select>
      </Field>
      <Field label="Maturity">
        <select style={inp} value={form.maturity} onChange={set('maturity')}>
          <option value="early">Early</option><option value="heating">Heating</option><option value="peaking">Peaking</option>
        </select>
      </Field>
      <Field label="Signal Strength (1-5)">
        <select style={inp} value={form.signal_strength} onChange={set('signal_strength')}>
          {[1,2,3,4,5].map(n=><option key={n} value={n}>{n}</option>)}
        </select>
      </Field>
      <Field label="Notes"><textarea style={{...inp,height:60,resize:'vertical'}} value={form.notes} onChange={set('notes')} /></Field>
      <Field label="Source URL"><input style={inp} value={form.source_url} onChange={set('source_url')} /></Field>
      <div style={{ marginTop:16 }}>
        <button style={btnPrimary} onClick={()=>onAdd(form,onClose)}>Add</button>
        <button style={btnSecondary} onClick={onClose}>Cancel</button>
      </div>
    </Modal>
  )
}


// ── INTEL TAB ─────────────────────────────────────────────────────────────────
function IntelTab({ items, signals, onAdd }) {
  const [streamF, setStreamF] = useState('all')
  const [catF, setCatF] = useState('all')
  const [tierF, setTierF] = useState('all')
  const [dateF, setDateF] = useState('all')
  const [view, setView] = useState('feed')
  const [showModal, setShowModal] = useState(false)

  const heatingCats = useMemo(() => signals.filter(s=>s.maturity==='heating').map(s=>norm(s.category)), [signals])

  const cutoff = useMemo(() => {
    if (dateF==='7d') return Date.now()-7*86400000
    if (dateF==='30d') return Date.now()-30*86400000
    if (dateF==='90d') return Date.now()-90*86400000
    return 0
  }, [dateF])

  const filtered = useMemo(() => items.filter(it => {
    if (streamF!=='all' && it.stream_type!==streamF) return false
    if (catF!=='all' && it.category!==catF) return false
    if (tierF!=='all' && it.deal_size_tier!==tierF) return false
    if (cutoff && new Date(it.published_at)<cutoff) return false
    return true
  }), [items, streamF, catF, tierF, cutoff])

  const categories = useMemo(() => [...new Set(items.map(i=>i.category))].sort(), [items])

  // Velocity view data
  const velocityData = useMemo(() => {
    const months = []
    for (let i=5; i>=0; i--) {
      const d = new Date(); d.setMonth(d.getMonth()-i)
      months.push({ label: d.toLocaleDateString('en-US',{month:'short',year:'2-digit'}), key: `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}` })
    }
    const cats = [...new Set(items.map(i=>i.category))]
    return cats.map(cat => ({
      cat,
      counts: months.map(m => ({
        ...m,
        count: items.filter(it => it.category===cat && it.published_at && it.published_at.startsWith(m.key)).length
      }))
    }))
  }, [items])

  return (
    <div>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:12 }}>
        <div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
          <select style={inp} value={streamF} onChange={e=>setStreamF(e.target.value)}>
            {['all','deals','regulatory','research','retail'].map(s=><option key={s} value={s}>{s==='all'?'All Types':s.charAt(0).toUpperCase()+s.slice(1)}</option>)}
          </select>
          <select style={inp} value={catF} onChange={e=>setCatF(e.target.value)}>
            <option value="all">All Categories</option>
            {categories.map(c=><option key={c} value={c}>{c}</option>)}
          </select>
          <select style={inp} value={tierF} onChange={e=>setTierF(e.target.value)}>
            {['all','<$10M','$10-100M','$100M-1B','$1B+'].map(t=><option key={t} value={t}>{t==='all'?'All Sizes':t}</option>)}
          </select>
          <select style={inp} value={dateF} onChange={e=>setDateF(e.target.value)}>
            <option value="all">All Time</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
          </select>
          <div style={{ display:'flex', border:'1px solid #ddd', borderRadius:5, overflow:'hidden' }}>
            {['feed','velocity'].map(v=>(
              <button key={v} onClick={()=>setView(v)}
                style={{ padding:'5px 14px', border:'none', cursor:'pointer', fontSize:12,
                  background: view===v ? '#1a1a1a' : '#fff',
                  color: view===v ? '#fff' : '#555' }}>
                {v.charAt(0).toUpperCase()+v.slice(1)}
              </button>
            ))}
          </div>
        </div>
        <button style={btnPrimary} onClick={()=>setShowModal(true)}>+ Add Intel</button>
      </div>

      {view==='feed' && (
        <div>
          {filtered.map(it => {
            const isHeating = heatingCats.some(hc => norm(it.category).includes(hc) || hc.includes(norm(it.category)))
            return (
              <div key={it.id} style={{ background:'#fff', border:'1px solid #e8e8e4', borderRadius:8, padding:16, marginBottom:10 }}>
                <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:6 }}>
                  <span style={{ fontWeight:600, fontSize:14, flex:1, marginRight:8 }}>{it.headline}</span>
                  <div style={{ display:'flex', gap:4, flexShrink:0, flexWrap:'wrap', justifyContent:'flex-end' }}>
                    <Tag type="stream" value={it.stream_type} />
                    {it.deal_size_tier && <span style={{...TAG.base,background:'#f4f4f1',color:'#555'}}>{it.deal_size_tier}</span>}
                    {isHeating && <span style={{...TAG.base,background:'#fff3e0',color:'#bf5000'}}>↑ Heating Signal</span>}
                  </div>
                </div>
                <div style={{ fontSize:11, color:'#888', marginBottom:6 }}>
                  <span style={{...TAG.base,background:'#f4f4f1',color:'#666'}}>{it.category}</span>
                </div>
                {it.context_line && <p style={{ fontSize:12, color:'#555', margin:'0 0 8px', lineHeight:1.5 }}>{it.context_line}</p>}
                <div style={{ fontSize:11, color:'#aaa' }}>
                  <a href={it.source_url} target="_blank" rel="noreferrer" style={{ color:'#888', textDecoration:'none' }}>{it.source_name}</a>
                  {' · '}{fmt(it.published_at)}
                </div>
                {it.notes && <div style={{ marginTop:8, background:'#f8f8f6', borderRadius:4, padding:'8px 10px', fontSize:12, color:'#555' }}>{it.notes}</div>}
              </div>
            )
          })}
          {filtered.length===0 && <div style={{ textAlign:'center', color:'#aaa', padding:40 }}>No items match your filters.</div>}
        </div>
      )}

      {view==='velocity' && (
        <div>
          <p style={{ fontSize:12, color:'#888', marginBottom:16 }}>Events per category per month (last 6 months)</p>
          {velocityData.map(({ cat, counts }) => {
            const max = Math.max(...counts.map(c=>c.count), 1)
            return (
              <div key={cat} style={{ marginBottom:20 }}>
                <div style={{ fontSize:12, fontWeight:600, marginBottom:6 }}>{cat}</div>
                <div style={{ display:'flex', gap:4, alignItems:'flex-end', height:60 }}>
                  {counts.map(c=>(
                    <div key={c.key} style={{ flex:1, display:'flex', flexDirection:'column', alignItems:'center', gap:2 }}>
                      <div style={{ width:'100%', background: c.count ? '#1a1a1a' : '#eee', borderRadius:2, height: c.count ? Math.max(6, (c.count/max)*52) : 4 }} />
                      <span style={{ fontSize:9, color:'#aaa' }}>{c.label}</span>
                      {c.count > 0 && <span style={{ fontSize:9, color:'#555' }}>{c.count}</span>}
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {showModal && <IntelModal onClose={()=>setShowModal(false)} onAdd={onAdd} />}
    </div>
  )
}

function IntelModal({ onClose, onAdd }) {
  const [form, setForm] = useState({ headline:'', stream_type:'deals', category:'', deal_size_tier:'', context_line:'', source_url:'', source_name:'', published_at: new Date().toISOString().slice(0,10), notes:'' })
  const set = k => e => setForm(f=>({...f,[k]:e.target.value}))
  return (
    <Modal title="Add Intel" onClose={onClose}>
      <Field label="Headline"><input style={inp} value={form.headline} onChange={set('headline')} /></Field>
      <Field label="Type">
        <select style={inp} value={form.stream_type} onChange={set('stream_type')}>
          {['deals','regulatory','research','retail'].map(s=><option key={s} value={s}>{s.charAt(0).toUpperCase()+s.slice(1)}</option>)}
        </select>
      </Field>
      <Field label="Category"><input style={inp} value={form.category} onChange={set('category')} placeholder="e.g. food & bev" /></Field>
      <Field label="Deal Size (optional)">
        <select style={inp} value={form.deal_size_tier} onChange={set('deal_size_tier')}>
          <option value="">None</option>
          {['<$10M','$10-100M','$100M-1B','$1B+'].map(t=><option key={t} value={t}>{t}</option>)}
        </select>
      </Field>
      <Field label="Context line"><input style={inp} value={form.context_line} onChange={set('context_line')} /></Field>
      <Field label="Source URL"><input style={inp} value={form.source_url} onChange={set('source_url')} /></Field>
      <Field label="Source Name"><input style={inp} value={form.source_name} onChange={set('source_name')} /></Field>
      <Field label="Date"><input type="date" style={inp} value={form.published_at} onChange={set('published_at')} /></Field>
      <Field label="Notes (optional)"><textarea style={{...inp,height:50,resize:'vertical'}} value={form.notes} onChange={set('notes')} /></Field>
      <div style={{ marginTop:16 }}>
        <button style={btnPrimary} onClick={()=>onAdd(form,onClose)}>Add</button>
        <button style={btnSecondary} onClick={onClose}>Cancel</button>
      </div>
    </Modal>
  )
}


// ── LANDSCAPE TAB ─────────────────────────────────────────────────────────────
function FundCards({ deals }) {
  const [expanded, setExpanded] = useState({})

  const byFund = useMemo(() => {
    const map = {}
    deals.forEach(d => {
      if (!map[d.fund_name]) map[d.fund_name] = []
      map[d.fund_name].push(d)
    })
    return Object.entries(map).sort((a,b) => b[1].length - a[1].length)
  }, [deals])

  const catColor = (cat) => {
    const palette = {
      'Beauty & Skincare': '#f3e5f5',
      'Food & Beverage': '#e8f5e9',
      'Fashion & Apparel': '#fff3e0',
      'Functional Food & Bev': '#e0f2f1',
      'Consumer Health & Telehealth': '#e3f2fd',
      'Fitness & Sports': '#fce4ec',
      'Sustainability & Eco': '#f1f8e9',
      'Consumer Tech & Wearables': '#e8eaf6',
      'Pet': '#fff8e1',
      'Baby & Family': '#fce4ec',
      'Personal Care & Hygiene': '#f9fbe7',
      'Home & Living': '#efebe9',
      'Wellness & Supplements': '#e0f7fa',
    }
    return palette[cat] || '#f5f5f5'
  }

  return (
    <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12, marginBottom:24 }}>
      {byFund.map(([fund, companies]) => {
        const isOpen = expanded[fund]
        const catCounts = {}
        companies.forEach(c => { catCounts[c.category] = (catCounts[c.category]||0)+1 })
        const topCats = Object.entries(catCounts).sort((a,b)=>b[1]-a[1]).slice(0,4)
        const total = companies.length

        return (
          <div key={fund} style={{ background:'#fff', border:'1px solid #e8e8e4', borderRadius:8, overflow:'hidden' }}>
            <div onClick={()=>setExpanded(e=>({...e,[fund]:!e[fund]}))}
              style={{ padding:'12px 14px', cursor:'pointer', display:'flex', justifyContent:'space-between', alignItems:'flex-start' }}>
              <div>
                <div style={{ fontWeight:600, fontSize:13, marginBottom:6 }}>{fund}</div>
                <div style={{ display:'flex', flexWrap:'wrap', gap:4 }}>
                  {topCats.map(([cat, count]) => (
                    <span key={cat} style={{ fontSize:10, padding:'2px 7px', borderRadius:10, background: catColor(cat), color:'#333' }}>
                      {cat} · {Math.round(count/total*100)}%
                    </span>
                  ))}
                </div>
              </div>
              <div style={{ textAlign:'right', flexShrink:0, marginLeft:8 }}>
                <div style={{ fontSize:18, fontWeight:700, color:'#1a1a1a' }}>{total}</div>
                <div style={{ fontSize:10, color:'#aaa' }}>companies</div>
                <div style={{ fontSize:11, color:'#aaa', marginTop:4 }}>{isOpen ? '▲' : '▼'}</div>
              </div>
            </div>
            {isOpen && (
              <div style={{ borderTop:'1px solid #f4f4f1', maxHeight:260, overflowY:'auto' }}>
                {companies.map((c,i) => (
                  <div key={c.id} style={{ display:'flex', justifyContent:'space-between', alignItems:'center',
                    padding:'7px 14px', borderBottom: i<companies.length-1 ? '1px solid #f9f9f9':'none',
                    fontSize:12 }}>
                    <span style={{ fontWeight:500 }}>{c.company_name}</span>
                    <span style={{ fontSize:10, padding:'2px 6px', borderRadius:8, background: catColor(c.category), color:'#555' }}>
                      {c.category}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

function LandscapeTab({ deals, onAddDeal }) {
  const [portfolioView, setPortfolioView] = useState('all')
  const [showModal, setShowModal] = useState(false)
  const [showFunds, setShowFunds] = useState(false)

  return (
    <div>
      <div style={{ display:'flex', justifyContent:'flex-end', marginBottom:16 }}>
        <button style={btnPrimary} onClick={()=>setShowModal(true)}>+ Add Deal</button>
      </div>

      {/* Portfolio section — toggle All / By Fund */}
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:12 }}>
        <h4 style={{ fontSize:13, fontWeight:600, margin:0 }}>Portfolio</h4>
        <div style={{ display:'flex', border:'1px solid #ddd', borderRadius:5, overflow:'hidden' }}>
          {['all','by-fund'].map(v=>(
            <button key={v} onClick={()=>setPortfolioView(v)}
              style={{ padding:'4px 12px', border:'none', cursor:'pointer', fontSize:11,
                background: portfolioView===v ? '#1a1a1a' : '#fff',
                color: portfolioView===v ? '#fff' : '#555' }}>
              {v==='all' ? 'All Funds' : 'By Fund'}
            </button>
          ))}
        </div>
      </div>

      {portfolioView==='all' && (
        <div style={{ background:'#fff', border:'1px solid #e8e8e4', borderRadius:8, overflow:'hidden', marginBottom:24 }}>
          <table style={{ width:'100%', borderCollapse:'collapse' }}>
            <thead>
              <tr style={{ background:'#fafafa' }}>
                {['Fund','Company','Category','Stage','Size'].map(h=>(
                  <th key={h} style={{ textAlign:'left', fontSize:11, color:'#888', fontWeight:500, padding:'6px 8px', borderBottom:'1px solid #e8e8e4' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {deals.map((d,i)=>(
                <tr key={d.id} style={{ borderBottom: i<deals.length-1 ? '1px solid #f4f4f1' : 'none' }}>
                  <td style={{ padding:'8px', fontSize:12 }}>{d.fund_name}</td>
                  <td style={{ padding:'8px', fontSize:13, fontWeight:500 }}>
                    {d.company_name}
                    {d.data_source === 'rss' && d.deal_date && (
                      <span style={{ marginLeft:6, fontSize:11, color:'#888' }}>{fmt(d.deal_date)}</span>
                    )}
                  </td>
                  <td style={{ padding:'8px', fontSize:12 }}>{d.category}</td>
                  <td style={{ padding:'8px', fontSize:12 }}>{d.round_stage}</td>
                  <td style={{ padding:'8px', fontSize:12 }}>{d.round_size_m ? `$${d.round_size_m}M` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {portfolioView==='by-fund' && (
        <FundCards deals={deals} />
      )}

      {/* Funds panel */}
      <button style={btnSecondary} onClick={()=>setShowFunds(v=>!v)}>
        {showFunds ? 'Hide' : 'Show'} Tracked Funds ({FUNDS_REFERENCE.length})
      </button>
      {showFunds && (
        <div style={{ marginTop:16, display:'grid', gridTemplateColumns:'1fr 1fr', gap:10 }}>
          {FUNDS_REFERENCE.map(f=>(
            <div key={f.name} style={{ background:'#fff', border:'1px solid #e8e8e4', borderRadius:6, padding:12 }}>
              <div style={{ fontWeight:600, fontSize:13, marginBottom:4 }}>{f.name}</div>
              <div style={{ fontSize:11, color:'#888' }}>{f.thesis}</div>
            </div>
          ))}
        </div>
      )}

      {showModal && <LandscapeModal onClose={()=>setShowModal(false)} onAdd={onAddDeal} />}
    </div>
  )
}

function LandscapeModal({ onClose, onAdd }) {
  const [form, setForm] = useState({ fund_name:'', company_name:'', category:'', round_stage:'', round_size_m:'', deal_date: new Date().toISOString().slice(0,10) })
  const set = k => e => setForm(f=>({...f,[k]:e.target.value}))
  return (
    <Modal title="Add Deal" onClose={onClose}>
      <Field label="Fund Name"><input style={inp} value={form.fund_name} onChange={set('fund_name')} /></Field>
      <Field label="Company Name"><input style={inp} value={form.company_name} onChange={set('company_name')} /></Field>
      <Field label="Category"><input style={inp} value={form.category} onChange={set('category')} /></Field>
      <Field label="Stage"><input style={inp} value={form.round_stage} onChange={set('round_stage')} placeholder="Series A, Acquisition, etc." /></Field>
      <Field label="Round Size ($M, optional)"><input type="number" style={inp} value={form.round_size_m} onChange={set('round_size_m')} /></Field>
      <Field label="Deal Date"><input type="date" style={inp} value={form.deal_date} onChange={set('deal_date')} /></Field>
      <div style={{ marginTop:16 }}>
        <button style={btnPrimary} onClick={()=>onAdd(form,onClose)}>Add</button>
        <button style={btnSecondary} onClick={onClose}>Cancel</button>
      </div>
    </Modal>
  )
}


// ── ROOT APP ──────────────────────────────────────────────────────────────────
export default function App() {
  const [tab, setTab] = useState('signals')
  const [signals, setSignals] = useState(SAMPLE_SIGNALS)
  const [intel, setIntel] = useState(SAMPLE_INTEL)
  const [metrics, setMetrics] = useState(SAMPLE_METRICS)
  const [deals, setDeals] = useState(SAMPLE_DEALS)
  const [toast, setToast] = useState(null)

  useEffect(() => {
    supabase.from('signals_v2').select('*').order('updated_at',{ascending:false})
      .then(({data,error}) => { if (!error && data && data.length) setSignals(data) })
  }, [])
  useEffect(() => {
    supabase.from('intel_items').select('*').order('published_at',{ascending:false})
      .then(({data,error}) => { if (!error && data && data.length) setIntel(data) })
  }, [])
  useEffect(() => {
    supabase.from('category_metrics').select('*')
      .then(({data,error}) => { if (!error && data && data.length) setMetrics(data) })
    supabase.from('landscape_deals').select('*').order('deal_date',{ascending:false})
      .then(({data,error}) => { if (!error && data && data.length) setDeals(data) })
  }, [])

  async function addSignal(form, onClose) {
    const record = { ...form, signal_strength: Number(form.signal_strength), first_spotted: new Date().toISOString().slice(0,10), updated_at: new Date().toISOString(), is_weekly_pick: false, sources: form.source_url ? [{label:'Source',url:form.source_url}] : [] }
    const { error } = await supabase.from('signals_v2').insert(record)
    if (error) {
      setSignals(s=>[{ ...record, id: Date.now() }, ...s])
      setToast({ ok:false, text:'Saved locally (Supabase unavailable)' })
    } else {
      const { data } = await supabase.from('signals_v2').select('*').order('updated_at',{ascending:false})
      if (data && data.length) setSignals(data)
      setToast({ ok:true, text:'Added to Signals' })
    }
    onClose()
  }

  async function addIntel(form, onClose) {
    const record = { ...form, deal_size_tier: form.deal_size_tier || null, created_at: new Date().toISOString() }
    const { error } = await supabase.from('intel_items').insert(record)
    if (error) {
      setIntel(s=>[{ ...record, id: Date.now() }, ...s])
      setToast({ ok:false, text:'Saved locally (Supabase unavailable)' })
    } else {
      const { data } = await supabase.from('intel_items').select('*').order('published_at',{ascending:false})
      if (data && data.length) setIntel(data)
      setToast({ ok:true, text:'Added to Intel' })
    }
    onClose()
  }

  async function addDeal(form, onClose) {
    const record = { ...form, round_size_m: form.round_size_m ? Number(form.round_size_m) : null, created_at: new Date().toISOString() }
    const { error } = await supabase.from('landscape_deals').insert(record)
    if (error) {
      setDeals(s=>[{ ...record, id: Date.now() }, ...s])
      setToast({ ok:false, text:'Saved locally (Supabase unavailable)' })
    } else {
      const { data } = await supabase.from('landscape_deals').select('*').order('deal_date',{ascending:false})
      if (data && data.length) setDeals(data)
      setToast({ ok:true, text:'Added to Landscape' })
    }
    onClose()
  }

  const TABS = [
    { id:'signals', label:'Signals' },
    { id:'intel', label:'Intel' },
    { id:'landscape', label:'Landscape' },
  ]

  return (
    <div style={{ minHeight:'100vh', background:'#f8f8f6' }}>
      {/* Nav */}
      <nav style={{ background:'#fff', borderBottom:'1px solid #e8e8e4', padding:'0 24px', display:'flex', alignItems:'center', gap:0, position:'sticky', top:0, zIndex:100 }}>
        <span style={{ fontWeight:700, fontSize:15, letterSpacing:'-0.3px', marginRight:32, padding:'14px 0' }}>Prism</span>
        {TABS.map(t=>(
          <button key={t.id} onClick={()=>setTab(t.id)}
            style={{ padding:'14px 16px', border:'none', borderBottom: tab===t.id ? '2px solid #1a1a1a' : '2px solid transparent', background:'none', cursor:'pointer', fontSize:13, fontWeight: tab===t.id ? 600 : 400, color: tab===t.id ? '#1a1a1a' : '#888', marginBottom:'-1px' }}>
            {t.label}
          </button>
        ))}
      </nav>

      {/* Content */}
      <div style={{ maxWidth:860, margin:'0 auto', padding:'24px 24px 60px' }}>
        {tab==='signals' && <SignalsTab signals={signals} onAdd={addSignal} />}
        {tab==='intel' && <IntelTab items={intel} signals={signals} onAdd={addIntel} />}
        {tab==='landscape' && <LandscapeTab deals={deals} onAddDeal={addDeal} />}
      </div>

      {toast && <Toast msg={toast} onDone={()=>setToast(null)} />}
    </div>
  )
}
