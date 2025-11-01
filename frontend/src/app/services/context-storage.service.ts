import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { 
  BaseContext, 
  ContextType, 
  ContextVersion, 
  ContextOperationResult 
} from '../models/context.model';
import {
  ContextStorageConfig,
  ContextStorageMetadata,
  ContextStorageStats,
  ContextCleanupPolicy
} from '../models/context-state.model';

/**
 * Context Storage Service - Specialized persistence layer for context data
 * Handles storage operations using localStorage, sessionStorage, and IndexedDB
 */
@Injectable({
  providedIn: 'root'
})
export class ContextStorageService {
  private readonly STORAGE_PREFIX = 'writer_assistant_context_';
  private readonly METADATA_KEY = `${this.STORAGE_PREFIX}metadata`;
  private readonly CONFIG_KEY = `${this.STORAGE_PREFIX}config`;
  
  private storageStatsSubject = new BehaviorSubject<ContextStorageStats>({
    totalContexts: 0,
    totalSize: 0,
    storageUsed: 0,
    contextsByType: {} as Record<ContextType, number>,
    oldestContext: new Date(),
    newestContext: new Date(),
    averageSize: 0
  });

  public storageStats$ = this.storageStatsSubject.asObservable();

  private defaultStorageConfigs: Record<ContextType, ContextStorageConfig> = {
    [ContextType.SESSION]: {
      type: ContextType.SESSION,
      storageType: 'sessionStorage',
      maxVersions: 10,
      maxBranches: 3,
      compressionEnabled: false,
      encryptionEnabled: false,
      retentionDays: 1
    },
    [ContextType.STORY]: {
      type: ContextType.STORY,
      storageType: 'localStorage',
      maxVersions: 50,
      maxBranches: 10,
      compressionEnabled: true,
      encryptionEnabled: false,
      retentionDays: 365
    },
    [ContextType.CHARACTER]: {
      type: ContextType.CHARACTER,
      storageType: 'localStorage',
      maxVersions: 30,
      maxBranches: 5,
      compressionEnabled: true,
      encryptionEnabled: false,
      retentionDays: 365
    },
    [ContextType.CONVERSATION]: {
      type: ContextType.CONVERSATION,
      storageType: 'localStorage',
      maxVersions: 20,
      maxBranches: 3,
      compressionEnabled: true,
      encryptionEnabled: false,
      retentionDays: 90
    },
    [ContextType.PHASE]: {
      type: ContextType.PHASE,
      storageType: 'localStorage',
      maxVersions: 15,
      maxBranches: 3,
      compressionEnabled: false,
      encryptionEnabled: false,
      retentionDays: 180
    },
    [ContextType.SERVER]: {
      type: ContextType.SERVER,
      storageType: 'sessionStorage', // Never persisted
      maxVersions: 1,
      maxBranches: 1,
      compressionEnabled: false,
      encryptionEnabled: false,
      retentionDays: 0
    }
  };

  private defaultCleanupPolicy: ContextCleanupPolicy = {
    enabled: true,
    maxAge: 90, // days
    maxSize: 50 * 1024 * 1024, // 50MB
    maxVersionsPerContext: 20,
    maxBranchesPerContext: 5,
    cleanupFrequency: 24, // hours
    preserveActive: true,
    preserveTagged: ['important', 'bookmark', 'milestone']
  };

  constructor() {
    this.initializeStorage();
    this.updateStorageStats();
  }

  /**
   * Initialize storage with default configurations
   */
  private initializeStorage(): void {
    try {
      const existingConfig = this.getStorageConfigs();
      if (!existingConfig || Object.keys(existingConfig).length === 0) {
        this.saveStorageConfigs(this.defaultStorageConfigs);
      }

      const existingPolicy = this.getCleanupPolicy();
      if (!existingPolicy) {
        this.saveCleanupPolicy(this.defaultCleanupPolicy);
      }
    } catch (error) {
      console.error('Failed to initialize context storage:', error);
    }
  }

  /**
   * Save a context to storage
   */
  async saveContext<T extends BaseContext>(context: T): Promise<ContextOperationResult<T>> {
    try {
      const config = this.getStorageConfig(context.type);
      const storageKey = this.getContextStorageKey(context.id, context.type);
      
      // Prepare data for storage
      const contextData = this.prepareForStorage(context, config);
      const serializedData = JSON.stringify(contextData);
      
      // Calculate size and validate storage limits
      const dataSize = new Blob([serializedData]).size;
      const canStore = await this.validateStorageCapacity(dataSize);
      
      if (!canStore) {
        return {
          success: false,
          error: 'Insufficient storage capacity',
          warnings: ['Consider cleaning up old contexts or reducing data size']
        };
      }

      // Store the data
      const storage = this.getStorageInterface(config.storageType);
      storage.setItem(storageKey, serializedData);

      // Update metadata
      await this.updateContextMetadata(context.id, context.type, dataSize);
      
      // Update statistics
      this.updateStorageStats();

      return {
        success: true,
        data: context,
        metadata: {
          version: context.metadata.version,
          timestamp: new Date(),
          operation: 'save'
        }
      };
    } catch (error) {
      console.error('Failed to save context:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  /**
   * Load a context from storage
   */
  async loadContext<T extends BaseContext>(
    contextId: string, 
    contextType: ContextType
  ): Promise<ContextOperationResult<T>> {
    try {
      const config = this.getStorageConfig(contextType);
      const storageKey = this.getContextStorageKey(contextId, contextType);
      const storage = this.getStorageInterface(config.storageType);
      
      const serializedData = storage.getItem(storageKey);
      if (!serializedData) {
        return {
          success: false,
          error: 'Context not found'
        };
      }

      const contextData = JSON.parse(serializedData);
      const context = this.restoreFromStorage<T>(contextData, config);

      // Update access metadata
      await this.updateContextAccess(contextId, contextType);

      return {
        success: true,
        data: context,
        metadata: {
          version: context.metadata.version,
          timestamp: new Date(),
          operation: 'load'
        }
      };
    } catch (error) {
      console.error('Failed to load context:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to parse context data'
      };
    }
  }

  /**
   * Delete a context from storage
   */
  async deleteContext(contextId: string, contextType: ContextType): Promise<ContextOperationResult<void>> {
    try {
      const config = this.getStorageConfig(contextType);
      const storageKey = this.getContextStorageKey(contextId, contextType);
      const storage = this.getStorageInterface(config.storageType);
      
      // Remove the context data
      storage.removeItem(storageKey);
      
      // Remove metadata
      await this.removeContextMetadata(contextId, contextType);
      
      // Update statistics
      this.updateStorageStats();

      return {
        success: true,
        metadata: {
          version: 0,
          timestamp: new Date(),
          operation: 'delete'
        }
      };
    } catch (error) {
      console.error('Failed to delete context:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  /**
   * List all contexts of a specific type
   */
  async listContexts(contextType?: ContextType): Promise<ContextOperationResult<ContextStorageMetadata[]>> {
    try {
      const allMetadata = this.getAllContextMetadata();
      const filteredMetadata = contextType 
        ? allMetadata.filter(meta => meta.contextType === contextType)
        : allMetadata;

      return {
        success: true,
        data: filteredMetadata,
        metadata: {
          version: 0,
          timestamp: new Date(),
          operation: 'list'
        }
      };
    } catch (error) {
      console.error('Failed to list contexts:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  /**
   * Get storage statistics
   */
  getStorageStats(): ContextStorageStats {
    return this.storageStatsSubject.value;
  }

  /**
   * Update storage statistics
   */
  private updateStorageStats(): void {
    try {
      const metadata = this.getAllContextMetadata();
      const totalSize = metadata.reduce((sum, meta) => sum + meta.size, 0);
      const contextsByType = metadata.reduce((acc, meta) => {
        acc[meta.contextType] = (acc[meta.contextType] || 0) + 1;
        return acc;
      }, {} as Record<ContextType, number>);

      const dates = metadata.map(meta => meta.lastAccessed);
      const oldestContext = dates.length > 0 ? new Date(Math.min(...dates.map(d => d.getTime()))) : new Date();
      const newestContext = dates.length > 0 ? new Date(Math.max(...dates.map(d => d.getTime()))) : new Date();

      // Estimate storage usage (localStorage typically has ~5-10MB limit)
      const estimatedLimit = 10 * 1024 * 1024; // 10MB
      const storageUsed = (totalSize / estimatedLimit) * 100;

      const stats: ContextStorageStats = {
        totalContexts: metadata.length,
        totalSize,
        storageUsed: Math.min(storageUsed, 100),
        contextsByType,
        oldestContext,
        newestContext,
        averageSize: metadata.length > 0 ? totalSize / metadata.length : 0
      };

      this.storageStatsSubject.next(stats);
    } catch (error) {
      console.error('Failed to update storage stats:', error);
    }
  }

  /**
   * Prepare context data for storage (compression, encryption, etc.)
   */
  private prepareForStorage<T extends BaseContext>(context: T, config: ContextStorageConfig): any {
    let data = { ...context };

    // Convert Date objects to ISO strings for JSON serialization
    data = this.serializeDates(data);

    // Apply compression if enabled
    if (config.compressionEnabled) {
      // Simple compression placeholder - could implement LZ-string or similar
      data = this.compressData(data);
    }

    // Apply encryption if enabled
    if (config.encryptionEnabled) {
      data = this.encryptData(data);
    }

    return data;
  }

  /**
   * Restore context data from storage (decompression, decryption, etc.)
   */
  private restoreFromStorage<T extends BaseContext>(data: any, config: ContextStorageConfig): T {
    let contextData = data;

    // Apply decryption if enabled
    if (config.encryptionEnabled) {
      contextData = this.decryptData(contextData);
    }

    // Apply decompression if enabled
    if (config.compressionEnabled) {
      contextData = this.decompressData(contextData);
    }

    // Convert ISO strings back to Date objects
    contextData = this.deserializeDates(contextData);

    return contextData as T;
  }

  /**
   * Serialize Date objects to ISO strings
   */
  private serializeDates(obj: any): any {
    if (obj instanceof Date) {
      return obj.toISOString();
    }
    if (Array.isArray(obj)) {
      return obj.map(item => this.serializeDates(item));
    }
    if (obj && typeof obj === 'object') {
      const serialized: any = {};
      for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
          serialized[key] = this.serializeDates(obj[key]);
        }
      }
      return serialized;
    }
    return obj;
  }

  /**
   * Deserialize ISO strings back to Date objects
   */
  private deserializeDates(obj: any): any {
    if (typeof obj === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(obj)) {
      return new Date(obj);
    }
    if (Array.isArray(obj)) {
      return obj.map(item => this.deserializeDates(item));
    }
    if (obj && typeof obj === 'object') {
      const deserialized: any = {};
      for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
          deserialized[key] = this.deserializeDates(obj[key]);
        }
      }
      return deserialized;
    }
    return obj;
  }

  /**
   * Simple data compression placeholder
   */
  private compressData(data: any): any {
    // Placeholder for compression logic
    // Could implement LZ-string or similar compression library
    return data;
  }

  /**
   * Simple data decompression placeholder
   */
  private decompressData(data: any): any {
    // Placeholder for decompression logic
    return data;
  }

  /**
   * Simple data encryption placeholder
   */
  private encryptData(data: any): any {
    // Placeholder for encryption logic
    // Should implement proper encryption for sensitive data
    return data;
  }

  /**
   * Simple data decryption placeholder
   */
  private decryptData(data: any): any {
    // Placeholder for decryption logic
    return data;
  }

  /**
   * Validate storage capacity before saving
   */
  private async validateStorageCapacity(dataSize: number): Promise<boolean> {
    try {
      const stats = this.getStorageStats();
      const policy = this.getCleanupPolicy();
      
      if (stats.totalSize + dataSize > policy.maxSize) {
        // Attempt cleanup before rejecting
        await this.performCleanup();
        const updatedStats = this.getStorageStats();
        return updatedStats.totalSize + dataSize <= policy.maxSize;
      }
      
      return true;
    } catch (error) {
      console.error('Failed to validate storage capacity:', error);
      return false;
    }
  }

  /**
   * Perform storage cleanup based on policy
   */
  private async performCleanup(): Promise<void> {
    try {
      const policy = this.getCleanupPolicy();
      if (!policy.enabled) return;

      const metadata = this.getAllContextMetadata();
      const now = new Date();
      
      // Find contexts to clean up
      const contextsToCleanup = metadata.filter(meta => {
        const age = (now.getTime() - meta.lastAccessed.getTime()) / (1000 * 60 * 60 * 24);
        return age > policy.maxAge && !policy.preserveActive;
      });

      // Remove old contexts
      for (const meta of contextsToCleanup) {
        await this.deleteContext(meta.contextId, meta.contextType);
      }

      console.log(`Cleaned up ${contextsToCleanup.length} old contexts`);
    } catch (error) {
      console.error('Failed to perform cleanup:', error);
    }
  }

  /**
   * Get storage interface based on type
   */
  private getStorageInterface(storageType: 'localStorage' | 'sessionStorage' | 'indexedDB'): Storage {
    switch (storageType) {
      case 'localStorage':
        return localStorage;
      case 'sessionStorage':
        return sessionStorage;
      case 'indexedDB':
        // Placeholder - would implement IndexedDB wrapper
        return localStorage;
      default:
        return localStorage;
    }
  }

  /**
   * Generate storage key for context
   */
  private getContextStorageKey(contextId: string, contextType: ContextType): string {
    return `${this.STORAGE_PREFIX}${contextType}_${contextId}`;
  }

  /**
   * Get storage configuration for context type
   */
  private getStorageConfig(contextType: ContextType): ContextStorageConfig {
    const configs = this.getStorageConfigs();
    return configs[contextType] || this.defaultStorageConfigs[contextType];
  }

  /**
   * Get all storage configurations
   */
  private getStorageConfigs(): Record<ContextType, ContextStorageConfig> {
    try {
      const data = localStorage.getItem(this.CONFIG_KEY);
      return data ? JSON.parse(data) : this.defaultStorageConfigs;
    } catch (error) {
      console.error('Failed to load storage configs:', error);
      return this.defaultStorageConfigs;
    }
  }

  /**
   * Save storage configurations
   */
  private saveStorageConfigs(configs: Record<ContextType, ContextStorageConfig>): void {
    try {
      localStorage.setItem(this.CONFIG_KEY, JSON.stringify(configs));
    } catch (error) {
      console.error('Failed to save storage configs:', error);
    }
  }

  /**
   * Get cleanup policy
   */
  private getCleanupPolicy(): ContextCleanupPolicy {
    try {
      const data = localStorage.getItem(`${this.STORAGE_PREFIX}cleanup_policy`);
      return data ? JSON.parse(data) : this.defaultCleanupPolicy;
    } catch (error) {
      console.error('Failed to load cleanup policy:', error);
      return this.defaultCleanupPolicy;
    }
  }

  /**
   * Save cleanup policy
   */
  private saveCleanupPolicy(policy: ContextCleanupPolicy): void {
    try {
      localStorage.setItem(`${this.STORAGE_PREFIX}cleanup_policy`, JSON.stringify(policy));
    } catch (error) {
      console.error('Failed to save cleanup policy:', error);
    }
  }

  /**
   * Update context metadata
   */
  private async updateContextMetadata(
    contextId: string, 
    contextType: ContextType, 
    size: number
  ): Promise<void> {
    try {
      const metadata = this.getAllContextMetadata();
      const existingIndex = metadata.findIndex(
        meta => meta.contextId === contextId && meta.contextType === contextType
      );

      const newMetadata: ContextStorageMetadata = {
        contextId,
        contextType,
        storageKey: this.getContextStorageKey(contextId, contextType),
        size,
        lastAccessed: new Date(),
        accessCount: existingIndex >= 0 ? metadata[existingIndex].accessCount + 1 : 1,
        isCompressed: false,
        isEncrypted: false,
        checksum: this.calculateChecksum(contextId + contextType + size)
      };

      if (existingIndex >= 0) {
        metadata[existingIndex] = newMetadata;
      } else {
        metadata.push(newMetadata);
      }

      localStorage.setItem(this.METADATA_KEY, JSON.stringify(metadata));
    } catch (error) {
      console.error('Failed to update context metadata:', error);
    }
  }

  /**
   * Update context access information
   */
  private async updateContextAccess(contextId: string, contextType: ContextType): Promise<void> {
    try {
      const metadata = this.getAllContextMetadata();
      const existingIndex = metadata.findIndex(
        meta => meta.contextId === contextId && meta.contextType === contextType
      );

      if (existingIndex >= 0) {
        metadata[existingIndex].lastAccessed = new Date();
        metadata[existingIndex].accessCount += 1;
        localStorage.setItem(this.METADATA_KEY, JSON.stringify(metadata));
      }
    } catch (error) {
      console.error('Failed to update context access:', error);
    }
  }

  /**
   * Remove context metadata
   */
  private async removeContextMetadata(contextId: string, contextType: ContextType): Promise<void> {
    try {
      const metadata = this.getAllContextMetadata();
      const filteredMetadata = metadata.filter(
        meta => !(meta.contextId === contextId && meta.contextType === contextType)
      );
      localStorage.setItem(this.METADATA_KEY, JSON.stringify(filteredMetadata));
    } catch (error) {
      console.error('Failed to remove context metadata:', error);
    }
  }

  /**
   * Get all context metadata
   */
  private getAllContextMetadata(): ContextStorageMetadata[] {
    try {
      const data = localStorage.getItem(this.METADATA_KEY);
      const metadata = data ? JSON.parse(data) : [];
      
      // Deserialize dates
      return metadata.map((meta: any) => ({
        ...meta,
        lastAccessed: new Date(meta.lastAccessed)
      }));
    } catch (error) {
      console.error('Failed to load context metadata:', error);
      return [];
    }
  }

  /**
   * Calculate simple checksum for data integrity
   */
  private calculateChecksum(data: string): string {
    let hash = 0;
    for (let i = 0; i < data.length; i++) {
      const char = data.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return hash.toString(16);
  }
}
