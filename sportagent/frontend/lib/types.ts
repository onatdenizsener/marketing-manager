export type Momentum = "rising" | "stable" | "declining";
export type ContentFormat = "reels" | "story" | "tweet" | "post" | "youtube_short";

export interface TrendItem {
  keyword: string;
  momentum: Momentum;
  source_signal_ids: string[];
  rationale: string;
}

export interface NewsSummaryItem {
  headline: string;
  summary_one_liner: string;
  source_signal_ids: string[];
}

export interface ContentAngle {
  idea: string;
  format: ContentFormat;
  target_audience: string;
  hashtags: string[];
  source_signal_ids: string[];
}

export interface CampaignPlan {
  theme: string;
  hook: string;
  target_audience: string;
  channel_recommendations: string[];
  content_pillar: string;
}

export interface NicheReport {
  insufficient_data: boolean;
  trending: TrendItem[];
  news_summary: NewsSummaryItem[];
  content_angles: ContentAngle[];
  campaign_plan: CampaignPlan | null;
  errors: string[];
}

export interface DailyReport {
  id: string;
  report_date: string;
  status: "pending" | "success" | "partial" | "failed";
  niches: Record<string, NicheReport>;
  markdown: string | null;
  signals_used: number;
  llm_tokens: number;
  duration_ms: number | null;
  errors: string[];
  created_at: string;
  updated_at: string;
}

export interface ReportListItem {
  id: string;
  report_date: string;
  status: string;
  signals_used: number;
  llm_tokens: number;
  duration_ms: number | null;
  created_at: string;
}

export interface SourceHealthRow {
  source: string;
  total_7d: number;
  success_7d: number;
  success_rate_7d: number | null;
  last_attempt: string | null;
  signals_7d: number;
}
