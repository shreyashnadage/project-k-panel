export interface MetricValue {
  metric_code: string
  period_start: string
  period_end: string
  value_numeric: number | null
  value_json: Record<string, unknown> | null
  unit: string
  version: number
  computed_at: string | null
}

export interface MetricSummary {
  client_id: string
  vertical: string
  metrics: MetricValue[]
  computed_at: string | null
}

export interface AlertEvidence {
  source_type: string
  source_id: string
  description: string
  value: unknown
}

export interface AlertResponse {
  alert_id: string
  detector_code: string
  severity: 'warning' | 'critical'
  title: string
  description: string
  evidence: AlertEvidence[]
  status: 'open' | 'acknowledged' | 'resolved' | 'snoozed'
  created_at: string
  snoozed_until: string | null
}

export interface AlertListResponse {
  client_id: string
  alerts: AlertResponse[]
  total: number
}

export interface AlertUpdateRequest {
  status: 'acknowledged' | 'resolved' | 'snoozed'
  snoozed_until?: string
}

export interface InsightResponse {
  insight_id: string
  metric_code: string
  category: string
  severity: string
  title: string
  body: string
  data: Record<string, unknown>
  is_read: boolean
  created_at: string
  expires_at: string | null
}

export interface InsightListResponse {
  client_id: string
  insights: InsightResponse[]
  total: number
}

export interface LoanRecommendation {
  reco_id: string
  product_type: string
  recommended_amount_paise: number
  confidence: 'high' | 'medium' | 'low'
  rationale: string
  status: string
  valid_until: string | null
  created_at: string
}

export interface EligibilityRule {
  rule_code: string
  rule_name: string
  passed: boolean
  detail: string
  weight: number
}

export interface LoanEvidenceItem {
  source_type: string
  source_id: string
  description: string
  value: unknown
}

export interface LoanEvidenceResponse extends LoanRecommendation {
  evidence: LoanEvidenceItem[]
  eligibility: EligibilityRule[]
}

export interface PipelineRun {
  run_id: string
  client_id: string
  started_at: string
  finished_at: string | null
  status: 'running' | 'success' | 'failed' | 'partial'
  layer_reached: string | null
  vouchers_pulled: number
  metrics_computed: number
  alerts_raised: number
  error_message: string | null
}

export interface PipelineTriggerResponse {
  run_id: string
  status: string
  message: string
}

export interface ClientProfileResponse {
  client_id: string
  vertical: string
  fiscal_year_start_month: number
  config_overrides: Record<string, unknown>
}
