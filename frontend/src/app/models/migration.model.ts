/**
 * Migration utilities for transitioning from ChapterCreationState to ChapterComposeState
 * Provides backward compatibility and data transformation functions
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
  OutlineItem,
  FeedbackItem,
  PhaseTransition,
  BranchNavigation
} from './story.model';

/**
 * Migration configuration and options
 */
export interface MigrationConfig {
  preserveLegacyData: boolean; // Keep original ChapterCreationState alongside new state
  createDefaultConversations: boolean; // Generate initial conversation threads
  migrateToPhase: 'plotOutline' | 'chapterDetailer' | 'finalEdit'; // Which phase to start in
  generateMissingIds: boolean; // Auto-generate IDs for legacy data
}

/**
 * Migration result with success/failure information
 */
export interface MigrationResult {
  success: boolean;
  newState?: ChapterComposeState;
  errors: string[];
  warnings: string[];
  migrationLog: Array<{
    step: string;
    status: 'success' | 'warning' | 'error';
    message: string;
    timestamp: Date;
  }>;
}

/**
 * Utility functions for migrating legacy data to new three-phase system
 */
export class ChapterComposeMigration {
  
  /**
   * Main migration function - converts ChapterCreationState to ChapterComposeState
   */
  static migrateFromLegacy(
    legacyState: ChapterCreationState,
    config: MigrationConfig = {
      preserveLegacyData: true,
      createDefaultConversations: true,
      migrateToPhase: 'chapterDetailer',
      generateMissingIds: true
    }
  ): MigrationResult {
    const result: MigrationResult = {
      success: false,
      errors: [],
      warnings: [],
      migrationLog: []
    };

    try {
      // Step 1: Create base structure
      const newState = this.createBaseChapterComposeState(config);
      this.logStep(result, 'create_base', 'success', 'Created base ChapterComposeState structure');

      // Step 2: Migrate feedback items
      const migratedFeedback = this.migrateFeedbackItems(legacyState.incorporatedFeedback || [], config);
      this.logStep(result, 'migrate_feedback', 'success', `Migrated ${migratedFeedback.length} feedback items`);

      // Step 3: Create plot outline from legacy plot point
      if (legacyState.plotPoint) {
        newState.phases.plotOutline.draftOutline = this.createOutlineFromPlotPoint(legacyState.plotPoint);
        this.logStep(result, 'create_outline', 'success', 'Created outline from legacy plot point');
      }

      // Step 4: Migrate chapter content if exists
      if (legacyState.generatedChapter) {
        this.migrateGeneratedChapter(newState, legacyState.generatedChapter, migratedFeedback);
        this.logStep(result, 'migrate_chapter', 'success', 'Migrated generated chapter content');
      }

      // Step 5: Migrate editor review if exists
      if (legacyState.editorReview) {
        newState.phases.finalEdit.editorSuggestions = legacyState.editorReview.suggestions;
        // Convert boolean array to Map
        legacyState.editorReview.userSelections.forEach((selected, index) => {
          if (legacyState.editorReview!.suggestions[index]) {
            newState.phases.finalEdit.userSelections.set(
              legacyState.editorReview!.suggestions[index].issue, 
              selected
            );
          }
        });
        this.logStep(result, 'migrate_editor_review', 'success', 'Migrated editor review data');
      }

      // Step 6: Set appropriate phase and status
      this.setMigrationPhaseAndStatus(newState, legacyState, config);
      this.logStep(result, 'set_phase', 'success', `Set current phase to ${newState.currentPhase}`);

      result.success = true;
      result.newState = newState;

    } catch (error) {
      result.errors.push(`Migration failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      this.logStep(result, 'migration', 'error', `Migration failed: ${error}`);
    }

    return result;
  }

  /**
   * Creates a base ChapterComposeState with default values
   */
  private static createBaseChapterComposeState(config: MigrationConfig): ChapterComposeState {
    const now = new Date();
    const baseId = this.generateId();

    return {
      currentPhase: config.migrateToPhase,
      phases: {
        plotOutline: this.createDefaultPlotOutlinePhase(baseId + '_plot'),
        chapterDetailer: this.createDefaultChapterDetailerPhase(baseId + '_detailer'),
        finalEdit: this.createDefaultFinalEditPhase(baseId + '_final')
      },
      phaseTransitions: {
        toChapterDetailer: this.createDefaultPhaseTransition('plotOutline', 'chapterDetailer'),
        toFinalEdit: this.createDefaultPhaseTransition('chapterDetailer', 'finalEdit')
      },
      branchNavigation: {
        currentBranchId: 'main',
        availableBranches: ['main'],
        branchHistory: ['main'],
        canCreateBranch: true,
        canMergeBranches: false
      },
      sharedContext: {
        chapterNumber: 1,
        selectedCharacters: [],
        selectedRaters: [],
        globalNotes: ''
      },
      progress: {
        overallStatus: 'in_progress',
        completedPhases: [],
        currentPhaseProgress: 0
      },
      metadata: {
        created: now,
        lastModified: now,
        version: '1.0.0',
        totalTimeSpent: 0,
        sessionCount: 1,
        lastSessionAt: now
      }
    };
  }

  /**
   * Creates a default conversation thread
   */
  private static createDefaultConversationThread(id: string, title: string): ConversationThread {
    const now = new Date();
    const rootMessageId = this.generateId();
    const branchId = 'main';

    const rootMessage: ChatMessage = {
      id: rootMessageId,
      content: 'Starting chapter composition...',
      role: 'system',
      timestamp: now,
      branchId: branchId,
      metadata: {
        messageType: 'text',
        source: 'system',
        isEdited: false
      }
    };

    const mainBranch: ConversationBranch = {
      id: branchId,
      name: 'Main',
      branchPointMessageId: rootMessageId,
      isActive: true,
      created: now,
      lastModified: now
    };

    return {
      id,
      title,
      messages: new Map([[rootMessageId, rootMessage]]),
      branches: new Map([[branchId, mainBranch]]),
      currentBranchId: branchId,
      rootMessageId: rootMessageId,
      metadata: {
        created: now,
        lastModified: now,
        totalMessages: 1,
        totalBranches: 1
      }
    };
  }

  /**
   * Migrates legacy feedback items to new enhanced format
   */
  private static migrateFeedbackItems(legacyFeedback: FeedbackItem[], config: MigrationConfig): FeedbackItem[] {
    return legacyFeedback.map(item => ({
      id: config.generateMissingIds ? this.generateId() : (item.id || this.generateId()),
      source: item.source,
      type: item.type,
      content: item.content,
      incorporated: item.incorporated,
      phase: item.phase || 'chapterDetailer', // Use existing phase or default to chapterDetailer
      priority: item.priority || 'medium', // Use existing priority or default to medium
      targetSection: item.targetSection,
      metadata: item.metadata || {
        created: new Date(),
        relatedMessageId: undefined
      }
    }));
  }

  /**
   * Creates outline items from legacy plot point
   */
  private static createOutlineFromPlotPoint(plotPoint: string): OutlineItem[] {
    return [{
      id: this.generateId(),
      order: 1,
      title: 'Main Plot Point',
      description: plotPoint,
      type: 'scene',
      characterInvolvement: [],
      plotRelevance: 'high',
      metadata: {
        created: new Date(),
        lastModified: new Date(),
        source: 'user'
      }
    }];
  }

  /**
   * Helper methods for creating default phase states
   */
  private static createDefaultPlotOutlinePhase(id: string): PlotOutlinePhase {
    return {
      conversation: this.createDefaultConversationThread(id, 'Plot Outline Discussion'),
      draftOutline: [],
      outlineHistory: [],
      feedbackIntegration: {
        pendingFeedback: [],
        integratedFeedback: [],
        feedbackSources: []
      },
      status: 'draft',
      metadata: {
        startedAt: new Date(),
        lastModified: new Date(),
        iterationCount: 0
      }
    };
  }

  private static createDefaultChapterDetailerPhase(id: string): ChapterDetailerPhase {
    return {
      conversation: this.createDefaultConversationThread(id, 'Chapter Development'),
      chapterDrafts: [],
      sidebarFeedback: {
        characterFeedback: new Map(),
        raterFeedback: new Map(),
        feedbackStatus: new Map()
      },
      status: 'drafting',
      metadata: {
        startedAt: new Date(),
        lastModified: new Date(),
        draftCount: 0,
        feedbackRounds: 0
      }
    };
  }

  private static createDefaultFinalEditPhase(id: string): FinalEditPhase {
    return {
      conversation: this.createDefaultConversationThread(id, 'Final Review'),
      finalDrafts: [],
      reviewItems: [],
      editorSuggestions: [],
      userSelections: new Map(),
      status: 'reviewing',
      metadata: {
        startedAt: new Date(),
        lastModified: new Date(),
        reviewRounds: 0
      }
    };
  }

  private static createDefaultPhaseTransition(from: string, to: string): PhaseTransition {
    return {
      fromPhase: from as any,
      toPhase: to as any,
      canTransition: false,
      requirements: [
        {
          requirement: `Complete ${from} phase`,
          satisfied: false,
          description: `The ${from} phase must be completed before transitioning to ${to}`
        }
      ],
      metadata: {
        lastChecked: new Date()
      }
    };
  }

  private static migrateGeneratedChapter(
    newState: ChapterComposeState, 
    generatedChapter: any, 
    migratedFeedback: FeedbackItem[]
  ): void {
    // Add to chapter detailer phase
    newState.phases.chapterDetailer.chapterDrafts.push({
      id: this.generateId(),
      content: generatedChapter.text,
      version: 1,
      timestamp: new Date(),
      incorporatedFeedback: migratedFeedback
    });

    // Also add to final edit phase
    newState.phases.finalEdit.finalDrafts.push({
      id: this.generateId(),
      content: generatedChapter.text,
      title: 'Migrated Chapter',
      source: 'phase2_output',
      timestamp: new Date()
    });
  }

  private static setMigrationPhaseAndStatus(
    newState: ChapterComposeState, 
    legacyState: ChapterCreationState, 
    config: MigrationConfig
  ): void {
    // Determine appropriate phase based on legacy state
    if (legacyState.generatedChapter && legacyState.editorReview) {
      newState.currentPhase = 'finalEdit';
      newState.progress.completedPhases = ['plotOutline', 'chapterDetailer'];
    } else if (legacyState.generatedChapter) {
      newState.currentPhase = 'chapterDetailer';
      newState.progress.completedPhases = ['plotOutline'];
    } else {
      newState.currentPhase = config.migrateToPhase;
    }
  }

  private static generateId(): string {
    return 'migrated_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  private static logStep(
    result: MigrationResult, 
    step: string, 
    status: 'success' | 'warning' | 'error', 
    message: string
  ): void {
    result.migrationLog.push({
      step,
      status,
      message,
      timestamp: new Date()
    });
  }
}

/**
 * Validation utilities for ChapterComposeState
 */
export class ChapterComposeValidator {
  
  /**
   * Validates a ChapterComposeState for consistency and completeness
   */
  static validate(state: ChapterComposeState): {
    isValid: boolean;
    errors: string[];
    warnings: string[];
  } {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Validate phase consistency
    if (!state.phases[state.currentPhase]) {
      errors.push(`Current phase '${state.currentPhase}' does not exist in phases object`);
    }

    // Validate conversation threads
    Object.values(state.phases).forEach((phase, index) => {
      const phaseName = ['plotOutline', 'chapterDetailer', 'finalEdit'][index];
      if (!phase.conversation.messages.has(phase.conversation.rootMessageId)) {
        errors.push(`${phaseName} phase: Root message not found in messages map`);
      }
    });

    // Validate branch navigation
    if (!state.phases[state.currentPhase].conversation.branches.has(state.branchNavigation.currentBranchId)) {
      errors.push(`Current branch '${state.branchNavigation.currentBranchId}' not found in current phase`);
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }
}
