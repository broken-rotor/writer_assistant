export interface FeedbackAgent {
  id: string;
  name: string;
  type: 'rater' | 'editor' | 'specialist';
  specialties: string[];
  focusAreas: string[];
  description: string;
  typicalScore: number;
}

export interface FeedbackItem {
  id: string;
  agentId: string;
  type: 'strength' | 'concern' | 'suggestion';
  content: string;
  priority: 'low' | 'medium' | 'high';
  actionable: boolean;
  selected: boolean;
}

export interface FeedbackData {
  agentId: string;
  agentName: string;
  score: number;
  feedback?: string;
  strengths?: string[];
  concerns?: string[];
  suggestions: string[] | FeedbackItem[];
  priority?: 'low' | 'medium' | 'high';
  timestamp: Date;
}

export interface ContentRefinement {
  originalContent: string;
  refinedContent: string;
  appliedFeedback: string[];
  beforeScore: number;
  afterScore: number;
  improvementAreas: string[];
  remainingIssues: string[];
}