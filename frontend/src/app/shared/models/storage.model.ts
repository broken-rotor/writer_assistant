export interface LocalStorageInfo {
  usedSpace: number;
  availableSpace: number;
  storiesCount: number;
  lastBackup: Date;
}

export interface ConversationBranch {
  id: string;
  name: string;
  parentId?: string;
  prompts: ConversationPrompt[];
  storyState: any;
  createdAt: Date;
  lastModified: Date;
}

export interface ConversationPrompt {
  id: string;
  parentId?: string;
  content: string;
  timestamp: Date;
  modifications: string[];
  storyState: any;
}

export interface ConversationTree {
  rootPrompt: ConversationPrompt;
  branches: ConversationBranch[];
  currentBranch: string;
  currentPrompt: string;
}

export interface StateCheckpoint {
  id: string;
  name: string;
  description: string;
  timestamp: Date;
  storyState: any;
  memoryState: any;
  conversationState: any;
}

export interface MemoryState {
  agentId: string;
  agentName: string;
  workingMemory: any;
  episodicMemory: any;
  semanticMemory: any;
  lastUpdated: Date;
  size: number;
}

export interface ValidationResult {
  isValid: boolean;
  issues: ValidationIssue[];
  warnings: ValidationWarning[];
}

export interface ValidationIssue {
  type: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
  affectedElements: string[];
  suggestedFix?: string;
}

export interface ValidationWarning {
  type: string;
  description: string;
  affectedElements: string[];
}