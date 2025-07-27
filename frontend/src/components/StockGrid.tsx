import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, BarChart3 } from "lucide-react";
import { Category, Stock } from "./TradingDashboard";

interface StockGridProps {
  category?: Category;
  selectedStock: Stock | null;
  onSelectStock: (stock: Stock) => void;
  onAnalyze: () => void;
  isAnalyzing: boolean;
}

export const StockGrid = ({ category, selectedStock, onSelectStock, onAnalyze, isAnalyzing }: StockGridProps) => {
  if (!category) {
    return (
      <Card className="h-full">
        <CardContent className="flex items-center justify-center h-full">
          <p className="text-muted-foreground">Select a category to view stocks</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <span>{category.icon}</span>
            {category.name} Stocks
          </h2>
          <p className="text-muted-foreground">
            Select a stock to analyze with AI insights
          </p>
        </div>
        
        {selectedStock && (
          <Button 
            onClick={onAnalyze}
            disabled={isAnalyzing}
            className="bg-gradient-to-r from-primary to-blue-500 hover:from-primary/90 hover:to-blue-500/90"
          >
            {isAnalyzing ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Analyzing...
              </>
            ) : (
              <>
                <BarChart3 className="w-4 h-4 mr-2" />
                Analyze {selectedStock.symbol}
              </>
            )}
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {category.stocks.map((stock) => (
          <Card 
            key={stock.symbol}
            className={`cursor-pointer transition-all duration-200 hover:shadow-lg ${
              selectedStock?.symbol === stock.symbol
                ? "ring-2 ring-primary bg-primary/5"
                : "hover:border-primary/50"
            }`}
            onClick={() => onSelectStock(stock)}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <h3 className="font-bold text-lg">{stock.symbol}</h3>
                  <p className="text-sm text-muted-foreground truncate">
                    {stock.name}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-lg">${stock.price.toFixed(2)}</p>
                  <Badge
                    variant={stock.change >= 0 ? "default" : "destructive"}
                    className={
                      stock.change >= 0
                        ? "bg-success text-success-foreground"
                        : ""
                    }
                  >
                    {stock.change >= 0 ? (
                      <TrendingUp className="w-3 h-3 mr-1" />
                    ) : (
                      <TrendingDown className="w-3 h-3 mr-1" />
                    )}
                    {stock.changePercent.toFixed(2)}%
                  </Badge>
                </div>
              </div>
              
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Change:</span>
                <span
                  className={
                    stock.change >= 0 ? "text-success" : "text-destructive"
                  }
                >
                  {stock.change >= 0 ? "+" : ""}
                  {stock.change.toFixed(2)}
                </span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};