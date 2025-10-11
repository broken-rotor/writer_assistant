// Story Model matching new simplified requirements

export interface SystemPrompts {
  mainPrefix: string;
  mainSuffix: string;
  assistantPrompt: string;
  editorPrompt: string;
}

export interface GeneralConfig {
  title: string;
  systemPrompts: SystemPrompts;
  worldbuilding: string;
}

export interface Character {
  id: string;
  basicBio: string;
  name: string;
  sex: string;
  gender: string;
  sexualPreference: string;
  age: number;
  physicalAppearance: string;
  usualClothing: string;
  personality: string;
  motivations: string;
  fears: string;
  relationships: string;
  isHidden: boolean;
  metadata: {
    creationSource: 'user' | 'ai_generated' | 'imported';
    lastModified: Date;
  };
}

export interface Rater {
  id: string;
  name: string;
  systemPrompt: string;
  enabled: boolean;
  metadata: {
    created: Date;
    lastModified: Date;
  };
}

export interface Chapter {
  id: string;
  number: number;
  title: string;
  content: string;
  plotPoint: string;
  incorporatedFeedback: FeedbackItem[];
  metadata: {
    created: Date;
    lastModified: Date;
    wordCount: number;
  };
}

export interface FeedbackItem {
  source: string; // Character or rater name
  type: 'action' | 'dialog' | 'sensation' | 'emotion' | 'thought' | 'suggestion';
  content: string;
  incorporated: boolean;
}

export interface CharacterFeedback {
  characterName: string;
  actions: string[];
  dialog: string[];
  physicalSensations: string[];
  emotions: string[];
  internalMonologue: string[];
}

export interface RaterFeedback {
  raterName: string;
  opinion: string;
  suggestions: string[];
}

export interface EditorSuggestion {
  issue: string;
  suggestion: string;
  priority: 'high' | 'medium' | 'low';
  selected: boolean;
}

export interface ChapterCreationState {
  plotPoint: string;
  incorporatedFeedback: FeedbackItem[];
  feedbackRequests: Map<string, {
    status: 'pending' | 'generating' | 'ready';
    feedback: CharacterFeedback | RaterFeedback;
  }>;
  generatedChapter?: {
    text: string;
    status: string;
    metadata: any;
  };
  editorReview?: {
    suggestions: EditorSuggestion[];
    userSelections: boolean[];
  };
}

export interface Story {
  id: string;
  general: GeneralConfig;
  characters: Map<string, Character>;
  raters: Map<string, Rater>;
  story: {
    summary: string;
    chapters: Chapter[];
  };
  chapterCreation: ChapterCreationState;
  metadata: {
    version: string;
    created: Date;
    lastModified: Date;
  };
}

export interface StoryListItem {
  id: string;
  title: string;
  lastModified: Date;
  chapterCount: number;
}

// API Request/Response types - Simplified structure for stateless backend
export interface CharacterFeedbackRequest {
  systemPrompts: {
    mainPrefix: string;
    mainSuffix: string;
  };
  worldbuilding: string;
  storySummary: string;
  previousChapters: Array<{
    number: number;
    title: string;
    content: string;
  }>;
  character: {
    name: string;
    basicBio: string;
    sex: string;
    gender: string;
    sexualPreference: string;
    age: number;
    physicalAppearance: string;
    usualClothing: string;
    personality: string;
    motivations: string;
    fears: string;
    relationships: string;
  };
  plotPoint: string;
}

export interface RaterFeedbackRequest {
  systemPrompts: {
    mainPrefix: string;
    mainSuffix: string;
  };
  raterPrompt: string;
  worldbuilding: string;
  storySummary: string;
  previousChapters: Array<{
    number: number;
    title: string;
    content: string;
  }>;
  plotPoint: string;
}

export interface GenerateChapterRequest {
  systemPrompts: {
    mainPrefix: string;
    mainSuffix: string;
    assistantPrompt: string;
  };
  worldbuilding: string;
  storySummary: string;
  previousChapters: Array<{
    number: number;
    title: string;
    content: string;
  }>;
  characters: Array<{
    name: string;
    basicBio: string;
    sex: string;
    gender: string;
    sexualPreference: string;
    age: number;
    physicalAppearance: string;
    usualClothing: string;
    personality: string;
    motivations: string;
    fears: string;
    relationships: string;
  }>;
  plotPoint: string;
  incorporatedFeedback: FeedbackItem[];
}

export interface ModifyChapterRequest {
  systemPrompts: {
    mainPrefix: string;
    mainSuffix: string;
    assistantPrompt: string;
  };
  worldbuilding: string;
  storySummary: string;
  previousChapters: Array<{
    number: number;
    title: string;
    content: string;
  }>;
  currentChapter: string;
  userRequest: string;
}

export interface EditorReviewRequest {
  systemPrompts: {
    mainPrefix: string;
    mainSuffix: string;
    editorPrompt: string;
  };
  worldbuilding: string;
  storySummary: string;
  previousChapters: Array<{
    number: number;
    title: string;
    content: string;
  }>;
  characters: Array<{
    name: string;
    basicBio: string;
    sex: string;
    gender: string;
    sexualPreference: string;
    age: number;
    physicalAppearance: string;
    usualClothing: string;
    personality: string;
    motivations: string;
    fears: string;
    relationships: string;
  }>;
  chapterToReview: string;
}

export interface FleshOutRequest {
  systemPrompts: {
    mainPrefix: string;
    mainSuffix: string;
  };
  worldbuilding: string;
  storySummary: string;
  textToFleshOut: string;
  context: string;
}

export interface GenerateCharacterDetailsRequest {
  systemPrompts: {
    mainPrefix: string;
    mainSuffix: string;
  };
  worldbuilding: string;
  storySummary: string;
  basicBio: string;
  existingCharacters: Array<{
    name: string;
    basicBio: string;
    relationships: string;
  }>;
}

// API Response types
export interface CharacterFeedbackResponse {
  characterName: string;
  feedback: {
    actions: string[];
    dialog: string[];
    physicalSensations: string[];
    emotions: string[];
    internalMonologue: string[];
  };
}

export interface RaterFeedbackResponse {
  raterName: string;
  feedback: {
    opinion: string;
    suggestions: Array<{
      issue: string;
      suggestion: string;
      priority: 'high' | 'medium' | 'low';
    }>;
  };
}

export interface GenerateChapterResponse {
  chapterText: string;
}

export interface ModifyChapterResponse {
  modifiedChapterText: string;
}

export interface EditorReviewResponse {
  overallAssessment: string;
  suggestions: EditorSuggestion[];
}

export interface FleshOutResponse {
  fleshedOutText: string;
}

export interface GenerateCharacterDetailsResponse {
  name: string;
  sex: string;
  gender: string;
  sexualPreference: string;
  age: number;
  physicalAppearance: string;
  usualClothing: string;
  personality: string;
  motivations: string;
  fears: string;
  relationships: string;
}
