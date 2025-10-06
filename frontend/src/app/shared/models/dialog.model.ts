export interface DialogMessage {
  id: string;
  characterId: string;
  content: string;
  timestamp: Date;
  emotionalState: string;
  internalThoughts?: string;
  selected: boolean;
  useInStory: boolean;
}

export interface DialogConversation {
  id: string;
  storyId: string;
  context: string;
  activeCharacters: string[];
  messages: DialogMessage[];
  createdAt: Date;
  lastActivity: Date;
}

export interface CharacterTemplate {
  id: string;
  name: string;
  category: string;
  personalityTraits: string[];
  backgroundElements: string[];
  speechPatterns: string[];
  description: string;
}

export interface SelectedResponse {
  characterId: string;
  messageId?: string;
  responseContent?: string;
  content?: string;
  timestamp?: Date;
  useInStory: boolean;
}