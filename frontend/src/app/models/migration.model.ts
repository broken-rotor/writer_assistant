/**
 * Migration utilities and interfaces for transitioning from ChapterCreationState 
 * to the new three-phase ChapterComposeState system
 */

import { 
  ChapterCreationState, 
  ChapterComposeState, 
  PlotOutlinePhase, 
  ChapterDetailerPhase, 
  FinalEditPhase,
  ConversationThread,
  ChatMessage,
  ConversationBranch,
  BranchNavigation,
  EnhancedFeedbackItem,
  FeedbackItem
} from './story.model';

/**
 * Migration configuration and options
 */
export interface MigrationConfig {
  preserveLegacyData: boolean;
  createBackup: boolean;
  validateAfterMigration: boolean;
  migrationStrategy: 'immediate' | 'gradual' | 'on-demand';
  fallbackToLegacy: boolean;
}

/**
 * Migration result with status and details
 */
export interface MigrationResult {
  success: boolean;
  migratedData?: ChapterComposeState;
  errors: string[];
  warnings: string[];
  backupCreated: boolean;
  migrationTimestamp: Date;
  dataIntegrityChecks: {
    feedbackItemsPreserved: boolean;
    plotPointPreserved: boolean;
    editorReviewPreserved: boolean;
    generatedChapterPreserved: boolean;
  };
}

/**
 * Validation result for migration data
 */
export interface MigrationValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  missingRequiredFields: string[];
  dataInconsistencies: string[];
}

/**
 * Migration adapter interface for different migration strategies
 */
export interface MigrationAdapter {
  canMigrate(legacyState: ChapterCreationState): boolean;
  migrate(legacyState: ChapterCreationState, config: MigrationConfig): Promise<MigrationResult>;
  validate(migratedState: ChapterComposeState): MigrationValidationResult;
  rollback(backupData: ChapterCreationState): Promise<boolean>;
}

/**
 * Default migration adapter implementation
 */
export interface DefaultMigrationAdapter extends MigrationAdapter {
  // Conversion utilities
  convertFeedbackItems(legacyFeedback: FeedbackItem[]): EnhancedFeedbackItem[];
  createInitialConversation(plotPoint: string): ConversationThread;
  createDefaultBranchNavigation(): BranchNavigation;
  
  // Phase initialization
  initializePlotOutlinePhase(plotPoint: string): PlotOutlinePhase;
  initializeChapterDetailerPhase(legacyState: ChapterCreationState): ChapterDetailerPhase;
  initializeFinalEditPhase(legacyState: ChapterCreationState): FinalEditPhase;
}

/**
 * Migration context for tracking migration state
 */
export interface MigrationContext {
  storyId: string;
  migrationId: string;
  startTime: Date;
  currentStep: string;
  totalSteps: number;
  completedSteps: number;
  errors: string[];
  warnings: string[];
  rollbackData?: ChapterCreationState;
}

/**
 * Migration event for tracking migration progress
 */
export interface MigrationEvent {
  type: 'started' | 'progress' | 'completed' | 'failed' | 'rolled-back';
  timestamp: Date;
  context: MigrationContext;
  message: string;
  data?: any;
}

/**
 * Migration service interface
 */
export interface MigrationService {
  // Core migration operations
  migrateStory(storyId: string, config?: MigrationConfig): Promise<MigrationResult>;
  validateMigration(storyId: string): Promise<MigrationValidationResult>;
  rollbackMigration(storyId: string): Promise<boolean>;
  
  // Migration status and monitoring
  getMigrationStatus(storyId: string): 'not-started' | 'in-progress' | 'completed' | 'failed';
  getMigrationHistory(storyId: string): MigrationEvent[];
  
  // Batch operations
  migrateBatch(storyIds: string[], config?: MigrationConfig): Promise<Map<string, MigrationResult>>;
  
  // Utility methods
  canMigrateStory(storyId: string): boolean;
  estimateMigrationTime(storyId: string): number; // in milliseconds
  createMigrationBackup(storyId: string): Promise<boolean>;
}

/**
 * Migration utilities for data transformation
 */
export interface MigrationUtils {
  // ID generation
  generateConversationId(): string;
  generateMessageId(): string;
  generateBranchId(): string;
  
  // Data validation
  validateLegacyState(state: ChapterCreationState): boolean;
  validateMigratedState(state: ChapterComposeState): boolean;
  
  // Data transformation
  transformFeedbackRequests(
    legacyRequests: Map<string, any>
  ): Map<string, any>;
  
  createInitialChatMessage(
    plotPoint: string, 
    phase: 'plot-outline' | 'chapter-detailer' | 'final-edit'
  ): ChatMessage;
  
  // Compatibility checks
  isLegacyStateComplete(state: ChapterCreationState): boolean;
  requiresManualIntervention(state: ChapterCreationState): boolean;
  
  // Error handling
  createMigrationError(message: string, context?: any): Error;
  logMigrationWarning(message: string, context?: any): void;
}

/**
 * Migration constants and defaults
 */
export const MIGRATION_CONSTANTS = {
  DEFAULT_CONFIG: {
    preserveLegacyData: true,
    createBackup: true,
    validateAfterMigration: true,
    migrationStrategy: 'gradual' as const,
    fallbackToLegacy: true
  },
  
  PHASE_NAMES: {
    PLOT_OUTLINE: 'plot-outline' as const,
    CHAPTER_DETAILER: 'chapter-detailer' as const,
    FINAL_EDIT: 'final-edit' as const
  },
  
  MESSAGE_TYPES: {
    USER: 'user' as const,
    ASSISTANT: 'assistant' as const,
    SYSTEM: 'system' as const
  },
  
  MIGRATION_VERSION: '1.0.0',
  
  MAX_MIGRATION_RETRIES: 3,
  MIGRATION_TIMEOUT_MS: 30000,
  
  VALIDATION_RULES: {
    REQUIRED_FIELDS: [
      'currentPhase',
      'phases',
      'sharedContext',
      'navigation',
      'overallProgress',
      'metadata'
    ],
    
    PHASE_REQUIRED_FIELDS: {
      'plot-outline': ['conversation', 'outline', 'draftSummary', 'status', 'progress'],
      'chapter-detailer': ['conversation', 'chapterDraft', 'feedbackIntegration', 'status', 'progress'],
      'final-edit': ['conversation', 'finalChapter', 'reviewSelection', 'status', 'progress']
    }
  }
} as const;

/**
 * Type guards for migration data
 */
export const MigrationTypeGuards = {
  isChapterCreationState(obj: any): obj is ChapterCreationState {
    return obj && 
           typeof obj.plotPoint === 'string' &&
           Array.isArray(obj.incorporatedFeedback) &&
           obj.feedbackRequests instanceof Map;
  },
  
  isChapterComposeState(obj: any): obj is ChapterComposeState {
    return obj &&
           typeof obj.currentPhase === 'string' &&
           obj.phases &&
           obj.sharedContext &&
           obj.navigation &&
           obj.overallProgress &&
           obj.metadata;
  },
  
  isMigrationResult(obj: any): obj is MigrationResult {
    return obj &&
           typeof obj.success === 'boolean' &&
           Array.isArray(obj.errors) &&
           Array.isArray(obj.warnings) &&
           obj.migrationTimestamp instanceof Date;
  }
} as const;
