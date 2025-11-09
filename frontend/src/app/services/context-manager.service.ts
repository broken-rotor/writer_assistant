import { Injectable, inject } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import {
  BaseContext,
  ContextType,
  ContextCollection,
  SessionContext,
  StoryContext,
  CharacterContext,
  ConversationContext,
  ServerContext,
  ContextQuery,
  ContextOperationResult,
  ContextMetadata,
  ContextBranch
} from '../models/context.model';
import { ContextStorageService } from './context-storage.service';

/**
 * Context Manager Service - Central hub for all context state management
 * Orchestrates context operations, versioning, branching, and provides unified API
 */
@Injectable({
  providedIn: 'root'
})
export class ContextManagerService {
  private contextStorageService = inject(ContextStorageService);

  // Active context collection
  private contextCollectionSubject = new BehaviorSubject<ContextCollection>({
    sessionContext: this.createDefaultSessionContext(),
    storyContexts: new Map(),
    characterContexts: new Map(),
    conversationContexts: new Map()
  });

  // Current active context IDs
  private activeContextsSubject = new BehaviorSubject<{
    sessionId?: string;
    storyId?: string;
    characterId?: string;
    conversationId?: string;
  }>({});

  public contextCollection$ = this.contextCollectionSubject.asObservable();
  public activeContexts$ = this.activeContextsSubject.asObservable();

  constructor() {
    this.initializeContextManager();
  }

  /**
   * Initialize the context manager
   */
  private async initializeContextManager(): Promise<void> {
    try {
      // Load existing session context or create new one
      await this.loadOrCreateSessionContext();
      
      // Load active contexts based on session state
      await this.loadActiveContexts();
      
      console.log('Context manager initialized successfully');
    } catch (error) {
      console.error('Failed to initialize context manager:', error);
    }
  }

  /**
   * Create a new context of the specified type
   */
  async createContext<T extends BaseContext>(
    contextType: ContextType,
    initialData: Partial<T>
  ): Promise<ContextOperationResult<T>> {
    try {
      const contextId = this.generateContextId();
      const now = new Date();

      const metadata: ContextMetadata = {
        id: contextId,
        version: 1,
        createdAt: now,
        updatedAt: now,
        branchId: 'main'
      };

      const mainBranch: ContextBranch = {
        id: 'main',
        name: 'Main',
        createdAt: now,
        lastActiveAt: now,
        isActive: true
      };

      const baseContext: BaseContext = {
        id: contextId,
        type: contextType,
        metadata,
        branches: [mainBranch],
        currentBranchId: 'main'
      };

      const context = { ...baseContext, ...initialData } as T;

      // Save to storage
      const saveResult = await this.contextStorageService.saveContext(context);
      if (!saveResult.success) {
        return saveResult;
      }

      // Update in-memory collection
      this.addContextToCollection(context);

      return {
        success: true,
        data: context,
        metadata: {
          version: 1,
          timestamp: now,
          operation: 'create'
        }
      };
    } catch (error) {
      console.error('Failed to create context:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  /**
   * Load a context by ID and type
   */
  async loadContext<T extends BaseContext>(
    contextId: string,
    contextType: ContextType
  ): Promise<ContextOperationResult<T>> {
    try {
      const loadResult = await this.contextStorageService.loadContext<T>(contextId, contextType);
      
      if (loadResult.success && loadResult.data) {
        // Update in-memory collection
        this.addContextToCollection(loadResult.data);
      }

      return loadResult;
    } catch (error) {
      console.error('Failed to load context:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  /**
   * Update an existing context
   */
  async updateContext<T extends BaseContext>(
    contextId: string,
    contextType: ContextType,
    updates: Partial<T>
  ): Promise<ContextOperationResult<T>> {
    try {
      // Load current context
      const loadResult = await this.loadContext<T>(contextId, contextType);
      if (!loadResult.success || !loadResult.data) {
        return {
          success: false,
          error: 'Context not found'
        };
      }

      const currentContext = loadResult.data;
      const now = new Date();

      // Create updated context
      const updatedContext: T = {
        ...currentContext,
        ...updates,
        metadata: {
          ...currentContext.metadata,
          version: currentContext.metadata.version + 1,
          updatedAt: now
        }
      };

      // Save to storage
      const saveResult = await this.contextStorageService.saveContext(updatedContext);
      if (!saveResult.success) {
        return saveResult;
      }

      // Update in-memory collection
      this.addContextToCollection(updatedContext);

      return {
        success: true,
        data: updatedContext,
        metadata: {
          version: updatedContext.metadata.version,
          timestamp: now,
          operation: 'update'
        }
      };
    } catch (error) {
      console.error('Failed to update context:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  /**
   * Delete a context
   */
  async deleteContext(contextId: string, contextType: ContextType): Promise<ContextOperationResult<void>> {
    try {
      // Remove from storage
      const deleteResult = await this.contextStorageService.deleteContext(contextId, contextType);
      
      if (deleteResult.success) {
        // Remove from in-memory collection
        this.removeContextFromCollection(contextId, contextType);
      }

      return deleteResult;
    } catch (error) {
      console.error('Failed to delete context:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  /**
   * Query contexts based on criteria
   */
  async queryContexts(query: ContextQuery): Promise<ContextOperationResult<BaseContext[]>> {
    try {
      const listResult = await this.contextStorageService.listContexts(query.type);
      if (!listResult.success || !listResult.data) {
        return {
          success: false,
          error: 'Failed to retrieve contexts'
        };
      }

      // Load contexts based on metadata
      const contexts: BaseContext[] = [];
      for (const metadata of listResult.data) {
        const loadResult = await this.loadContext(metadata.contextId, metadata.contextType);
        if (loadResult.success && loadResult.data) {
          contexts.push(loadResult.data);
        }
      }

      // Apply additional filtering
      let filteredContexts = contexts;

      if (query.storyId) {
        filteredContexts = filteredContexts.filter(ctx => 
          'storyId' in ctx && (ctx as any).storyId === query.storyId
        );
      }

      if (query.characterId) {
        filteredContexts = filteredContexts.filter(ctx => 
          'characterId' in ctx && (ctx as any).characterId === query.characterId
        );
      }

      if (query.branchId) {
        filteredContexts = filteredContexts.filter(ctx => 
          ctx.currentBranchId === query.branchId
        );
      }

      if (query.dateRange) {
        filteredContexts = filteredContexts.filter(ctx => 
          ctx.metadata.createdAt >= query.dateRange!.start &&
          ctx.metadata.createdAt <= query.dateRange!.end
        );
      }

      if (query.tags && query.tags.length > 0) {
        filteredContexts = filteredContexts.filter(ctx => 
          ctx.metadata.tags && 
          query.tags!.some(tag => ctx.metadata.tags!.includes(tag))
        );
      }

      // Apply pagination
      if (query.offset || query.limit) {
        const offset = query.offset || 0;
        const limit = query.limit || filteredContexts.length;
        filteredContexts = filteredContexts.slice(offset, offset + limit);
      }

      return {
        success: true,
        data: filteredContexts,
        metadata: {
          version: 0,
          timestamp: new Date(),
          operation: 'query'
        }
      };
    } catch (error) {
      console.error('Failed to query contexts:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  /**
   * Set active context for a specific type
   */
  async setActiveContext(contextId: string, contextType: ContextType): Promise<void> {
    try {
      const currentActive = this.activeContextsSubject.value;
      const updatedActive = { ...currentActive };

      switch (contextType) {
        case ContextType.SESSION:
          updatedActive.sessionId = contextId;
          break;
        case ContextType.STORY:
          updatedActive.storyId = contextId;
          break;
        case ContextType.CHARACTER:
          updatedActive.characterId = contextId;
          break;
        case ContextType.CONVERSATION:
          updatedActive.conversationId = contextId;
          break;
      }

      this.activeContextsSubject.next(updatedActive);

      // Update session context with active context info
      if (contextType !== ContextType.SESSION) {
        await this.updateSessionContextActiveIds(updatedActive);
      }
    } catch (error) {
      console.error('Failed to set active context:', error);
    }
  }

  /**
   * Get current context collection
   */
  getCurrentContextCollection(): ContextCollection {
    return this.contextCollectionSubject.value;
  }

  /**
   * Get active context of specific type
   */
  getActiveContext<T extends BaseContext>(contextType: ContextType): T | null {
    const collection = this.getCurrentContextCollection();
    const activeIds = this.activeContextsSubject.value;

    switch (contextType) {
      case ContextType.SESSION:
        return collection.sessionContext as unknown as T;
      case ContextType.STORY:
        return activeIds.storyId ? 
          (collection.storyContexts.get(activeIds.storyId) as unknown as T) || null : null;
      case ContextType.CHARACTER:
        return activeIds.characterId ? 
          (collection.characterContexts.get(activeIds.characterId) as unknown as T) || null : null;
      case ContextType.CONVERSATION:
        return activeIds.conversationId ?
          (collection.conversationContexts.get(activeIds.conversationId) as unknown as T) || null : null;
      default:
        return null;
    }
  }

  /**
   * Create default session context
   */
  private createDefaultSessionContext(): SessionContext {
    const now = new Date();
    const sessionId = this.generateContextId();

    return {
      id: sessionId,
      type: ContextType.SESSION,
      sessionId,
      metadata: {
        id: sessionId,
        version: 1,
        createdAt: now,
        updatedAt: now,
        branchId: 'main'
      },
      branches: [{
        id: 'main',
        name: 'Main',
        createdAt: now,
        lastActiveAt: now,
        isActive: true
      }],
      currentBranchId: 'main',
      userPreferences: {
        autoSave: true,
        contextRetention: 90,
        maxBranches: 5
      },
      workspaceState: {
        openTabs: [],
        sidebarState: {},
        viewMode: 'default'
      },
      recentActions: []
    };
  }

  /**
   * Load or create session context
   */
  private async loadOrCreateSessionContext(): Promise<void> {
    try {
      // Try to load existing session context
      const sessionId = localStorage.getItem('writer_assistant_current_session');
      
      if (sessionId) {
        const loadResult = await this.loadContext<SessionContext>(sessionId, ContextType.SESSION);
        if (loadResult.success && loadResult.data) {
          const collection = this.contextCollectionSubject.value;
          collection.sessionContext = loadResult.data;
          this.contextCollectionSubject.next(collection);
          return;
        }
      }

      // Create new session context
      const sessionContext = this.createDefaultSessionContext();
      await this.contextStorageService.saveContext(sessionContext);
      
      const collection = this.contextCollectionSubject.value;
      collection.sessionContext = sessionContext;
      this.contextCollectionSubject.next(collection);

      // Store session ID
      localStorage.setItem('writer_assistant_current_session', sessionContext.sessionId);
    } catch (error) {
      console.error('Failed to load or create session context:', error);
    }
  }

  /**
   * Load active contexts based on session state
   */
  private async loadActiveContexts(): Promise<void> {
    try {
      const sessionContext = this.getCurrentContextCollection().sessionContext;
      
      // Load active story context if specified
      if (sessionContext.storyId) {
        await this.loadContext(sessionContext.storyId, ContextType.STORY);
        this.setActiveContext(sessionContext.storyId, ContextType.STORY);
      }

      // Load other active contexts as needed
      // This could be extended based on session state
    } catch (error) {
      console.error('Failed to load active contexts:', error);
    }
  }

  /**
   * Add context to in-memory collection
   */
  private addContextToCollection(context: BaseContext): void {
    const collection = this.contextCollectionSubject.value;

    switch (context.type) {
      case ContextType.SESSION:
        collection.sessionContext = context as SessionContext;
        break;
      case ContextType.STORY:
        collection.storyContexts.set(context.id, context as StoryContext);
        break;
      case ContextType.CHARACTER:
        collection.characterContexts.set(context.id, context as CharacterContext);
        break;
      case ContextType.CONVERSATION:
        collection.conversationContexts.set(context.id, context as ConversationContext);
        break;
      case ContextType.SERVER:
        collection.serverContext = context as ServerContext;
        break;
    }

    this.contextCollectionSubject.next(collection);
  }

  /**
   * Remove context from in-memory collection
   */
  private removeContextFromCollection(contextId: string, contextType: ContextType): void {
    const collection = this.contextCollectionSubject.value;

    switch (contextType) {
      case ContextType.STORY:
        collection.storyContexts.delete(contextId);
        break;
      case ContextType.CHARACTER:
        collection.characterContexts.delete(contextId);
        break;
      case ContextType.CONVERSATION:
        collection.conversationContexts.delete(contextId);
        break;
      case ContextType.SERVER:
        collection.serverContext = undefined;
        break;
    }

    this.contextCollectionSubject.next(collection);
  }

  /**
   * Update session context with active context IDs
   */
  private async updateSessionContextActiveIds(activeIds: any): Promise<void> {
    try {
      const sessionContext = this.getCurrentContextCollection().sessionContext;

      const updates: Partial<SessionContext> = {
        storyId: activeIds.storyId
      };

      await this.updateContext(sessionContext.id, ContextType.SESSION, updates);
    } catch (error) {
      console.error('Failed to update session context active IDs:', error);
    }
  }

  /**
   * Generate unique context ID
   */
  private generateContextId(): string {
    return `ctx_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get storage statistics
   */
  getStorageStats(): Observable<any> {
    return this.contextStorageService.storageStats$;
  }
}
