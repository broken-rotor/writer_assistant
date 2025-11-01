import { Injectable, inject } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { 
  BaseContext, 
  ContextType, 
  ContextVersion, 
  ContextDiff,
  ContextOperationResult 
} from '../models/context.model';
import { ContextStorageService } from './context-storage.service';

/**
 * Context Versioning Service - Handles versioning and history tracking for context evolution
 * Enables rollback, history navigation, and change tracking
 */
@Injectable({
  providedIn: 'root'
})
export class ContextVersioningService {
  private contextStorageService = inject(ContextStorageService);
  
  private readonly VERSION_STORAGE_PREFIX = 'writer_assistant_context_versions_';
  private readonly DIFF_STORAGE_PREFIX = 'writer_assistant_context_diffs_';

  // Version history cache
  private versionHistoryCache = new Map<string, ContextVersion[]>();
  
  // Version statistics
  private versionStatsSubject = new BehaviorSubject<{
    totalVersions: number;
    contextCount: number;
    averageVersionsPerContext: number;
    oldestVersion: Date;
    newestVersion: Date;
  }>({
    totalVersions: 0,
    contextCount: 0,
    averageVersionsPerContext: 0,
    oldestVersion: new Date(),
    newestVersion: new Date()
  });

  public versionStats$ = this.versionStatsSubject.asObservable();

  constructor() {
    this.updateVersionStats();
  }

  /**
   * Create a new version of a context
   */
  async createVersion<T extends BaseContext>(
    context: T,
    previousVersion?: ContextVersion<T>
  ): Promise<ContextOperationResult<ContextVersion<T>>> {
    try {
      const now = new Date();
      const diffs = previousVersion ? this.calculateDiffs(previousVersion.data, context) : [];

      const version: ContextVersion<T> = {
        metadata: {
          ...context.metadata,
          parentVersion: previousVersion?.metadata.version
        },
        data: this.deepClone(context),
        diffs,
        checksum: this.calculateChecksum(JSON.stringify(context))
      };

      // Save version to storage
      const versionKey = this.getVersionStorageKey(context.id, context.type, context.metadata.version);
      const serializedVersion = JSON.stringify(this.serializeDates(version));
      localStorage.setItem(versionKey, serializedVersion);

      // Update version history cache
      this.updateVersionHistoryCache(context.id, context.type, version);

      // Update statistics
      this.updateVersionStats();

      return {
        success: true,
        data: version,
        metadata: {
          version: context.metadata.version,
          timestamp: now,
          operation: 'create_version'
        }
      };
    } catch (error) {
      console.error('Failed to create version:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  /**
   * Get version history for a context
   */
  async getVersionHistory<T extends BaseContext>(
    contextId: string,
    contextType: ContextType
  ): Promise<ContextOperationResult<ContextVersion<T>[]>> {
    try {
      // Check cache first
      const cacheKey = `${contextId}_${contextType}`;
      if (this.versionHistoryCache.has(cacheKey)) {
        return {
          success: true,
          data: this.versionHistoryCache.get(cacheKey) as ContextVersion<T>[],
          metadata: {
            version: 0,
            timestamp: new Date(),
            operation: 'get_version_history'
          }
        };
      }

      // Load from storage
      const versions: ContextVersion<T>[] = [];
      const versionKeys = this.getVersionKeys(contextId, contextType);

      for (const key of versionKeys) {
        try {
          const serializedVersion = localStorage.getItem(key);
          if (serializedVersion) {
            const version = this.deserializeDates(JSON.parse(serializedVersion)) as ContextVersion<T>;
            versions.push(version);
          }
        } catch (error) {
          console.warn(`Failed to load version from key ${key}:`, error);
        }
      }

      // Sort by version number
      versions.sort((a, b) => a.metadata.version - b.metadata.version);

      // Update cache
      this.versionHistoryCache.set(cacheKey, versions);

      return {
        success: true,
        data: versions,
        metadata: {
          version: 0,
          timestamp: new Date(),
          operation: 'get_version_history'
        }
      };
    } catch (error) {
      console.error('Failed to get version history:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  /**
   * Get a specific version of a context
   */
  async getVersion<T extends BaseContext>(
    contextId: string,
    contextType: ContextType,
    version: number
  ): Promise<ContextOperationResult<ContextVersion<T>>> {
    try {
      const versionKey = this.getVersionStorageKey(contextId, contextType, version);
      const serializedVersion = localStorage.getItem(versionKey);

      if (!serializedVersion) {
        return {
          success: false,
          error: `Version ${version} not found for context ${contextId}`
        };
      }

      const versionData = this.deserializeDates(JSON.parse(serializedVersion)) as ContextVersion<T>;

      return {
        success: true,
        data: versionData,
        metadata: {
          version,
          timestamp: new Date(),
          operation: 'get_version'
        }
      };
    } catch (error) {
      console.error('Failed to get version:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to parse version data'
      };
    }
  }

  /**
   * Rollback context to a previous version
   */
  async rollbackToVersion<T extends BaseContext>(
    contextId: string,
    contextType: ContextType,
    targetVersion: number
  ): Promise<ContextOperationResult<T>> {
    try {
      // Get the target version
      const versionResult = await this.getVersion<T>(contextId, contextType, targetVersion);
      if (!versionResult.success || !versionResult.data) {
        return {
          success: false,
          error: `Target version ${targetVersion} not found`
        };
      }

      const targetVersionData = versionResult.data;
      const now = new Date();

      // Create new context from target version data
      const rolledBackContext: T = {
        ...targetVersionData.data,
        metadata: {
          ...targetVersionData.data.metadata,
          version: targetVersionData.data.metadata.version + 1,
          updatedAt: now,
          parentVersion: targetVersion,
          description: `Rolled back to version ${targetVersion}`
        }
      };

      // Save the rolled back context
      const saveResult = await this.contextStorageService.saveContext(rolledBackContext);
      if (!saveResult.success) {
        return saveResult;
      }

      // Create version entry for the rollback
      await this.createVersion(rolledBackContext, targetVersionData);

      return {
        success: true,
        data: rolledBackContext,
        metadata: {
          version: rolledBackContext.metadata.version,
          timestamp: now,
          operation: 'rollback'
        }
      };
    } catch (error) {
      console.error('Failed to rollback to version:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  /**
   * Compare two versions and get differences
   */
  async compareVersions<T extends BaseContext>(
    contextId: string,
    contextType: ContextType,
    version1: number,
    version2: number
  ): Promise<ContextOperationResult<ContextDiff[]>> {
    try {
      // Get both versions
      const [result1, result2] = await Promise.all([
        this.getVersion<T>(contextId, contextType, version1),
        this.getVersion<T>(contextId, contextType, version2)
      ]);

      if (!result1.success || !result1.data) {
        return {
          success: false,
          error: `Version ${version1} not found`
        };
      }

      if (!result2.success || !result2.data) {
        return {
          success: false,
          error: `Version ${version2} not found`
        };
      }

      const diffs = this.calculateDiffs(result1.data.data, result2.data.data);

      return {
        success: true,
        data: diffs,
        metadata: {
          version: 0,
          timestamp: new Date(),
          operation: 'compare_versions'
        }
      };
    } catch (error) {
      console.error('Failed to compare versions:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  /**
   * Clean up old versions based on retention policy
   */
  async cleanupOldVersions(
    contextId: string,
    contextType: ContextType,
    maxVersions: number
  ): Promise<ContextOperationResult<number>> {
    try {
      const historyResult = await this.getVersionHistory(contextId, contextType);
      if (!historyResult.success || !historyResult.data) {
        return {
          success: false,
          error: 'Failed to get version history'
        };
      }

      const versions = historyResult.data;
      if (versions.length <= maxVersions) {
        return {
          success: true,
          data: 0,
          metadata: {
            version: 0,
            timestamp: new Date(),
            operation: 'cleanup_versions'
          }
        };
      }

      // Keep the most recent versions
      const versionsToDelete = versions
        .sort((a, b) => b.metadata.version - a.metadata.version)
        .slice(maxVersions);

      let deletedCount = 0;
      for (const version of versionsToDelete) {
        try {
          const versionKey = this.getVersionStorageKey(
            contextId, 
            contextType, 
            version.metadata.version
          );
          localStorage.removeItem(versionKey);
          deletedCount++;
        } catch (error) {
          console.warn(`Failed to delete version ${version.metadata.version}:`, error);
        }
      }

      // Clear cache to force reload
      const cacheKey = `${contextId}_${contextType}`;
      this.versionHistoryCache.delete(cacheKey);

      // Update statistics
      this.updateVersionStats();

      return {
        success: true,
        data: deletedCount,
        metadata: {
          version: 0,
          timestamp: new Date(),
          operation: 'cleanup_versions'
        }
      };
    } catch (error) {
      console.error('Failed to cleanup old versions:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  /**
   * Get version statistics
   */
  getVersionStats(): Observable<any> {
    return this.versionStats$;
  }

  /**
   * Calculate differences between two context objects
   */
  private calculateDiffs(oldContext: any, newContext: any, path = ''): ContextDiff[] {
    const diffs: ContextDiff[] = [];
    const now = new Date();

    // Handle primitive values
    if (typeof oldContext !== 'object' || typeof newContext !== 'object') {
      if (oldContext !== newContext) {
        diffs.push({
          field: path,
          oldValue: oldContext,
          newValue: newContext,
          timestamp: now,
          operation: 'update'
        });
      }
      return diffs;
    }

    // Handle null values
    if (oldContext === null && newContext !== null) {
      diffs.push({
        field: path,
        oldValue: null,
        newValue: newContext,
        timestamp: now,
        operation: 'create'
      });
      return diffs;
    }

    if (oldContext !== null && newContext === null) {
      diffs.push({
        field: path,
        oldValue: oldContext,
        newValue: null,
        timestamp: now,
        operation: 'delete'
      });
      return diffs;
    }

    // Handle arrays
    if (Array.isArray(oldContext) && Array.isArray(newContext)) {
      const maxLength = Math.max(oldContext.length, newContext.length);
      for (let i = 0; i < maxLength; i++) {
        const fieldPath = path ? `${path}[${i}]` : `[${i}]`;
        
        if (i >= oldContext.length) {
          diffs.push({
            field: fieldPath,
            oldValue: undefined,
            newValue: newContext[i],
            timestamp: now,
            operation: 'create'
          });
        } else if (i >= newContext.length) {
          diffs.push({
            field: fieldPath,
            oldValue: oldContext[i],
            newValue: undefined,
            timestamp: now,
            operation: 'delete'
          });
        } else {
          diffs.push(...this.calculateDiffs(oldContext[i], newContext[i], fieldPath));
        }
      }
      return diffs;
    }

    // Handle objects
    const allKeys = new Set([...Object.keys(oldContext), ...Object.keys(newContext)]);
    
    for (const key of allKeys) {
      const fieldPath = path ? `${path}.${key}` : key;
      
      if (!(key in oldContext)) {
        diffs.push({
          field: fieldPath,
          oldValue: undefined,
          newValue: newContext[key],
          timestamp: now,
          operation: 'create'
        });
      } else if (!(key in newContext)) {
        diffs.push({
          field: fieldPath,
          oldValue: oldContext[key],
          newValue: undefined,
          timestamp: now,
          operation: 'delete'
        });
      } else {
        diffs.push(...this.calculateDiffs(oldContext[key], newContext[key], fieldPath));
      }
    }

    return diffs;
  }

  /**
   * Calculate checksum for data integrity
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

  /**
   * Deep clone an object
   */
  private deepClone<T>(obj: T): T {
    if (obj === null || typeof obj !== 'object') {
      return obj;
    }

    if (obj instanceof Date) {
      return new Date(obj.getTime()) as unknown as T;
    }

    if (Array.isArray(obj)) {
      return obj.map(item => this.deepClone(item)) as unknown as T;
    }

    const cloned = {} as T;
    for (const key in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        cloned[key] = this.deepClone(obj[key]);
      }
    }

    return cloned;
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
        if (Object.prototype.hasOwnProperty.call(obj, key)) {
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
        if (Object.prototype.hasOwnProperty.call(obj, key)) {
          deserialized[key] = this.deserializeDates(obj[key]);
        }
      }
      return deserialized;
    }
    return obj;
  }

  /**
   * Get storage key for a specific version
   */
  private getVersionStorageKey(contextId: string, contextType: ContextType, version: number): string {
    return `${this.VERSION_STORAGE_PREFIX}${contextType}_${contextId}_v${version}`;
  }

  /**
   * Get all version keys for a context
   */
  private getVersionKeys(contextId: string, contextType: ContextType): string[] {
    const prefix = `${this.VERSION_STORAGE_PREFIX}${contextType}_${contextId}_v`;
    const keys: string[] = [];

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(prefix)) {
        keys.push(key);
      }
    }

    return keys;
  }

  /**
   * Update version history cache
   */
  private updateVersionHistoryCache<T extends BaseContext>(
    contextId: string,
    contextType: ContextType,
    version: ContextVersion<T>
  ): void {
    const cacheKey = `${contextId}_${contextType}`;
    const existingHistory = this.versionHistoryCache.get(cacheKey) || [];
    
    // Add or update version in cache
    const existingIndex = existingHistory.findIndex(v => v.metadata.version === version.metadata.version);
    if (existingIndex >= 0) {
      existingHistory[existingIndex] = version;
    } else {
      existingHistory.push(version);
      existingHistory.sort((a, b) => a.metadata.version - b.metadata.version);
    }

    this.versionHistoryCache.set(cacheKey, existingHistory);
  }

  /**
   * Update version statistics
   */
  private updateVersionStats(): void {
    try {
      let totalVersions = 0;
      const contextVersionCounts = new Map<string, number>();
      const versionDates: Date[] = [];

      // Count versions in localStorage
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith(this.VERSION_STORAGE_PREFIX)) {
          totalVersions++;
          
          // Extract context identifier
          const parts = key.replace(this.VERSION_STORAGE_PREFIX, '').split('_');
          if (parts.length >= 3) {
            const contextKey = `${parts[0]}_${parts[1]}`;
            contextVersionCounts.set(contextKey, (contextVersionCounts.get(contextKey) || 0) + 1);
          }

          // Try to get version date
          try {
            const versionData = localStorage.getItem(key);
            if (versionData) {
              const parsed = JSON.parse(versionData);
              if (parsed.metadata && parsed.metadata.createdAt) {
                versionDates.push(new Date(parsed.metadata.createdAt));
              }
            }
          } catch (error) {
            console.info('Failed to parse version stats:', error)
          }
        }
      }

      const contextCount = contextVersionCounts.size;
      const averageVersionsPerContext = contextCount > 0 ? totalVersions / contextCount : 0;
      const oldestVersion = versionDates.length > 0 ? 
        new Date(Math.min(...versionDates.map(d => d.getTime()))) : new Date();
      const newestVersion = versionDates.length > 0 ? 
        new Date(Math.max(...versionDates.map(d => d.getTime()))) : new Date();

      this.versionStatsSubject.next({
        totalVersions,
        contextCount,
        averageVersionsPerContext,
        oldestVersion,
        newestVersion
      });
    } catch (error) {
      console.error('Failed to update version stats:', error);
    }
  }
}
