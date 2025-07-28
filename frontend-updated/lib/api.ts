// API Configuration and utilities for backend integration

const API_BASE_URL = 'http://localhost:8000'

// Types matching the backend response structure
export interface StockInfo {
  symbol: string
  price: number
}

export interface TechnicalAnalysisResponse {
  trend: string
  support: number
  resistance: number
  rsi: number
  macd: string
}

export interface SemanticAnalysisResponse {
  sentiment: string
  newsScore: number
  socialMediaBuzz: string
  analystRating: string
}

export interface AnalysisResponse {
  stock: StockInfo
  technicalAnalysis: TechnicalAnalysisResponse
  semanticAnalysis: SemanticAnalysisResponse
  aiInsight: string
}

export interface AnalysisRequest {
  symbol: string
  days_back?: number
  technical_interval?: string
  technical_limit?: number
}

// API Error class
export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

// API call function with proper error handling
export async function analyzeStock(request: AnalysisRequest): Promise<AnalysisResponse> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 30000) // 30 second timeout

  try {
    const requestData = {
      symbol: request.symbol,
      days_back: request.days_back || 7,
      technical_interval: request.technical_interval || "1D",
      technical_limit: request.technical_limit || 100
    }

    console.log('Sending analysis request:', requestData)

    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestData),
      signal: controller.signal
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      const errorText = await response.text()
      console.error('Server error response:', errorText)
      throw new ApiError(response.status, errorText || `HTTP error! status: ${response.status}`)
    }

    const analysisData = await response.json()
    console.log('Analysis data received:', analysisData)
    return analysisData

  } catch (error) {
    clearTimeout(timeoutId)

    if (error instanceof Error && error.name === 'AbortError') {
      console.error('Request timed out')
      throw new ApiError(408, 'Analysis is taking longer than expected. Please try again.')
    } else if (error instanceof ApiError) {
      throw error
    } else {
      console.error('Analysis failed:', error)
      const errorMessage = error instanceof Error ? error.message : 'Analysis failed'
      throw new ApiError(500, errorMessage)
    }
  }
} 