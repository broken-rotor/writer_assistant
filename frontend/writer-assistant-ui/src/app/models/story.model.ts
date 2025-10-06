export enum StoryPhase {
  OUTLINE_DEVELOPMENT = 'outline_development',
  CHAPTER_DEVELOPMENT = 'chapter_development',
  COMPLETED = 'completed'
}

export enum StoryStatus {
  DRAFT = 'draft',
  IN_PROGRESS = 'in_progress',
  REVIEW = 'review',
  APPROVED = 'approved'
}

export interface Character {
  id: string;
  name: string;
  role: string;
  personality_traits: string[];
  background: Record<string, any>;
  relationships: Record<string, any>;
}

export interface Chapter {
  id: string;
  number: number;
  title: string;
  content: string;
  status: StoryStatus;
  word_count: number;
  created_at: string;
  updated_at: string;
}

export interface Outline {
  id: string;
  structure: Record<string, any>;
  plot_points: Array<Record<string, any>>;
  character_arcs: Record<string, any>;
  themes: string[];
  status: StoryStatus;
  created_at: string;
  updated_at: string;
}

export interface Story {
  id: string;
  title: string;
  genre: string;
  description: string;
  current_phase: StoryPhase;
  status: StoryStatus;
  outline?: Outline;
  chapters: Chapter[];
  characters: Character[];
  user_id: string;
  created_at: string;
  updated_at: string;
  progress: Record<string, any>;
}

export interface StoryCreate {
  title: string;
  genre: string;
  description?: string;
  initial_guidance?: string;
  configuration?: Record<string, any>;
}

export interface StoryUpdate {
  title?: string;
  description?: string;
  status?: StoryStatus;
  current_phase?: StoryPhase;
}