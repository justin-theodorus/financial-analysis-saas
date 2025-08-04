"use client"

import { useState, useEffect } from "react"
import { TrendingUp, TrendingDown, Brain, BarChart3, Loader2 } from "lucide-react"
import AnalysisPanel from "./analysis-panel"
import { analyzeStock, AnalysisResponse, ApiError } from "@/lib/api"
import { fetchCategoryStocks, Stock, STOCK_SYMBOLS } from "@/lib/marketstack"

interface StockGridProps {
  category: string
}

export default function StockGrid({ category }: StockGridProps) {
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisData, setAnalysisData] = useState<AnalysisResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  
  // New state for API data
  const [stocks, setStocks] = useState<Stock[]>([])
  const [loading, setLoading] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)

  // Fetch stock data when category changes
  useEffect(() => {
    const loadStocks = async () => {
      if (!category || !(category in STOCK_SYMBOLS)) {
        setStocks([])
        return
      }

      setLoading(true)
      setApiError(null)
      
      try {
        const stockData = await fetchCategoryStocks(category as keyof typeof STOCK_SYMBOLS)
        setStocks(stockData)
      } catch (err) {
        console.error('Failed to load stocks:', err)
        setApiError('Failed to load stock data. Please try again.')
        // Fallback to empty array or cached data
        setStocks([])
      } finally {
        setLoading(false)
      }
    }

    loadStocks()
  }, [category])

  const formatPrice = (price: number) => `$${price.toFixed(2)}`
  const formatChange = (change: number) => `${change >= 0 ? "+" : ""}${change.toFixed(2)}`
  const formatPercent = (percent: number) => `${percent >= 0 ? "+" : ""}${percent.toFixed(2)}%`

  const handleAnalyze = async () => {
    if (!selectedStock) return

    setIsAnalyzing(true)
    setAnalysisData(null)
    setError(null)

    try {
      const response = await analyzeStock({
        symbol: selectedStock.symbol,
        days_back: 7,
        technical_interval: "1D",
        technical_limit: 100
      })

      setAnalysisData(response)
    } catch (err) {
      console.error('Analysis failed:', err)
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Analysis failed. Please try again.')
      }
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleRefresh = async () => {
    if (!category || !(category in STOCK_SYMBOLS)) return
    
    setLoading(true)
    setApiError(null)
    
    try {
      const stockData = await fetchCategoryStocks(category as keyof typeof STOCK_SYMBOLS)
      setStocks(stockData)
    } catch (err) {
      console.error('Failed to refresh stocks:', err)
      setApiError('Failed to refresh stock data. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const getCategoryIcon = () => {
    switch (category) {
      case "technology":
        return "💻"
      case "financial":
        return "🏦"
      case "energy":
        return "⚡"
      case "healthcare":
        return "🏥"
      default:
        return "📊"
    }
  }

  return (
    <div className="flex gap-6 h-full">
      {/* Main Content */}
      <div className="flex-1 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
              <span className="text-2xl">{getCategoryIcon()}</span>
              {category.charAt(0).toUpperCase() + category.slice(1)} Stocks
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Select a stock to analyze with AI insights
              {loading && " • Loading live data..."}
            </p>
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleRefresh}
              disabled={loading}
              className="bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg flex items-center gap-2 transition-colors text-sm"
            >
              <Loader2 className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            
            {selectedStock && (
              <button
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-6 py-3 rounded-lg flex items-center gap-2 transition-colors font-medium"
              >
                <BarChart3 className="w-5 h-5" />
                {isAnalyzing ? "Analyzing..." : `Analyze ${selectedStock.symbol}`}
              </button>
            )}
          </div>
        </div>

        {apiError && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <span className="text-red-600 dark:text-red-400">⚠️</span>
              <p className="text-red-600 dark:text-red-400 text-sm">{apiError}</p>
            </div>
          </div>
        )}

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Array.from({ length: 6 }).map((_, index) => (
              <div
                key={index}
                className="bg-white dark:bg-[#1F1F23] border border-gray-200 dark:border-[#2B2B30] rounded-lg p-4 animate-pulse"
              >
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <div className="h-6 bg-gray-300 dark:bg-gray-600 rounded w-16 mb-2"></div>
                    <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-24"></div>
                  </div>
                  <div className="h-6 bg-gray-300 dark:bg-gray-600 rounded w-20"></div>
                </div>
                <div className="flex items-center justify-between">
                  <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-12"></div>
                  <div className="flex gap-2">
                    <div className="h-5 bg-gray-300 dark:bg-gray-600 rounded w-12"></div>
                    <div className="h-5 bg-gray-300 dark:bg-gray-600 rounded w-16"></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {stocks.map((stock) => (
              <div
                key={stock.symbol}
                onClick={() => setSelectedStock(stock)}
                className={`
                  bg-white dark:bg-[#1F1F23] border rounded-lg p-4 cursor-pointer transition-all duration-200 hover:shadow-lg
                  ${
                    selectedStock?.symbol === stock.symbol
                      ? "border-blue-500 ring-2 ring-blue-500/20"
                      : "border-gray-200 dark:border-[#2B2B30] hover:border-gray-300 dark:hover:border-[#3B3B40]"
                  }
                `}
              >
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white">{stock.symbol}</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{stock.name}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-gray-900 dark:text-white">
                      {formatPrice(stock.price)}
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Change:</span>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-sm font-medium ${
                        stock.change >= 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
                      }`}
                    >
                      {formatChange(stock.change)}
                    </span>
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium flex items-center gap-1 ${
                        stock.changePercent >= 0
                          ? "bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400"
                          : "bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400"
                      }`}
                    >
                      {stock.changePercent >= 0 ? (
                        <TrendingUp className="w-3 h-3" />
                      ) : (
                        <TrendingDown className="w-3 h-3" />
                      )}
                      {formatPercent(stock.changePercent)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {stocks.length === 0 && !loading && (
          <div className="text-center py-12">
            <Brain className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No stocks available</h3>
            <p className="text-gray-600 dark:text-gray-400">Select a market category to view available stocks</p>
          </div>
        )}
      </div>

      {/* Right Panel - Keep existing code */}
      <div className="w-80 flex-shrink-0">
        {selectedStock && !isAnalyzing && !analysisData && !error && (
          <div className="bg-white dark:bg-[#1F1F23] border border-gray-200 dark:border-[#2B2B30] rounded-lg p-6">
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🎯</span>
              </div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">{selectedStock.symbol} Selected</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-2">{selectedStock.name}</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                {formatPrice(selectedStock.price)}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                Click "Analyze" to get AI-powered insights for this stock
              </p>
            </div>
          </div>
        )}

        {isAnalyzing && (
          <div className="bg-white dark:bg-[#1F1F23] border border-gray-200 dark:border-[#2B2B30] rounded-lg p-6">
            <div className="text-center">
              <div className="relative w-16 h-16 mx-auto mb-4">
                <div className="absolute inset-0 border-4 border-blue-200 dark:border-blue-800 rounded-full"></div>
                <div className="absolute inset-0 border-4 border-blue-600 rounded-full border-t-transparent animate-spin"></div>
                <div className="absolute inset-2 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
                  <Brain className="w-6 h-6 text-blue-600 animate-pulse" />
                </div>
              </div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                Analyzing {selectedStock?.symbol}
              </h3>
              <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                <div className="flex items-center justify-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Processing market data...</span>
                </div>
                <div className="flex items-center justify-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Running technical analysis...</span>
                </div>
                <div className="flex items-center justify-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Generating AI insights...</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-white dark:bg-[#1F1F23] border border-red-200 dark:border-red-800 rounded-lg p-6">
            <div className="text-center">
              <div className="w-12 h-12 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">⚠️</span>
              </div>
              <h3 className="text-lg font-bold text-red-600 dark:text-red-400 mb-2">Analysis Failed</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{error}</p>
              <button
                onClick={handleAnalyze}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        )}

        {analysisData && selectedStock && <AnalysisPanel stock={selectedStock} analysisData={analysisData} />}
      </div>
    </div>
  )
}
