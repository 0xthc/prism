import { useState, useMemo, useEffect } from 'react'
import { supabase } from './supabase.js'

const TABS = ['Precognition', 'Market', 'Trends', 'Intel']

const CATEGORIES = [
  'Food & Drink',
  'Beauty',
  'Health & Fitness',
  'Lifestyle',
  'Fashion',
  'Sustainability',
  'Consumer AI',
]

const SOURCES = ['App Store', 'Product Hunt', 'Press', 'Accelerator', 'Newsletter']

const MOCK_PRODUCTS = [
  {
    id: 1,
    name: 'Zestful',
    category: 'Consumer AI',
    differentiation: 'AI meal coach that learns from your grocery receipts — no logging, no friction',
    sources: ['App Store', 'Product Hunt'],
    source_detail: 'PH launch · Digital Native mention',
    date_spotted: '2026-02-20',
    pmf_flag: '',
  },
  {
    id: 2,
    name: 'Phlur Reserve',
    category: 'Beauty',
    differentiation: 'Refillable fine fragrance with carbon-attributed supply chain — premium sustainability without compromise',
    sources: ['Press', 'Accelerator'],
    source_detail: 'Glossy · Chobani Incubator W26',
    date_spotted: '2026-02-14',
    pmf_flag: 'Interesting',
  },
  {
    id: 3,
    name: 'Lokal Foods',
    category: 'Food & Drink',
    differentiation: 'Hyper-local fermented snacks distributed through neighborhood bodegas, not grocery chains',
    sources: ['Press', 'Accelerator'],
    source_detail: 'The Spoon · Techstars Consumer W25',
    date_spotted: '2026-01-30',
    pmf_flag: 'Watch',
  },
  {
    id: 4,
    name: 'Stillness',
    category: 'Health & Fitness',
    differentiation: 'Sleep quality tracker using only microphone — no wearable required, privacy-first',
    sources: ['App Store', 'Product Hunt'],
    source_detail: 'App Store Health & Fitness · PH #1 of day',
    date_spotted: '2026-02-10',
    pmf_flag: 'Watch',
  },
  {
    id: 5,
    name: 'Packd',
    category: 'Fashion',
    differentiation: 'Gen Z capsule wardrobe builder — buy less, style more. Resale-native from day one',
    sources: ['Newsletter', 'Product Hunt'],
    source_detail: 'Digital Native · PH launch',
    date_spotted: '2026-02-18',
    pmf_flag: '',
  },
  {
    id: 6,
    name: 'Onda Sparkling',
    category: 'Food & Drink',
    differentiation: 'Functional sparkling water with adaptogens — ashwagandha + lion\'s mane positioned as "clarity drink"',
    sources: ['Press', 'Accelerator'],
    source_detail: 'Modern Retail · SKS Accelerator',
    date_spotted: '2026-02-05',
    pmf_flag: 'Interesting',
  },
  {
    id: 7,
    name: 'Hana Skin',
    category: 'Beauty',
    differentiation: 'Bakuchiol-first skincare for sensitive skin — clinical results of retinol without the irritation',
    sources: ['Press', 'Newsletter'],
    source_detail: 'Glossy · Consumer VC newsletter',
    date_spotted: '2026-01-25',
    pmf_flag: 'Watch',
  },
  {
    id: 8,
    name: 'Tempo Social',
    category: 'Health & Fitness',
    differentiation: 'Group workout app that pairs strangers for accountability — Strava meets Bumble BFF',
    sources: ['App Store', 'Newsletter'],
    source_detail: 'App Store · Not Boring mention',
    date_spotted: '2026-02-22',
    pmf_flag: '',
  },
  {
    id: 9,
    name: 'Forma',
    category: 'Sustainability',
    differentiation: 'Circular home goods brand — returns accepted always, refurbished and resold at 60% margin',
    sources: ['Accelerator', 'Press'],
    source_detail: 'Target Accelerator · Modern Retail',
    date_spotted: '2026-02-01',
    pmf_flag: 'Interesting',
  },
  {
    id: 10,
    name: 'Grove Daily',
    category: 'Lifestyle',
    differentiation: 'AI morning routine builder — combines weather, calendar, and biometric data to optimize your day start',
    sources: ['App Store', 'Product Hunt'],
    source_detail: 'App Store Lifestyle · PH launch',
    date_spotted: '2026-02-25',
    pmf_flag: '',
  },
  {
    id: 11,
    name: 'Temple',
    category: 'Health & Fitness',
    differentiation: 'Brain-monitoring wearable that converts EEG data into real-time cognitive performance signals — Oura Ring for your mind. Founded by Deepinder Goyal (Zomato co-founder). $54M F&F at $190M post-money.',
    sources: ['Press', 'Newsletter'],
    source_detail: 'Morning Digest · Consumer VC',
    date_spotted: '2026-02-28',
    pmf_flag: 'Watch',
  },
]

const CATEGORY_STYLES = {
  'Food & Drink': { bg: '#fff3e0', color: '#bf5000' },
  'Beauty':        { bg: '#fce4ec', color: '#c2185b' },
  'Health & Fitness': { bg: '#e8f5e9', color: '#2e7d32' },
  'Lifestyle':     { bg: '#e8eaf6', color: '#3949ab' },
  'Fashion':       { bg: '#f3e5f5', color: '#7b1fa2' },
  'Sustainability':{ bg: '#e0f2f1', color: '#00695c' },
  'Consumer AI':   { bg: '#e3f2fd', color: '#1565c0' },
}

const PMF_STYLES = {
  'Watch':       { bg: '#fff8e1', color: '#f57f17', border: '#ffe082' },
  'Interesting': { bg: '#e8f5e9', color: '#2e7d32', border: '#a5d6a7' },
  'Pass':        { bg: '#fafafa', color: '#999',    border: '#e0e0e0' },
}

const SOURCE_STYLES = {
  'App Store':    { bg: '#e3f2fd', color: '#1565c0' },
  'Product Hunt': { bg: '#fff3e0', color: '#bf5000' },
  'Press':        { bg: '#f3e5f5', color: '#7b1fa2' },
  'Accelerator':  { bg: '#e8f5e9', color: '#2e7d32' },
  'Newsletter':   { bg: '#fce4ec', color: '#c2185b' },
}

function App() {
  const [activeTab, setActiveTab] = useState('Signals')

  return (
    <div className="app-shell">
      <nav className="top-nav">
        <div className="brand">Prism</div>
        <div className="tab-list">
          {TABS.map((tab) => (
            <button
              key={tab}
              className={`tab-btn${activeTab === tab ? ' active' : ''}`}
              onClick={() => setActiveTab(tab)}
              type="button"
            >
              {tab}
            </button>
          ))}
        </div>
      </nav>
      {activeTab === 'Precognition' && <SignalsTab />}
      {activeTab === 'Market'       && <MarketTab />}
      {activeTab === 'Trends'       && <TrendsTab />}
      {activeTab === 'Intel'        && <IntelTab />}
    </div>
  )
}

// ── Patterns data ─────────────────────────────────────────────────

const PATTERNS = [
  {
    id: 1,
    name: 'Ingredient Credentialing',
    category: 'Beauty',
    status: 'Established',
    thesis: 'Consumers are ingredient-literate. Brand identity built around a single credentialed compound outperforms benefit claims. The ingredient becomes the vocabulary — in any category where incumbents still hide their formula.',
    signals: [
      { label: 'Bakuchiol Serum', src: 'Shifts', detail: '+173%, 60.5K/mo — plant-based retinol rivals retinol on search volume. "Gentler retinol" converts harder than "reduces wrinkles".' },
      { label: 'Niacinamide Body Lotion', src: 'Shifts', detail: '+1,450% (5yr) — ingredient era migrating from face to body. Any body care brand without a niacinamide SKU is late.' },
      { label: 'Beet Gummies', src: 'Shifts', detail: '+956% — ingredient credentialing entering functional food. Beets = heart + performance. Low competition.' },
      { label: 'Mushroom Chocolate', src: 'Shifts', detail: '+171% — adaptogen credentialing in confectionery. Functional indulgence is not slowing.' },
    ],
    implication: 'Categories still running benefit language ("reduces stress", "boosts energy") haven\'t been flipped yet. The transition is: benefit claim → named compound → hero ingredient identity. Find the category, find the compound, build the brand around it. Pricing power follows credentialing.',
    watchFor: 'Peptides in haircare, ceramides in men\'s grooming, electrolytes-by-source in functional beverages, collagen by type in joint supplements',
  },
  {
    id: 2,
    name: 'Precision Health — Generic to Personal',
    category: 'Health & Fitness',
    status: 'Emerging',
    thesis: 'Health products are moving from one-size-fits-all to genuinely adaptive — whether the input is a biomarker device, a microbiome test, or behavioral data. The moat is the feedback loop: the product gets smarter the longer you use it.',
    signals: [
      { label: 'Temple (neurotech wearable)', src: 'Press', detail: '$54M F&F at $190M post — Deepinder Goyal. EEG-based cognitive performance. Biomarker → protocol loop.' },
      { label: 'Throne (gut health device)', src: 'Newsletter', detail: 'At-home gut health + urological + hydration monitoring. Closes the loop from measurement to action.' },
      { label: 'Tiny Health (infant microbiome)', src: 'Newsletter', detail: 'Microbiome test for infants. Parental precision anxiety meets early-life health intervention.' },
      { label: 'Zoe / Oura / Lumen', src: 'Newsletter', detail: 'Gut microbiome → AI nutrition (Zoe), sleep + recovery → readiness score (Oura), breath → metabolic protocol (Lumen). Same loop, different biomarker.' },
    ],
    implication: 'PMF test: does the recommendation meaningfully change after 90 days of use? If yes, the data moat is real — switching cost grows over time. If the output is the same on day 1 and day 90, there is no AI thesis, just marketing. Wedge is always one biomarker in one specific population (not "general wellness").',
    watchFor: 'Female hormone tracking with dosing recommendation, longevity biomarkers for 35-55 demographic, supplement stacking for specific populations (ADHD, perimenopausal, new fathers)',
  },
  {
    id: 3,
    name: 'Mental Health Mainstreaming',
    category: 'Health & Fitness',
    status: 'Established',
    thesis: 'Post-pandemic, emotional wellness is a permanent baseline purchase criterion — not a niche. Gen Z expects brands to be structural stakeholders in wellbeing. The signal is equity and ownership, not sponsorship.',
    signals: [
      { label: 'Happy × NAMI equity', src: 'Newsletter', detail: 'NAMI receives equity in Happy coffee — not a % of sales. Structural mission vs. cause marketing. Gen Z reads the difference.' },
      { label: '#Hearts2Hearts on TikTok', src: 'Shifts', detail: '49K posts — confessional self-love content driving community for wellness brands. Emotional content converts to community faster than product demos.' },
      { label: 'Destigmatization as baseline', src: 'Newsletter', detail: 'Therapy-coded language now mainstream Gen Z assumption. Not a differentiator — a floor. Brands without it read as out of touch.' },
    ],
    implication: 'Track structural mission alignment: does the brand give equity, board seats, or revenue share to the cause? Cause marketing (% of profits, PR partnerships) does not convert this cohort. Founders personally connected to the mental health issue outperform category entrants who adopt the language without the stake.',
    watchFor: 'Addiction recovery brands, ADHD consumer products, loneliness-coded social platforms with community economics, chronic illness support communities with commerce layer',
  },
  {
    id: 4,
    name: 'Convenience × Sustainability Resolution',
    category: 'Lifestyle',
    status: 'Emerging',
    thesis: 'Products that eliminate the convenience/sustainability tradeoff in one format unlock a premium consumer who refuses to choose. The format innovation is the moat — not the sustainability story.',
    signals: [
      { label: 'Disposable Period Underwear', src: 'Shifts', detail: '+562%, 9.9K/mo — convenience + sustainable materials in one format. Strong repeat purchase and expanding category.' },
      { label: 'Bamboo Baby Pajamas', src: 'Shifts', detail: '+617% — eco-parenting with premium pricing and loyal repeat. Parents as the highest-guilt, highest-LTV consumer cohort.' },
    ],
    implication: 'The consumer is not eco-anxious — they are convenience-maximizing with a preference for not feeling guilty. Lead with the convenience story. Sustainability is the permission structure, not the pitch. Winning categories share two traits: high repeat purchase rate and high guilt on the existing incumbent format.',
    watchFor: 'Single-use travel items in sustainable format, home cleaning refill systems at mass-market price point, sustainable packaging in pet food (guilt category)',
  },
  {
    id: 5,
    name: 'Community-Native Brands',
    category: 'Lifestyle',
    status: 'Forming',
    thesis: 'Brands built by and for specific underserved communities — not adapted for them — have a structural distribution advantage incumbents cannot buy. The community is the PMF validator and the first channel.',
    signals: [
      { label: 'Suki trending on X', src: 'Shifts', detail: 'Beauty brand gaining rapid organic traction — community-native discovery pattern: community before media.' },
      { label: '#iftar on TikTok', src: 'Shifts', detail: '118K posts — Ramadan as a mainstream consumer moment. F&B and beauty brands with genuine community stake convert; parachute brands don\'t.' },
      { label: 'Skin of color gap', src: 'Newsletter', detail: 'Personalization tools in skincare perform worst for darker skin tones. The underserved segment is the addressable market.' },
    ],
    implication: 'Incumbent brands cannot credibly enter community-native categories — authenticity is the product, not a feature. Discovery happens inside the community before press picks it up, which means these brands surface in Prism Signals before they appear in mainstream deal flow. Founder-market fit is non-negotiable: the founder has to be of the community, not a student of it.',
    watchFor: 'Haircare and skincare for textured hair and skin of color, wellness for South Asian diaspora, halal-certified functional food, West African beauty entering US market',
  },
]

const STATUS_STYLES = {
  'Established': { bg: '#e8f5e9', color: '#2e7d32' },
  'Forming':     { bg: '#fff3e0', color: '#bf5000' },
  'Emerging':    { bg: '#e3f2fd', color: '#1565c0' },
  'Watching':    { bg: '#f4f4f1', color: '#555' },
}

const SRC_STYLES = {
  'Shifts':      { bg: '#f3e5f5', color: '#7b1fa2' },
  'Signals':     { bg: '#e8f5e9', color: '#2e7d32' },
  'Press':       { bg: '#e3f2fd', color: '#1565c0' },
  'Newsletter':  { bg: '#fff3e0', color: '#bf5000' },
}

function PatternsTab() {
  const [selected, setSelected] = useState(null)
  const [catFilter, setCatFilter] = useState('All')
  const [statusFilter, setStatusFilter] = useState('All')

  const categories = ['All', ...Array.from(new Set(PATTERNS.map(p => p.category)))]
  const statuses   = ['All', 'Established', 'Forming', 'Emerging']

  const visible = useMemo(() => PATTERNS.filter(p =>
    (catFilter === 'All' || p.category === catFilter) &&
    (statusFilter === 'All' || p.status === statusFilter)
  ), [catFilter, statusFilter])

  const active = selected ? PATTERNS.find(p => p.id === selected) : null

  return (
    <div className="signals-wrap" style={{ display: 'flex', gap: 0, padding: 0, alignItems: 'stretch', height: 'calc(100vh - 48px)' }}>
      {/* Left panel */}
      <div style={{ width: 340, flexShrink: 0, borderRight: '1px solid #e8e8e5', overflowY: 'auto', padding: '20px 16px' }}>
        <div style={{ marginBottom: 16 }}>
          <h1 style={{ margin: '0 0 4px', fontSize: 16, fontWeight: 700 }}>Patterns</h1>
          <div style={{ fontSize: 11, color: '#888' }}>Consumer thesis clusters — recurring signals across categories</div>
        </div>

        {/* Filters */}
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 9, color: '#aaa', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 5 }}>Status</div>
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
            {statuses.map(s => {
              const ss = STATUS_STYLES[s] || {}
              const active = statusFilter === s
              return (
                <button key={s} onClick={() => setStatusFilter(s)} style={{
                  padding: '2px 8px', borderRadius: 20, fontSize: 10, fontWeight: 500, cursor: 'pointer',
                  border: active ? 'none' : '1px solid #e0e0dc',
                  background: active ? (ss.bg || '#1a1a1a') : '#fff',
                  color: active ? (ss.color || '#fff') : '#666',
                }}>{s}</button>
              )
            })}
          </div>
        </div>
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 9, color: '#aaa', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 5 }}>Category</div>
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
            {categories.map(c => {
              const cs = CATEGORY_STYLES[c] || {}
              const isActive = catFilter === c
              return (
                <button key={c} onClick={() => setCatFilter(c)} style={{
                  padding: '2px 8px', borderRadius: 20, fontSize: 10, fontWeight: 500, cursor: 'pointer',
                  border: isActive ? 'none' : '1px solid #e0e0dc',
                  background: isActive ? (cs.bg || '#1a1a1a') : '#fff',
                  color: isActive ? (cs.color || '#fff') : '#666',
                }}>{c}</button>
              )
            })}
          </div>
        </div>

        {/* Pattern list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {visible.map(p => {
            const ss = STATUS_STYLES[p.status] || {}
            const cs = CATEGORY_STYLES[p.category] || {}
            const isSelected = selected === p.id
            return (
              <div key={p.id} onClick={() => setSelected(isSelected ? null : p.id)} style={{
                background: isSelected ? '#fafaf8' : '#fff',
                border: isSelected ? '1.5px solid #1a1a1a' : '1px solid #e8e8e5',
                borderRadius: 10, padding: '11px 13px', cursor: 'pointer',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 5 }}>
                  <div style={{ fontWeight: 600, fontSize: 12, color: '#1a1a1a', lineHeight: 1.3, flex: 1 }}>{p.name}</div>
                  <span style={{ fontSize: 9, fontWeight: 600, padding: '2px 7px', borderRadius: 20, marginLeft: 6, flexShrink: 0, background: ss.bg, color: ss.color }}>{p.status}</span>
                </div>
                <div style={{ fontSize: 11, color: '#666', lineHeight: 1.5, marginBottom: 6 }}>{p.thesis}</div>
                <div style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
                  <span style={{ fontSize: 9, padding: '1px 7px', borderRadius: 20, background: cs.bg, color: cs.color, fontWeight: 600 }}>{p.category}</span>
                  <span style={{ fontSize: 10, color: '#aaa' }}>{p.signals.length} signals</span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Right panel — detail */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '28px 28px' }}>
        {!active ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#bbb', fontSize: 13 }}>
            Select a pattern to explore
          </div>
        ) : (
          <div style={{ maxWidth: 640 }}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
              <span style={{ fontSize: 10, padding: '3px 10px', borderRadius: 20, background: STATUS_STYLES[active.status]?.bg, color: STATUS_STYLES[active.status]?.color, fontWeight: 700 }}>{active.status}</span>
              <span style={{ fontSize: 10, padding: '3px 10px', borderRadius: 20, background: CATEGORY_STYLES[active.category]?.bg, color: CATEGORY_STYLES[active.category]?.color, fontWeight: 600 }}>{active.category}</span>
            </div>
            <h2 style={{ margin: '0 0 10px', fontSize: 18, fontWeight: 700, color: '#1a1a1a', lineHeight: 1.3 }}>{active.name}</h2>
            <p style={{ margin: '0 0 24px', fontSize: 13, color: '#444', lineHeight: 1.7 }}>{active.thesis}</p>

            {/* Signals */}
            <div style={{ marginBottom: 24 }}>
              <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#aaa', marginBottom: 10 }}>Supporting signals</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {active.signals.map((s, i) => {
                  const ss = SRC_STYLES[s.src] || SRC_STYLES['Newsletter']
                  return (
                    <div key={i} style={{ background: '#fafaf8', borderRadius: 8, padding: '10px 13px', border: '1px solid #e8e8e5' }}>
                      <div style={{ display: 'flex', gap: 7, alignItems: 'center', marginBottom: 4 }}>
                        <span style={{ fontWeight: 600, fontSize: 12, color: '#1a1a1a' }}>{s.label}</span>
                        <span style={{ fontSize: 9, padding: '1px 7px', borderRadius: 20, background: ss.bg, color: ss.color, fontWeight: 600 }}>{s.src}</span>
                      </div>
                      <div style={{ fontSize: 11, color: '#666', lineHeight: 1.5 }}>{s.detail}</div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Implication */}
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#aaa', marginBottom: 8 }}>Investment implication</div>
              <p style={{ margin: 0, fontSize: 12, color: '#333', lineHeight: 1.7, background: '#f8f8f6', borderRadius: 8, padding: '12px 14px', borderLeft: '3px solid #1a1a1a' }}>{active.implication}</p>
            </div>

            {/* Watch for */}
            <div>
              <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#aaa', marginBottom: 8 }}>Watch for next</div>
              <p style={{ margin: 0, fontSize: 12, color: '#666', lineHeight: 1.6, fontStyle: 'italic' }}>{active.watchFor}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function Placeholder({ title, subtitle }) {
  return (
    <section className="placeholder-tab">
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </section>
  )
}

const SCORE_COLOR = (score) => {
  if (score >= 70) return '#2e7d32'
  if (score >= 50) return '#f57f17'
  return '#1565c0'
}

const STAGE_LABEL = {
  'pre-raise': { bg: '#e8f5e9', color: '#2e7d32', label: 'Pre-raise' },
  'raising':   { bg: '#fff8e1', color: '#f57f17', label: 'Raising' },
  'seed':      { bg: '#e3f2fd', color: '#1565c0', label: 'Seed' },
  'series-a':  { bg: '#f3e5f5', color: '#7b1fa2', label: 'Series A' },
}

const ACC_STYLES = {
  'Chobani Incubator':  { bg: '#fff3e0', color: '#bf5000' },
  'SKS Accelerator':    { bg: '#e8f5e9', color: '#2e7d32' },
  'Techstars Consumer': { bg: '#e3f2fd', color: '#1565c0' },
  'Target Accelerator': { bg: '#fce4ec', color: '#c2185b' },
  'Expo West':          { bg: '#f3e5f5', color: '#7b1fa2' },
  'Product Hunt':       { bg: '#fff8e1', color: '#f57f17' },
}

function SignalsTab() {
  const [brands, setBrands]   = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch]   = useState('')
  const [catFilter, setCat]   = useState('All')

  useEffect(() => {
    supabase
      .from('consumer_founders')
      .select('*')
      .order('score', { ascending: false })
      .limit(60)
      .then(({ data }) => {
        if (data && data.length > 0) setBrands(data)
        setLoading(false)
      })
  }, [])

  const cats = ['All', ...new Set(brands.map(b => b.category).filter(Boolean))]

  const filtered = brands.filter(b => {
    const matchCat = catFilter === 'All' || b.category === catFilter
    const matchSearch = !search ||
      b.brand_name?.toLowerCase().includes(search.toLowerCase()) ||
      b.why_surfaced?.toLowerCase().includes(search.toLowerCase())
    return matchCat && matchSearch
  })

  const highSignal = brands.filter(b => b.score >= 60).length

  return (
    <div className="signals-wrap">
      <div className="signals-header">
        <div>
          <h1>Precognition</h1>
          <div className="shifts-week">Consumer brands before the raise</div>
        </div>
        <div className="header-right">
          <input className="search-input" type="text" placeholder="Search brands..."
            value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
      </div>

      {loading && <p className="empty-state">Loading…</p>}

      {!loading && brands.length === 0 && (
        <p className="empty-state">No brands yet — run the precognition scraper first.</p>
      )}

      {!loading && brands.length > 0 && (
        <>
          <div className="stats-row">
            <span className="stat-item"><strong>{brands.length}</strong> brands tracked</span>
            <span className="stat-sep">·</span>
            <span className="stat-item"><strong>{highSignal}</strong> high signal (60+)</span>
          </div>

          <div className="filter-row">
            {cats.map(c => (
              <button key={c} className={`filter-btn${catFilter === c ? ' active' : ''}`}
                onClick={() => setCat(c)} type="button">{c}</button>
            ))}
          </div>

          {filtered.length === 0 && <p className="empty-state">No brands match.</p>}

          <div className="product-grid">
            {filtered.map(brand => {
              const catStyle   = MARKET_CATEGORY_STYLES[brand.category] || { bg: '#f4f4f1', color: '#555' }
              const stageStyle = STAGE_LABEL[brand.stage] || { bg: '#f4f4f1', color: '#666', label: brand.stage }
              const accStyle   = ACC_STYLES[brand.accelerator] || { bg: '#f4f4f1', color: '#555' }
              const scoreColor = SCORE_COLOR(brand.score || 0)
              const signals    = (() => { try { return JSON.parse(brand.signals || '[]') } catch { return [] } })()

              return (
                <div key={brand.id} className="product-card">
                  <div className="card-top">
                    <div>
                      {brand.category && (
                        <span className="cat-badge" style={{ background: catStyle.bg, color: catStyle.color }}>
                          {brand.category}
                        </span>
                      )}
                      <h3 className="product-name">{brand.brand_name}</h3>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
                      <span style={{ fontSize: 18, fontWeight: 700, color: scoreColor }}>{brand.score}</span>
                      <span style={{ fontSize: 10, color: '#aaa' }}>score</span>
                    </div>
                  </div>

                  {brand.accelerator && (
                    <span className="cat-badge" style={{ background: accStyle.bg, color: accStyle.color, marginBottom: 8, display: 'inline-block' }}>
                      {brand.accelerator}
                    </span>
                  )}

                  {brand.why_surfaced && (
                    <p className="differentiation" style={{ fontSize: 12, color: '#555' }}>
                      {brand.why_surfaced}
                    </p>
                  )}

                  {signals.length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      {signals.map((sig, i) => (
                        <div key={i} style={{ fontSize: 11, color: '#888', marginBottom: 3 }}>
                          <strong style={{ color: '#555' }}>{sig.label}</strong> — {sig.detail}
                        </div>
                      ))}
                    </div>
                  )}

                  <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ flex: 1, height: 3, background: '#f0f0ee', borderRadius: 2 }}>
                      <div style={{ width: `${brand.score}%`, height: '100%', background: scoreColor, borderRadius: 2 }} />
                    </div>
                    {brand.stage && (
                      <span className="cat-badge" style={{ background: stageStyle.bg, color: stageStyle.color, fontSize: 10 }}>
                        {stageStyle.label}
                      </span>
                    )}
                  </div>

                  {brand.source_url && (
                    <a href={brand.source_url} target="_blank" rel="noopener noreferrer"
                       style={{ fontSize: 11, color: '#888', textDecoration: 'none', display: 'block', marginTop: 8 }}>
                      ↗ {brand.source}
                    </a>
                  )}
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}

function ProductCard({ product, onSetFlag }) {
  const catStyle = CATEGORY_STYLES[product.category] || { bg: '#f4f4f1', color: '#555' }
  const pmfStyle = product.pmf_flag ? PMF_STYLES[product.pmf_flag] : null

  return (
    <div className="product-card">
      <div className="card-top">
        <div>
          <span
            className="cat-badge"
            style={{ background: catStyle.bg, color: catStyle.color }}
          >
            {product.category}
          </span>
          <h3 className="product-name">{product.name}</h3>
        </div>
        {pmfStyle && (
          <span
            className="pmf-badge"
            style={{ background: pmfStyle.bg, color: pmfStyle.color, borderColor: pmfStyle.border }}
          >
            {product.pmf_flag}
          </span>
        )}
      </div>

      <p className="differentiation">{product.differentiation}</p>

      <div className="source-tags">
        {product.sources.map((src) => {
          const s = SOURCE_STYLES[src] || { bg: '#f4f4f1', color: '#555' }
          return (
            <span key={src} className="source-tag" style={{ background: s.bg, color: s.color }}>
              {src}
            </span>
          )
        })}
      </div>

      <div className="card-meta">
        <span className="meta-source">{product.source_detail}</span>
        <span className="meta-date">{formatDate(product.date_spotted)}</span>
      </div>

      <div className="pmf-row">
        <span className="pmf-label">PMF call</span>
        <div className="pmf-flags">
          {['Watch', 'Interesting', 'Pass'].map((flag) => {
            const s = PMF_STYLES[flag]
            const active = product.pmf_flag === flag
            return (
              <button
                key={flag}
                className={`pmf-btn${active ? ' active' : ''}`}
                style={active ? { background: s.bg, color: s.color, borderColor: s.border } : {}}
                onClick={() => onSetFlag(product.id, flag)}
                type="button"
              >
                {flag}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ── Shifts data ────────────────────────────────────────────────────

const SHIFTS_DATA = {
  week: 'March 2, 2026',
  social_pulse: [
    {
      id: 1,
      platform: 'X',
      name: 'Smoothie King',
      type: 'Brand',
      signal: 'Trending #7 organically — rare for a QSR wellness brand. Signals viral campaign or cultural moment. Functional drink category heating up in Q1.',
      category: 'Food & Drink',
    },
    {
      id: 2,
      platform: 'X',
      name: 'Suki',
      type: 'Beauty',
      signal: 'Trending 18hrs — beauty brand or influencer gaining rapid traction organically. Category signal worth watching.',
      category: 'Beauty',
    },
    {
      id: 3,
      platform: 'TikTok',
      name: '#iftar',
      type: 'Food',
      signal: '118K posts. Ramadan food content mainstream, not niche. F&B, hospitality, and beauty (evening self-care) have a clear window to show up authentically.',
      category: 'Food & Drink',
    },
    {
      id: 4,
      platform: 'TikTok',
      name: '#Tan',
      type: 'Beauty',
      signal: '37K posts, jumped 8 spots. Sunless tanning surging from spring body content. Self-tanning drop-routine format converting. Beauty brands with tanning SKUs should push creator partnerships now.',
      category: 'Beauty',
    },
  ],
  rising_trends: [
    {
      id: 1,
      name: 'Niacinamide Body Lotion',
      category: 'Beauty',
      growth: '+1,450% (5yr)',
      volume: '5.4K/mo',
      type: 'Ingredient shift',
      insight: 'Skincare\'s ingredient era has migrated from face to body. Olay, CeraVe, The INKEY List are already there. Any body care brand without a niacinamide SKU is leaving shelf space on the table.',
    },
    {
      id: 2,
      name: 'Bakuchiol Serum',
      category: 'Beauty',
      growth: '+173%',
      volume: '60.5K/mo',
      type: 'Ingredient shift',
      insight: 'Plant-based retinol now rivals retinol in search volume. Still indie enough to build brand identity around. The "gentler retinol" story converts hard — sensitivity-first skincare is a durable positioning.',
    },
    {
      id: 3,
      name: 'Beet Gummies',
      category: 'Health & Fitness',
      growth: '+956%',
      volume: '5.4K/mo',
      type: 'Ingredient shift',
      insight: 'Exploding under the radar. Beets = heart health + natural sports performance. Crossroads of functional food and supplements. Low competition, launchable for any brand in women\'s wellness or sports recovery.',
    },
    {
      id: 4,
      name: 'Barrel Fit Jeans',
      category: 'Fashion',
      growth: '+99x',
      volume: null,
      type: 'Silhouette shift',
      insight: 'The anti-skinny-jean moment is here. Wide thigh, tapered ankle. The silhouette of 2026 — brands not creating content around barrel denim are dressing last season\'s customer.',
    },
    {
      id: 5,
      name: 'Disposable Period Underwear',
      category: 'Health & Fitness',
      growth: '+562%',
      volume: '9.9K/mo',
      type: 'New category',
      insight: 'Convenience + sustainability in one format. A new category forming in real time. Strong DTC story with repeat purchase mechanics built in.',
    },
    {
      id: 6,
      name: 'Mushroom Chocolate',
      category: 'Food & Drink',
      growth: '+171%',
      volume: null,
      type: 'Ingredient shift',
      insight: 'Functional indulgence is not slowing down. Adaptogens meeting confectionery — the consumer wants health benefits without sacrifice.',
    },
  ],
}

const SHIFT_TYPE_STYLES = {
  'Ingredient shift': { bg: '#e8f5e9', color: '#2e7d32' },
  'Silhouette shift': { bg: '#f3e5f5', color: '#7b1fa2' },
  'New category':     { bg: '#e3f2fd', color: '#1565c0' },
  'Food':             { bg: '#fff3e0', color: '#bf5000' },
  'Beauty':           { bg: '#fce4ec', color: '#c2185b' },
  'Brand':            { bg: '#e8eaf6', color: '#3949ab' },
}

const PLATFORM_STYLES = {
  'X':       { bg: '#1a1a1a', color: '#fff' },
  'TikTok':  { bg: '#010101', color: '#ff0050' },
}

function ShiftsTab() {
  const [section, setSection] = useState('Trends')

  return (
    <div className="signals-wrap">
      <div className="signals-header">
        <div>
          <h1>Shifts</h1>
          <div className="shifts-week">Week of {SHIFTS_DATA.week}</div>
        </div>
        <div className="view-toggle">
          {['Trends', 'Social Pulse'].map(s => (
            <button
              key={s}
              className={`filter-btn${section === s ? ' active' : ''}`}
              onClick={() => setSection(s)}
              type="button"
            >{s}</button>
          ))}
        </div>
      </div>

      {section === 'Trends' && (
        <>
          <div className="stats-row">
            <span className="stat-item"><strong>{SHIFTS_DATA.rising_trends.length}</strong> rising trends</span>
            <span className="stat-sep">·</span>
            <span className="stat-item"><strong>{SHIFTS_DATA.rising_trends.filter(t => t.type === 'Ingredient shift').length}</strong> ingredient shifts</span>
            <span className="stat-sep">·</span>
            <span className="stat-item"><strong>{SHIFTS_DATA.rising_trends.filter(t => t.type === 'New category').length}</strong> new categories</span>
          </div>
          <div className="product-grid">
            {SHIFTS_DATA.rising_trends.map(trend => {
              const catStyle = CATEGORY_STYLES[trend.category] || { bg: '#f4f4f1', color: '#555' }
              const typeStyle = SHIFT_TYPE_STYLES[trend.type] || { bg: '#f4f4f1', color: '#555' }
              return (
                <div key={trend.id} className="product-card">
                  <div className="card-top">
                    <div>
                      <span className="cat-badge" style={{ background: catStyle.bg, color: catStyle.color }}>{trend.category}</span>
                      <h3 className="product-name">{trend.name}</h3>
                    </div>
                    <span className="cat-badge" style={{ background: typeStyle.bg, color: typeStyle.color, flexShrink: 0 }}>{trend.type}</span>
                  </div>
                  <div className="shifts-metrics">
                    {trend.growth && <span className="metric-pill metric-growth">{trend.growth}</span>}
                    {trend.volume && <span className="metric-pill metric-volume">{trend.volume} searches/mo</span>}
                  </div>
                  <p className="differentiation">{trend.insight}</p>
                </div>
              )
            })}
          </div>
        </>
      )}

      {section === 'Social Pulse' && (
        <>
          <div className="stats-row">
            <span className="stat-item"><strong>{SHIFTS_DATA.social_pulse.length}</strong> signals this week</span>
          </div>
          <div className="product-grid">
            {SHIFTS_DATA.social_pulse.map(item => {
              const catStyle = CATEGORY_STYLES[item.category] || { bg: '#f4f4f1', color: '#555' }
              const platStyle = PLATFORM_STYLES[item.platform] || { bg: '#f4f4f1', color: '#555' }
              return (
                <div key={item.id} className="product-card">
                  <div className="card-top">
                    <div>
                      <span className="cat-badge" style={{ background: platStyle.bg, color: platStyle.color }}>{item.platform}</span>
                      <h3 className="product-name">{item.name}</h3>
                    </div>
                    <span className="cat-badge" style={{ background: catStyle.bg, color: catStyle.color, flexShrink: 0 }}>{item.category}</span>
                  </div>
                  <p className="differentiation">{item.signal}</p>
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = dateStr.includes('T') ? new Date(dateStr) : new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

// ── Trends tab ────────────────────────────────────────────────

const TREND_SOURCE_STYLES = {
  'google_trends': { bg: '#e3f2fd', color: '#1565c0', label: 'Google Trends' },
  'tiktok':        { bg: '#1a1a1a', color: '#fff',    label: 'TikTok' },
  'manual':        { bg: '#f4f4f1', color: '#666',    label: 'Manual' },
}

const STAGE_STYLES = {
  'emerging':      { bg: '#e8f5e9', color: '#2e7d32' },
  'accelerating':  { bg: '#fff8e1', color: '#f57f17' },
  'peaking':       { bg: '#fce4ec', color: '#c2185b' },
  'mainstream':    { bg: '#f4f4f1', color: '#999'    },
}

function TrendsTab() {
  const [trends, setTrends]   = useState([])
  const [loading, setLoading] = useState(true)
  const [source, setSource]   = useState('All')
  const [cat, setCat]         = useState('All')

  useEffect(() => {
    supabase
      .from('trend_shifts')
      .select('*')
      .order('momentum', { ascending: false })
      .limit(100)
      .then(({ data, error }) => {
        if (data && data.length > 0) setTrends(data)
        setLoading(false)
      })
  }, [])

  const sources    = ['All', 'TikTok', 'Google Trends']
  const categories = ['All', ...new Set(trends.map(t => t.category).filter(Boolean))]

  const filtered = trends.filter(t => {
    const matchSrc = source === 'All' || (TREND_SOURCE_STYLES[t.source]?.label === source)
    const matchCat = cat === 'All' || t.category === cat
    return matchSrc && matchCat
  })

  const emerging     = filtered.filter(t => t.stage === 'emerging').length
  const accelerating = filtered.filter(t => t.stage === 'accelerating').length

  return (
    <div className="signals-wrap">
      <div className="signals-header">
        <div>
          <h1>Trends</h1>
          <div className="shifts-week">Consumer shifts · Ingredient moves · New usage paradigms</div>
        </div>
      </div>

      {loading && <p className="empty-state">Loading…</p>}

      {!loading && trends.length === 0 && (
        <p className="empty-state">No trend data yet — scraper runs hourly.</p>
      )}

      {!loading && trends.length > 0 && (
        <>
          <div className="stats-row">
            <span className="stat-item"><strong>{emerging}</strong> emerging</span>
            <span className="stat-sep">·</span>
            <span className="stat-item"><strong>{accelerating}</strong> accelerating</span>
            <span className="stat-sep">·</span>
            <span className="stat-item"><strong>{filtered.length}</strong> total signals</span>
          </div>

          <div className="filter-row">
            {sources.map(s => (
              <button key={s} className={`filter-btn${source === s ? ' active' : ''}`}
                onClick={() => setSource(s)} type="button">{s}</button>
            ))}
            <span style={{ margin: '0 8px', color: '#ddd' }}>|</span>
            {categories.map(c => (
              <button key={c} className={`filter-btn${cat === c ? ' active' : ''}`}
                onClick={() => setCat(c)} type="button">{c}</button>
            ))}
          </div>

          <div className="product-grid">
            {filtered.map(trend => {
              const srcStyle   = TREND_SOURCE_STYLES[trend.source] || { bg: '#f4f4f1', color: '#555', label: trend.source }
              const stageStyle = STAGE_STYLES[trend.stage] || { bg: '#f4f4f1', color: '#666' }
              const catStyle   = MARKET_CATEGORY_STYLES[trend.category] || { bg: '#f4f4f1', color: '#555' }
              return (
                <div key={trend.id} className="product-card">
                  <div className="card-top">
                    <div>
                      <span className="cat-badge" style={{ background: srcStyle.bg, color: srcStyle.color }}>
                        {srcStyle.label}
                      </span>
                      <h3 className="product-name">{trend.trend_name}</h3>
                    </div>
                    <span className="pmf-badge" style={{ background: stageStyle.bg, color: stageStyle.color, borderColor: stageStyle.bg }}>
                      {trend.stage}
                    </span>
                  </div>

                  {trend.category && (
                    <span className="cat-badge" style={{ background: catStyle.bg, color: catStyle.color, marginBottom: 8, display: 'inline-block' }}>
                      {trend.category}
                    </span>
                  )}

                  {trend.signal && (
                    <p className="differentiation" style={{ marginTop: 8 }}>{trend.signal}</p>
                  )}

                  <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ flex: 1, height: 4, background: '#f0f0ee', borderRadius: 2 }}>
                      <div style={{ width: `${trend.momentum}%`, height: '100%', background: '#1a1a1a', borderRadius: 2 }} />
                    </div>
                    <span style={{ fontSize: 11, color: '#aaa', minWidth: 32 }}>{trend.momentum}</span>
                  </div>

                  {trend.source_url && (
                    <a href={trend.source_url} target="_blank" rel="noopener noreferrer"
                       style={{ fontSize: 11, color: '#888', textDecoration: 'none', display: 'block', marginTop: 8 }}>
                      ↗ {trend.source === 'tiktok' ? 'TikTok' : 'Google Trends'}
                    </a>
                  )}
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}

// ── Intel tab ─────────────────────────────────────────────────

function IntelTab() {
  const [intel, setIntel]     = useState([])
  const [loading, setLoading] = useState(true)
  const [tier, setTier]       = useState('All')

  useEffect(() => {
    supabase
      .from('brand_signals')
      .select('*')
      .eq('category', 'market_intel')
      .order('detected_at', { ascending: false })
      .limit(60)
      .then(({ data }) => {
        if (data) setIntel(data)
        setLoading(false)
      })
  }, [])

  const tiers    = ['All', 'Tier 1', 'Tier 2', 'Tier 3']
  const filtered = tier === 'All' ? intel : intel.filter(i => i.stage === tier)

  return (
    <div className="signals-wrap">
      <div className="signals-header">
        <div>
          <h1>Intel</h1>
          <div className="shifts-week">Substack signals · Consumer VC · Operator perspectives</div>
        </div>
      </div>

      {loading && <p className="empty-state">Loading…</p>}

      {!loading && (
        <>
          <div className="stats-row">
            <span className="stat-item"><strong>{intel.filter(i => i.stage === 'Tier 1').length}</strong> Tier 1</span>
            <span className="stat-sep">·</span>
            <span className="stat-item"><strong>{intel.length}</strong> total signals</span>
          </div>

          <div className="filter-row">
            {tiers.map(t => (
              <button key={t} className={`filter-btn${tier === t ? ' active' : ''}`}
                onClick={() => setTier(t)} type="button">{t}</button>
            ))}
          </div>

          {filtered.length === 0 && <p className="empty-state">No intel yet — scraper runs hourly.</p>}

          <div className="product-grid">
            {filtered.map(item => {
              const tierStyle = TIER_STYLES[item.stage] || { bg: '#f4f4f1', color: '#666' }
              return (
                <div key={item.id} className="product-card">
                  <div className="card-top">
                    <span className="cat-badge" style={{ background: tierStyle.bg, color: tierStyle.color }}>
                      {item.stage || 'Tier 2'}
                    </span>
                  </div>
                  <h3 className="product-name" style={{ fontSize: 13, marginTop: 6 }}>{item.brand_name}</h3>
                  {item.sub_category && (
                    <div style={{ fontSize: 10, color: '#aaa', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      {item.sub_category}
                    </div>
                  )}
                  {item.what && (
                    <p className="differentiation" style={{ fontSize: 12 }}>{item.what.slice(0, 300)}</p>
                  )}
                  <div className="card-meta">
                    <span className="meta-source">{item.founder}</span>
                    <span className="meta-date">{formatDate(item.detected_at)}</span>
                  </div>
                  {item.source_url && (
                    <a href={item.source_url} target="_blank" rel="noopener noreferrer"
                       style={{ fontSize: 11, color: '#888', textDecoration: 'none', display: 'block', marginTop: 8 }}>
                      ↗ Read
                    </a>
                  )}
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}

// ── Market tab ─────────────────────────────────────────────────

const MARKET_CATEGORY_STYLES = {
  'beauty':           { bg: '#fce4ec', color: '#c2185b' },
  'consumer':         { bg: '#e8eaf6', color: '#3949ab' },
  'food & beverage':  { bg: '#fff3e0', color: '#bf5000' },
  'wellness':         { bg: '#e8f5e9', color: '#2e7d32' },
  'longevity':        { bg: '#e0f7fa', color: '#00695c' },
  'femtech':          { bg: '#fce4ec', color: '#880e4f' },
  'sustainability':   { bg: '#e0f2f1', color: '#004d40' },
  'fashion':          { bg: '#f3e5f5', color: '#7b1fa2' },
  'fitness':          { bg: '#e8f5e9', color: '#1b5e20' },
  'market_intel':     { bg: '#e3f2fd', color: '#1565c0' },
}

const TIER_STYLES = {
  'Tier 1': { bg: '#1a1a1a', color: '#fff' },
  'Tier 2': { bg: '#e8eaf6', color: '#3949ab' },
  'Tier 3': { bg: '#f4f4f1', color: '#666' },
}

function MarketTab() {
  const [section, setSection] = useState('Fund Theses')
  const [funds, setFunds] = useState([])
  const [intel, setIntel] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      supabase
        .from('fund_raises')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(30),
      supabase
        .from('brand_signals')
        .select('*')
        .eq('category', 'market_intel')
        .order('detected_at', { ascending: false })
        .limit(30),
    ]).then(([fundsRes, intelRes]) => {
      if (fundsRes.data) setFunds(fundsRes.data)
      if (intelRes.data) setIntel(intelRes.data)
      setLoading(false)
    })
  }, [])

  return (
    <div className="signals-wrap">
      <div className="signals-header">
        <div>
          <h1>Market</h1>
          <div className="shifts-week">Consumer deal flow · Fund theses · VC intel</div>
        </div>
        <div className="view-toggle">
          {['Fund Theses', 'VC Intel'].map(s => (
            <button
              key={s}
              className={`filter-btn${section === s ? ' active' : ''}`}
              onClick={() => setSection(s)}
              type="button"
            >{s}</button>
          ))}
        </div>
      </div>

      {loading && <p className="empty-state">Loading…</p>}

      {!loading && section === 'Fund Theses' && (
        <>
          <div className="stats-row">
            <span className="stat-item"><strong>{funds.length}</strong> fund signals tracked</span>
          </div>
          {funds.length === 0 && <p className="empty-state">No fund signals yet — scraper runs hourly.</p>}
          <div className="product-grid">
            {funds.map(f => {
              const cats = f.categories || ['consumer']
              const primaryCat = cats[0] || 'consumer'
              const catStyle = MARKET_CATEGORY_STYLES[primaryCat] || { bg: '#f4f4f1', color: '#555' }
              return (
                <div key={f.id} className="product-card">
                  <div className="card-top">
                    <div>
                      <span className="cat-badge" style={{ background: catStyle.bg, color: catStyle.color }}>
                        {primaryCat}
                      </span>
                      <h3 className="product-name" style={{ fontSize: 13 }}>{f.fund_name}</h3>
                    </div>
                    {f.fund_size_m && (
                      <span className="pmf-badge" style={{ background: '#e8f5e9', color: '#2e7d32', borderColor: '#a5d6a7' }}>
                        ${f.fund_size_m}M
                      </span>
                    )}
                  </div>
                  {f.thesis && <p className="differentiation">{f.thesis.slice(0, 280)}</p>}
                  <div className="card-meta">
                    <span className="meta-source">{f.source}</span>
                    <span className="meta-date">{formatDate(f.announced_date || f.created_at)}</span>
                  </div>
                  {f.source_url && (
                    <a href={f.source_url} target="_blank" rel="noopener noreferrer"
                       style={{ fontSize: 11, color: '#888', textDecoration: 'none', display: 'block', marginTop: 8 }}>
                      ↗ {new URL(f.source_url).hostname.replace('www.','')}
                    </a>
                  )}
                </div>
              )
            })}
          </div>
        </>
      )}

      {!loading && section === 'VC Intel' && (
        <>
          <div className="stats-row">
            <span className="stat-item"><strong>{intel.length}</strong> newsletter signals</span>
            <span className="stat-sep">·</span>
            <span className="stat-item"><strong>{intel.filter(i => i.stage === 'Tier 1').length}</strong> Tier 1</span>
          </div>
          {intel.length === 0 && <p className="empty-state">No intel yet — scraper runs hourly.</p>}
          <div className="product-grid">
            {intel.map(item => {
              const tierStyle = TIER_STYLES[item.stage] || { bg: '#f4f4f1', color: '#666' }
              return (
                <div key={item.id} className="product-card">
                  <div className="card-top">
                    <div>
                      <span className="cat-badge" style={{ background: tierStyle.bg, color: tierStyle.color }}>
                        {item.stage || 'Tier 2'}
                      </span>
                      <h3 className="product-name" style={{ fontSize: 13 }}>{item.brand_name}</h3>
                    </div>
                  </div>
                  {item.sub_category && (
                    <div style={{ fontSize: 10, color: '#aaa', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      {item.sub_category}
                    </div>
                  )}
                  {item.what && <p className="differentiation" style={{ fontSize: 12 }}>{item.what.slice(0, 300)}</p>}
                  <div className="card-meta">
                    <span className="meta-source">{item.founder}</span>
                    <span className="meta-date">{formatDate(item.detected_at)}</span>
                  </div>
                  {item.source_url && (
                    <a href={item.source_url} target="_blank" rel="noopener noreferrer"
                       style={{ fontSize: 11, color: '#888', textDecoration: 'none', display: 'block', marginTop: 8 }}>
                      ↗ Read
                    </a>
                  )}
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}

export default App
