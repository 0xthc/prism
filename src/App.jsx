import { useState, useMemo } from 'react'

const TABS = ['Signals', 'Shifts', 'Market', 'Notes']

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
      {activeTab === 'Signals' && <SignalsTab />}
      {activeTab === 'Shifts'  && <ShiftsTab />}
      {activeTab === 'Market'  && <Placeholder title="Market"  subtitle="Consumer deal flow, category heat maps, funding pulse." />}
      {activeTab === 'Notes'   && <Placeholder title="Notes"   subtitle="Your field observations and consumer market notes." />}
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

function SignalsTab() {
  const [products, setProducts] = useState(MOCK_PRODUCTS)
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('All')

  const filtered = useMemo(() => {
    return products.filter((p) => {
      const matchCat = categoryFilter === 'All' || p.category === categoryFilter
      const matchSearch =
        !search ||
        p.name.toLowerCase().includes(search.toLowerCase()) ||
        p.differentiation.toLowerCase().includes(search.toLowerCase())
      return matchCat && matchSearch
    })
  }, [products, search, categoryFilter])

  const flagged = products.filter((p) => p.pmf_flag && p.pmf_flag !== 'Pass').length

  function setFlag(id, flag) {
    setProducts((prev) =>
      prev.map((p) => (p.id === id ? { ...p, pmf_flag: p.pmf_flag === flag ? '' : flag } : p))
    )
  }

  return (
    <div className="signals-wrap">
      <div className="signals-header">
        <h1>Signals</h1>
        <div className="header-right">
          <input
            className="search-input"
            type="text"
            placeholder="Search products..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="stats-row">
        <span className="stat-item">
          <strong>{products.length}</strong> products tracked
        </span>
        <span className="stat-sep">·</span>
        <span className="stat-item">
          <strong>{flagged}</strong> flagged
        </span>
      </div>

      <div className="filter-row">
        {['All', ...CATEGORIES].map((cat) => (
          <button
            key={cat}
            className={`filter-btn${categoryFilter === cat ? ' active' : ''}`}
            onClick={() => setCategoryFilter(cat)}
            type="button"
          >
            {cat}
          </button>
        ))}
      </div>

      {filtered.length === 0 && (
        <p className="empty-state">No products match.</p>
      )}

      <div className="product-grid">
        {filtered.map((product) => (
          <ProductCard key={product.id} product={product} onSetFlag={setFlag} />
        ))}
      </div>
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
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export default App
