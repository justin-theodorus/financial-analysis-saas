// lib/marketstack.ts

export interface Stock {
    symbol: string
    name: string
    price: number
    change: number
    changePercent: number
  }
  
  const API_KEY = process.env.NEXT_PUBLIC_MARKETSTACK_API_KEY || 'YOUR_API_KEY'
  const BASE_URL = 'https://api.marketstack.com/v1'
  
  // Company names for display
  export const STOCK_SYMBOLS = {
    technology: [
      { symbol: "AAPL", name: "Apple Inc." },
      { symbol: "MSFT", name: "Microsoft Corp." },
      { symbol: "GOOGL", name: "Alphabet Inc." },
      { symbol: "NVDA", name: "NVIDIA Corp." },
      { symbol: "TSLA", name: "Tesla Inc." },
      { symbol: "META", name: "Meta Platforms" },
    ],
    // ... other categories ...
  }
  
  export async function fetchCategoryStocks(category: keyof typeof STOCK_SYMBOLS): Promise<Stock[]> {
    const companies = STOCK_SYMBOLS[category]
    if (!companies) return []
  
    // MarketStack supports multiple ticker symbols in "symbols" param
    const symbols = companies.map(s => s.symbol).join(',')
    const url = `${BASE_URL}/eod/latest?access_key=${API_KEY}&symbols=${symbols}`
  
    const response = await fetch(url)
    if (!response.ok) throw new Error(`MarketStack error: ${response.status}`)
  
    const data = await response.json()
    if (!data?.data) throw new Error('Invalid response format from MarketStack')
  
    // Sometimes name is missing; pull from mapping
    return companies.map((comp) => {
      const quote = data.data.find((x: any) => x.symbol === comp.symbol)
      if (!quote) {
        return { symbol: comp.symbol, name: comp.name, price: 0, change: 0, changePercent: 0 }
      }
      const price = quote.close ?? quote.last ?? 0
      const open = quote.open ?? price
      const change = price - open
      const changePercent = open ? (change / open) * 100 : 0
  
      return {
        symbol: comp.symbol,
        name: comp.name,   // always use your map for display
        price,
        change,
        changePercent,
      }
    })
  }
  