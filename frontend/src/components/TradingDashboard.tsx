import { useState } from "react";
import { SidebarProvider } from "@/components/ui/sidebar";
import { DashboardSidebar } from "./DashboardSidebar";
import { StockGrid } from "./StockGrid";
import { AnalysisPanel } from "./AnalysisPanel";
import { DashboardHeader } from "./DashboardHeader";

export interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
}

export interface Category {
  id: string;
  name: string;
  icon: string;
  stocks: Stock[];
}

const mockData: Category[] = [
  {
    id: "tech",
    name: "Technology",
    icon: "💻",
    stocks: [
      { symbol: "AAPL", name: "Apple Inc.", price: 192.53, change: 2.14, changePercent: 1.12 },
      { symbol: "MSFT", name: "Microsoft Corp.", price: 415.26, change: -1.87, changePercent: -0.45 },
      { symbol: "GOOGL", name: "Alphabet Inc.", price: 143.05, change: 0.95, changePercent: 0.67 },
      { symbol: "NVDA", name: "NVIDIA Corp.", price: 875.28, change: 12.45, changePercent: 1.44 },
      { symbol: "TSLA", name: "Tesla Inc.", price: 248.50, change: -3.22, changePercent: -1.28 },
      { symbol: "META", name: "Meta Platforms", price: 501.20, change: 4.15, changePercent: 0.83 }
    ]
  },
  {
    id: "finance",
    name: "Financial",
    icon: "🏦",
    stocks: [
      { symbol: "JPM", name: "JPMorgan Chase", price: 175.89, change: 1.23, changePercent: 0.70 },
      { symbol: "BAC", name: "Bank of America", price: 34.56, change: -0.45, changePercent: -1.29 },
      { symbol: "WFC", name: "Wells Fargo", price: 54.78, change: 0.89, changePercent: 1.65 },
      { symbol: "GS", name: "Goldman Sachs", price: 389.12, change: 2.34, changePercent: 0.61 },
      { symbol: "MS", name: "Morgan Stanley", price: 91.45, change: -1.12, changePercent: -1.21 }
    ]
  },
  {
    id: "energy",
    name: "Energy",
    icon: "⚡",
    stocks: [
      { symbol: "XOM", name: "Exxon Mobil", price: 108.34, change: 1.89, changePercent: 1.77 },
      { symbol: "CVX", name: "Chevron Corp.", price: 151.67, change: 0.78, changePercent: 0.52 },
      { symbol: "COP", name: "ConocoPhillips", price: 122.90, change: -0.95, changePercent: -0.77 },
      { symbol: "SLB", name: "Schlumberger", price: 48.23, change: 1.34, changePercent: 2.86 }
    ]
  },
  {
    id: "healthcare",
    name: "Healthcare",
    icon: "🏥",
    stocks: [
      { symbol: "JNJ", name: "Johnson & Johnson", price: 160.45, change: 0.67, changePercent: 0.42 },
      { symbol: "PFE", name: "Pfizer Inc.", price: 28.90, change: -0.23, changePercent: -0.79 },
      { symbol: "UNH", name: "UnitedHealth Group", price: 518.76, change: 3.45, changePercent: 0.67 },
      { symbol: "ABBV", name: "AbbVie Inc.", price: 164.23, change: 1.12, changePercent: 0.69 }
    ]
  }
];

export const TradingDashboard = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>("tech");
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentCategory = mockData.find(cat => cat.id === selectedCategory);

  const handleAnalyze = async () => {
    if (!selectedStock) return;
    
    setIsAnalyzing(true);
    setError(null); // Clear previous errors
    
    // Set a timeout for the request
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
    
    try {
      const requestData = {
        symbol: selectedStock.symbol,
        days_back: 7,
        technical_interval: "1D",
        technical_limit: 100
      };
      
      console.log('Sending analysis request:', requestData);
      
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
        signal: controller.signal
      });
  
      clearTimeout(timeoutId);
  
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Server error response:', errorText);
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }
  
      const analysisData = await response.json();
      console.log('Analysis data received:', analysisData);
      setAnalysisData(analysisData);
      
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error.name === 'AbortError') {
        console.error('Request timed out');
        setError('Analysis is taking longer than expected. Please try again.');
      } else {
        console.error('Analysis failed:', error);
        setError(error.message);
      }
      
    } finally {
      setIsAnalyzing(false);
    }
  };
  

  return (
    <SidebarProvider>
      <div className="min-h-screen w-full bg-background">
        <DashboardHeader />
        
        <div className="flex">
          <DashboardSidebar
            categories={mockData}
            selectedCategory={selectedCategory}
            onCategoryChange={setSelectedCategory}
          />
          
          <main className="flex-1 p-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-120px)]">
              <div className="lg:col-span-2">
                <StockGrid
                  category={currentCategory}
                  selectedStock={selectedStock}
                  onSelectStock={setSelectedStock}
                  onAnalyze={handleAnalyze}
                  isAnalyzing={isAnalyzing}
                />
              </div>
              
              <div className="lg:col-span-1">
                <AnalysisPanel
                  selectedStock={selectedStock}
                  analysisData={analysisData}
                  isAnalyzing={isAnalyzing}
                  error={error}
                />
              </div>
            </div>
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
};