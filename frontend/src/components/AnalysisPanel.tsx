import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { TrendingUp, Brain, MessageSquare, Target, Activity, AlertCircle } from "lucide-react";
import { Stock } from "./TradingDashboard";

interface AnalysisPanelProps {
  selectedStock: Stock | null;
  analysisData: any;
  isAnalyzing: boolean;
  error?: string | null;
}

export const AnalysisPanel = ({ selectedStock, analysisData, isAnalyzing, error }: AnalysisPanelProps) => {
  if (!selectedStock && !analysisData) {
    return (
      <Card className="h-full">
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center">
            <Brain className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">
              Select a stock and click "Analyze" to get AI insights
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isAnalyzing) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5" />
            Analyzing {selectedStock?.symbol}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Technical Analysis</span>
                <span>Processing...</span>
              </div>
              <Progress value={33} className="h-2" />
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Semantic Analysis</span>
                <span>Processing...</span>
              </div>
              <Progress value={66} className="h-2" />
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>AI Insights Generation</span>
                <span>Processing...</span>
              </div>
              <Progress value={90} className="h-2" />
            </div>
          </div>
          
          <div className="text-center text-muted-foreground">
            <div className="animate-pulse">AI is analyzing market data...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-destructive">
            <AlertCircle className="w-5 h-5" />
            Error: {error}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Failed to generate analysis. Please try again later or select a different stock.
          </p>
        </CardContent>
      </Card>
    );
  }

  if (analysisData) {
    return (
      <div className="space-y-4 h-full overflow-y-auto">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Technical Analysis
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Trend</span>
              <Badge variant="default" className="bg-success text-success-foreground">
                {analysisData.technicalAnalysis.trend}
              </Badge>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Support</span>
              <span className="font-mono">${analysisData.technicalAnalysis.support.toFixed(2)}</span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Resistance</span>
              <span className="font-mono">${analysisData.technicalAnalysis.resistance.toFixed(2)}</span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">RSI</span>
              <span className="font-mono">{analysisData.technicalAnalysis.rsi}</span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">MACD</span>
              <Badge variant="default" className="bg-success text-success-foreground">
                {analysisData.technicalAnalysis.macd}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5" />
              Semantic Analysis
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Sentiment</span>
              <Badge variant="default" className="bg-success text-success-foreground">
                {analysisData.semanticAnalysis.sentiment}
              </Badge>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">News Score</span>
              <div className="flex items-center gap-2">
                <Progress value={analysisData.semanticAnalysis.newsScore * 10} className="h-2 w-16" />
                <span className="font-mono text-sm">{analysisData.semanticAnalysis.newsScore}/10</span>
              </div>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Social Buzz</span>
              <Badge variant="outline">
                {analysisData.semanticAnalysis.socialMediaBuzz}
              </Badge>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Analyst Rating</span>
              <Badge variant="default" className="bg-success text-success-foreground">
                {analysisData.semanticAnalysis.analystRating}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5" />
              AI Insight
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed">
              {analysisData.aiInsight}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="w-5 h-5" />
          {selectedStock?.symbol} Selected
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <h3 className="font-semibold">{selectedStock?.name}</h3>
            <p className="text-2xl font-bold">${selectedStock?.price.toFixed(2)}</p>
            <p className={`text-sm ${selectedStock?.change && selectedStock.change >= 0 ? 'text-success' : 'text-destructive'}`}>
              {selectedStock?.change && selectedStock.change >= 0 ? '+' : ''}{selectedStock?.change.toFixed(2)} ({selectedStock?.changePercent.toFixed(2)}%)
            </p>
          </div>
          
          <div className="text-center">
            <p className="text-muted-foreground text-sm">
              Click "Analyze" to get AI-powered insights for this stock
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};