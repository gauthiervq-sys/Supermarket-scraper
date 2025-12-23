import { useState } from 'react'
import ProductCard from './components/ProductCard'
import './index.css'

function App() {
  const [query, setQuery] = useState('')
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(false)
  const [selectedSize, setSelectedSize] = useState('all')
  const [availableSizes, setAvailableSizes] = useState([])

  const search = async () => {
    if (!query) return
    setLoading(true)
    setProducts([])

    try {
      const protocol = window.location.protocol
      const hostname = window.location.hostname

      // Backend via host-poort 8100
      const res = await fetch(
        `${protocol}//${hostname}:8100/search?q=${encodeURIComponent(query)}`
      )

      if (!res.ok) {
        throw new Error(`Backend error: ${res.status}`)
      }

      const data = await res.json()
      setProducts(data)

      const sizes = new Set()
      data.forEach(p => {
        if (p.liter_value > 0) sizes.add(p.volume)
      })
      setAvailableSizes(Array.from(sizes).sort())
    } catch (e) {
      console.error(e)
      alert('Error: Kan geen verbinding maken met backend.')
    }

    setLoading(false)
  }

  const filteredProducts = products.filter(p => {
    if (selectedSize === 'all') return true
    return p.volume === selectedSize
  })

  return (
    <div className="min-h-screen bg-slate-900 text-gray-100 p-4 md:p-8 font-sans">
      <div className="max-w-7xl mx-auto">
        {/* Header / zoekbalk */}
        <div className="bg-slate-800/50 backdrop-blur-md border border-slate-700 p-6 rounded-2xl shadow-2xl mb-8 sticky top-4 z-50">
          <h1 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500 mb-6 tracking-tight">
            BE Supermarkt Scanner Ultimate
          </h1>

          <div className="flex gap-4 flex-col md:flex-row">
            <input
              type="text"
              className="flex-1 p-4 bg-slate-950 border border-slate-700 rounded-xl text-lg text-white placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:outline-none transition"
              placeholder="Zoek product (bv. cola zero, jupiler)..."
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && search()}
            />
            <button
              onClick={search}
              disabled={loading}
              className="bg-blue-600 text-white px-8 py-4 rounded-xl font-bold hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 transition shadow-lg shadow-blue-900/20"
            >
              {loading ? 'Bezig...' : 'Zoeken 🔎'}
            </button>
          </div>

          {products.length > 0 && (
            <div className="mt-6 flex gap-2 flex-wrap">
              <button
                onClick={() => setSelectedSize('all')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  selectedSize === 'all'
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/50'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                Alles
              </button>
              {availableSizes.map(size => (
                <button
                  key={size}
                  onClick={() => setSelectedSize(size)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition uppercase ${
                    selectedSize === size
                      ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/50'
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                  }`}
                >
                  {size}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Loading state */}
        {loading && (
          <div className="text-center py-20 animate-pulse">
            <div className="text-6xl mb-4">🛒</div>
            <p className="text-slate-400 text-xl font-light">
              10 Winkels bezoeken... (dit kan even duren!)
            </p>
          </div>
        )}

        {/* Resultaten grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredProducts.map((p, i) => (
            <ProductCard key={i} product={p} />
          ))}
        </div>
      </div>
    </div>
  )
}

export default App
