"use client"

import { usePathname } from "next/navigation"
import StockGrid from "./stock-grid"
import { BarChart2, TrendingUp, DollarSign, Activity } from "lucide-react"

export default function Content() {
  const pathname = usePathname()

  // Extract category from pathname
  const category = pathname.includes("/market/") ? pathname.split("/market/")[1] : "dashboard"

  if (category === "dashboard") {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Dashboard Overview</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Welcome to StockInsight AI - Your intelligent stock analysis platform
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white dark:bg-[#1F1F23] border border-gray-200 dark:border-[#2B2B30] rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Stocks Tracked</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">2,847</p>
              </div>
              <BarChart2 className="w-8 h-8 text-blue-600" />
            </div>
          </div>

          <div className="bg-white dark:bg-[#1F1F23] border border-gray-200 dark:border-[#2B2B30] rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">AI Analyses Today</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">156</p>
              </div>
              <Activity className="w-8 h-8 text-green-600" />
            </div>
          </div>

          <div className="bg-white dark:bg-[#1F1F23] border border-gray-200 dark:border-[#2B2B30] rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Market Cap Tracked</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">$45.2T</p>
              </div>
              <DollarSign className="w-8 h-8 text-purple-600" />
            </div>
          </div>

          <div className="bg-white dark:bg-[#1F1F23] border border-gray-200 dark:border-[#2B2B30] rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Avg. Accuracy</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">94.2%</p>
              </div>
              <TrendingUp className="w-8 h-8 text-orange-600" />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-[#1F1F23] border border-gray-200 dark:border-[#2B2B30] rounded-lg p-6">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Getting Started</h2>
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-xs font-bold text-blue-600 dark:text-blue-400">1</span>
              </div>
              <div>
                <h3 className="font-medium text-gray-900 dark:text-white">Choose a Market Category</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Select from Technology, Financial, Energy, or Healthcare sectors
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-xs font-bold text-blue-600 dark:text-blue-400">2</span>
              </div>
              <div>
                <h3 className="font-medium text-gray-900 dark:text-white">Select a Stock</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Click on any stock card to select it for analysis
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-xs font-bold text-blue-600 dark:text-blue-400">3</span>
              </div>
              <div>
                <h3 className="font-medium text-gray-900 dark:text-white">Get AI Insights</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Click "Analyze" to receive semantic and technical analysis
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return <StockGrid key={category} category={category} />
}
