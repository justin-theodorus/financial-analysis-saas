"use client"

import { Brain, BarChart3, MessageSquare } from "lucide-react"
import { AnalysisResponse } from "@/lib/api"

interface Stock {
  symbol: string
  name: string
  price: number
  change: number
  changePercent: number
}

interface AnalysisPanelProps {
  stock: Stock
  analysisData: AnalysisResponse
}

export default function AnalysisPanel({ stock, analysisData }: AnalysisPanelProps) {
  // Use real data from backend API
  const technicalAnalysis = analysisData.technicalAnalysis
  const semanticAnalysis = analysisData.semanticAnalysis
  const aiInsight = analysisData.aiInsight

  return (
    <div className="space-y-4 max-h-[calc(100vh-200px)] overflow-y-auto">
      {/* Technical Analysis */}
      <div className="bg-white dark:bg-[#1F1F23] border border-gray-200 dark:border-[#2B2B30] rounded-lg p-4">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">Technical Analysis</h3>
        </div>

        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">Trend</span>
            <span
              className={`px-2 py-1 rounded text-xs font-medium ${
                technicalAnalysis.trend === "Bullish"
                  ? "bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400"
                  : "bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400"
              }`}
            >
              {technicalAnalysis.trend}
            </span>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">Support</span>
            <span className="text-sm font-medium text-gray-900 dark:text-white">${technicalAnalysis.support}</span>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">Resistance</span>
            <span className="text-sm font-medium text-gray-900 dark:text-white">${technicalAnalysis.resistance}</span>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">RSI</span>
            <span className="text-sm font-medium text-gray-900 dark:text-white">{technicalAnalysis.rsi}</span>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">MACD</span>
            <span
              className={`px-2 py-1 rounded text-xs font-medium ${
                technicalAnalysis.macd === "Buy Signal"
                  ? "bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400"
                  : "bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400"
              }`}
            >
              {technicalAnalysis.macd}
            </span>
          </div>
        </div>
      </div>

      {/* Semantic Analysis */}
      <div className="bg-white dark:bg-[#1F1F23] border border-gray-200 dark:border-[#2B2B30] rounded-lg p-4">
        <div className="flex items-center gap-2 mb-4">
          <MessageSquare className="w-5 h-5 text-purple-600" />
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">Semantic Analysis</h3>
        </div>

        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">Sentiment</span>
            <span
              className={`px-2 py-1 rounded text-xs font-medium ${
                semanticAnalysis.sentiment === "Positive"
                  ? "bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400"
                  : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400"
              }`}
            >
              {semanticAnalysis.sentiment}
            </span>
          </div>

                      <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">News Score</span>
              <div className="flex items-center gap-2">
                <div className="w-16 h-2 bg-gray-200 dark:bg-gray-700 rounded-full">
                  <div
                    className="h-full bg-blue-600 rounded-full"
                    style={{ width: `${(semanticAnalysis.newsScore / 10) * 100}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-gray-900 dark:text-white">{semanticAnalysis.newsScore.toFixed(1)}/10</span>
              </div>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Social Buzz</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">{semanticAnalysis.socialMediaBuzz}</span>
            </div>

          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">Analyst Rating</span>
            <span
              className={`px-2 py-1 rounded text-xs font-medium ${
                semanticAnalysis.analystRating === "Buy"
                  ? "bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400"
                  : "bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400"
              }`}
            >
              {semanticAnalysis.analystRating}
            </span>
          </div>
        </div>
      </div>

      {/* AI Insight */}
      <div className="bg-white dark:bg-[#1F1F23] border border-gray-200 dark:border-[#2B2B30] rounded-lg p-4">
        <div className="flex items-center gap-2 mb-4">
          <Brain className="w-5 h-5 text-orange-600" />
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">AI Insight</h3>
        </div>

        <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{aiInsight}</p>
      </div>
    </div>
  )
}
