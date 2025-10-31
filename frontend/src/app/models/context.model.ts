/**
 * Core context state models for client-side persistence and state management
 */

export interface ContextMetadata {
  id: string;
  version: number;
  createdAt: Date;
  updatedAt: Date;
  parentVersion?: number;
  branchId?: string;
  tags?: string[];
  description?: string;
}

export interface ContextDiff {
  field: string;
  oldValue: any;
  newValue: any;
  timestamp: Date;
  operation: 'create' | 'update' | 'delete';
}

export interface ContextVersion<T = any> {
  metadata: ContextMetadata;
  data: T;
  diffs?: ContextDiff[];
  checksum?: string;
}

export interface ContextBranch {
  id: string;
  name: string;
  parentBranchId?: string;
  createdAt: Date;
  lastActiveAt: Date;
  description?: string;
  isActive: boolean;
}

/**
 * Base interface for all context types
 */
export interface BaseContext {
  id: string;
  type: ContextType;
  metadata: ContextMetadata;
  branches: ContextBranch[];
  currentBranchId: string;
}

export enum ContextType {
  SESSION = 'session',
  STORY = 'story',
  CHARACTER = 'character',
  CONVERSATION = 'conversation',
  PHASE = 'phase',
  SERVER = 'server'
}

/**
 * Session Context - Current writing session state
 */
export interface SessionContext extends BaseContext {
  type: ContextType.SESSION;
  sessionId: string;
  storyId?: string;
  activePhase?: string;
  userPreferences: {
    autoSave: boolean;
    contextRetention: number; // days
    maxBranches: number;
  };
  workspaceState: {
    openTabs: string[];
    activeTab?: string;
    sidebarState: any;
    viewMode: string;
  };
  recentActions: Array<{
    action: string;
    timestamp: Date;
    context?: any;
  }>;
}

/**
 * Story Context - Persistent story-level context
 */
export interface StoryContext extends BaseContext {
  type: ContextType.STORY;
  storyId: string;
  title: string;
  genre: string;
  outline: {
    summary: string;
    themes: string[];
    plotPoints: Array<{
      id: string;
      title: string;
      description: string;
      order: number;
    }>;
  };
  worldBuilding: {
    setting: string;
    timeframe: string;
    rules: string[];
    locations: Array<{
      id: string;
      name: string;
      description: string;
    }>;
  };
  narrative: {
    tone: string;
    style: string;
    perspective: string;
    tense: string;
  };
  progress: {
    currentPhase: string;
    completedChapters: number;
    totalChapters: number;
    wordCount: number;
  };
}

/**
 * Character Context - Character-specific persistent state
 */
export interface CharacterContext extends BaseContext {
  type: ContextType.CHARACTER;
  characterId: string;
  storyId: string;
  profile: {
    name: string;
    age?: number;
    description: string;
    personality: string[];
    background: string;
    motivations: string[];
    relationships: Array<{
      characterId: string;
      relationship: string;
      description: string;
    }>;
  };
  memory: {
    experiences: Array<{
      id: string;
      event: string;
      timestamp: Date;
      emotionalImpact: number;
      significance: number;
      relatedCharacters: string[];
    }>;
    knowledge: Array<{
      topic: string;
      level: number; // 1-10
      source: string;
      confidence: number;
    }>;
    secrets: Array<{
      secret: string;
      knownBy: string[];
      importance: number;
    }>;
  };
  currentState: {
    location?: string;
    mood: string;
    goals: string[];
    conflicts: string[];
    relationships: Record<string, number>; // characterId -> relationship strength
  };
}

/**
 * Conversation Context - Chat history and decisions
 */
export interface ConversationContext extends BaseContext {
  type: ContextType.CONVERSATION;
  conversationId: string;
  storyId?: string;
  participants: Array<{
    id: string;
    type: 'user' | 'agent';
    name: string;
    role?: string;
  }>;
  messages: Array<{
    id: string;
    senderId: string;
    content: string;
    timestamp: Date;
    type: 'text' | 'system' | 'feedback' | 'generation';
    metadata?: any;
  }>;
  decisions: Array<{
    id: string;
    question: string;
    options: string[];
    selectedOption?: string;
    timestamp: Date;
    impact: string;
  }>;
  context: {
    topic: string;
    phase?: string;
    relatedCharacters: string[];
    keywords: string[];
  };
}

/**
 * Phase Context - Phase-specific context and transitions
 */
export interface PhaseContext extends BaseContext {
  type: ContextType.PHASE;
  phaseId: string;
  storyId: string;
  phaseName: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'paused';
  requirements: {
    inputs: string[];
    outputs: string[];
    dependencies: string[];
  };
  agentStates: Record<string, {
    agentId: string;
    status: string;
    lastActivity: Date;
    context: any;
  }>;
  transitions: Array<{
    fromPhase: string;
    toPhase: string;
    condition: string;
    timestamp?: Date;
  }>;
  metrics: {
    startTime?: Date;
    endTime?: Date;
    duration?: number;
    iterations: number;
    qualityScore?: number;
  };
}

/**
 * Server Context - Optional in-memory session-based context (non-persistent)
 */
export interface ServerContext extends BaseContext {
  type: ContextType.SERVER;
  sessionKey: string;
  expiresAt: Date;
  data: {
    activeConnections: number;
    processingQueue: string[];
    cacheHits: number;
    cacheMisses: number;
  };
  // Note: This context type is for optional server-side in-memory caching only
  // It should never be persisted to client storage
}

/**
 * Context collection that holds all context types for a session
 */
export interface ContextCollection {
  sessionContext: SessionContext;
  storyContexts: Map<string, StoryContext>;
  characterContexts: Map<string, CharacterContext>;
  conversationContexts: Map<string, ConversationContext>;
  phaseContexts: Map<string, PhaseContext>;
  serverContext?: ServerContext; // Optional, in-memory only
}

/**
 * Context query interface for filtering and searching contexts
 */
export interface ContextQuery {
  type?: ContextType;
  storyId?: string;
  characterId?: string;
  branchId?: string;
  dateRange?: {
    start: Date;
    end: Date;
  };
  tags?: string[];
  searchText?: string;
  limit?: number;
  offset?: number;
}

/**
 * Context operation result
 */
export interface ContextOperationResult<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  warnings?: string[];
  metadata?: {
    version: number;
    timestamp: Date;
    operation: string;
  };
}
