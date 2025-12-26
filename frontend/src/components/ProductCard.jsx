import { useState } from 'react'

function getUnitLabel(product) {
  const v = (product.volume || '').toLowerCase()

  // Heel simpel: drankjes -> liter, gewicht -> kg, rest voorlopig geen label
  if (v.includes('l')) {
    return 'per liter'
  }
  if (v.includes('kg') || v.includes('g')) {
    // Later kun je backend aanpassen naar echte prijs per 100g
    return 'per kg'
  }
  return null
}

function getUnitDescription(product) {
  // Check if this is a multi-pack
  if (product.unit_count && product.unit_count > 1) {
    if (product.unit_type === 'ML') {
      return 'per blik'
    } else if (product.unit_type === 'CL') {
      return 'per fles'
    } else if (product.unit_type === 'L') {
      return 'per stuk'
    }
    return 'per stuk'
  }
  return null
}

export default function ProductCard({ product }) {
  const [imageError, setImageError] = useState(false)
  const [logoError, setLogoError] = useState(false)

  const hasValidImage =
    product.image &&
    typeof product.image === 'string' &&
    product.image.startsWith('http')

  const unitLabel = getUnitLabel(product)
  const unitDescription = getUnitDescription(product)
  const showUnitPrice = product.unit_count && product.unit_count > 1

  return (
    <a
      href={product.link}
      target="_blank"
      rel="noreferrer"
      className="group bg-slate-800 border border-slate-700 rounded-2xl p-4 flex flex-col relative hover:border-blue-500/50 hover:shadow-2xl hover:shadow-blue-900/20 transition duration-300 overflow-hidden"
    >
      {/* Logo rechtsboven, met fallback als er geen logo-url is */}
      <div className="absolute top-4 right-4 z-10 bg-white/90 p-1 rounded-md shadow-sm min-w-[2.5rem] flex items-center justify-center">
        {product.logo && !logoError ? (
          <img 
            src={product.logo} 
            alt={product.store} 
            className="h-6 object-contain"
            onError={() => setLogoError(true)}
          />
        ) : (
          <span className="text-[0.6rem] font-semibold text-slate-800 uppercase">
            {product.store}
          </span>
        )}
      </div>

      {/* Productafbeelding met fallback voor kapotte URLs */}
      <div className="h-48 w-full bg-white rounded-xl flex items-center justify-center mb-4 p-4 group-hover:scale-105 transition duration-500">
        {hasValidImage && !imageError ? (
          <img
            src={product.image}
            alt={product.name}
            className="max-h-full max-w-full object-contain"
            onError={() => setImageError(true)}
          />
        ) : (
          <div className="text-gray-400 text-4xl">🥤</div>
        )}
      </div>

      <div className="flex-1 flex flex-col">
        <h3 className="font-bold text-gray-100 mb-1 leading-snug line-clamp-2 min-h-[3rem]">
          {product.name}
        </h3>

        <div className="flex items-center gap-2 mb-4">
          <span className="px-2 py-1 bg-slate-700 rounded text-xs text-slate-300 font-mono uppercase">
            {product.volume || '—'}
          </span>
        </div>

        <div className="mt-auto border-t border-slate-700 pt-4">
          {/* Main price - total price for the pack */}
          <div className="flex justify-between items-start mb-3">
            <div>
              <div className="text-2xl font-bold text-white">
                €{product.price.toFixed(2)}
              </div>
              <div className="text-xs text-slate-400">
                {product.unit_count > 1 ? `Totaal (${product.unit_count} stuks)` : 'Prijs per stuk'}
              </div>
            </div>

            {/* Price per liter/kg */}
            <div className="text-right">
              {product.price_per_liter > 0 && unitLabel ? (
                <>
                  <div className="text-lg font-bold text-emerald-400">
                    €{product.price_per_liter.toFixed(2)}
                  </div>
                  <div className="text-xs text-emerald-600/70 font-medium">
                    {unitLabel}
                  </div>
                </>
              ) : (
                <div className="text-slate-600 text-sm">N/A</div>
              )}
            </div>
          </div>

          {/* Price per unit (can/bottle) for multi-packs */}
          {showUnitPrice && (
            <div className="flex justify-between items-center pt-3 border-t border-slate-700/50">
              <div className="text-xs text-slate-400">
                {unitDescription || 'per stuk'}
              </div>
              <div className="text-base font-semibold text-blue-400">
                €{product.price_per_unit.toFixed(2)}
              </div>
            </div>
          )}
        </div>
      </div>
    </a>
  )
}
