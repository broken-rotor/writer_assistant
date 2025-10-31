/**
 * Context state management models for persistence and storage operations
 */

import { ContextType, BaseContext, ContextVersion, ContextBranch } from './context.model';

/**
 * Storage configuration for different context types
 */
export interface ContextStorageConfig {
  type: ContextType;
  storageType: 'localStorage' | 'sessionStorage' | 'indexedDB';
  maxVersions: number;
  maxBranches: number;
  compressionEnabled: boolean;
  encryptionEnabled: boolean;
  retentionDays: number;
}

/**
 * Context storage metadata
 */
export interface ContextStorageMetadata {
  contextId: string;
  contextType: ContextType;
  storageKey: string;
  size: number; // bytes
  lastAccessed: Date;
  accessCount: number;
  isCompressed: boolean;
  isEncrypted: boolean;
  checksum: string;
}

/**
 * Context storage statistics
 */
export interface ContextStorageStats {
  totalContexts: number;
  totalSize: number; // bytes
  storageUsed: number; // percentage
  contextsByType: Record<ContextType, number>;
  oldestContext: Date;
  newestContext: Date;
  averageSize: number;
  compressionRatio?: number;
}

/**
 * Context cleanup policy
 */
export interface ContextCleanupPolicy {
  enabled: boolean;
  maxAge: number; // days
  maxSize: number; // bytes
  maxVersionsPerContext: number;
  maxBranchesPerContext: number;
  cleanupFrequency: number; // hours
  preserveActive: boolean;
  preserveTagged: string[]; // preserve contexts with these tags
}

/**
 * Context migration info for schema updates
 */
export interface ContextMigration {
  fromVersion: string;
  toVersion: string;
  migrationFunction: (oldData: any) => any;
  description: string;
  required: boolean;
}

/**
 * Context validation result
 */
export interface ContextValidationResult {
  isValid: boolean;
  errors: Array<{
    field: string;
    message: string;
    severity: 'error' | 'warning';
  }>;
  warnings: string[];
  suggestions: string[];
}

/**
 * Context recovery options
 */
export interface ContextRecoveryOptions {
  attemptRepair: boolean;
  useBackup: boolean;
  resetToDefault: boolean;
  preserveUserData: boolean;
  createBackupBeforeRecovery: boolean;
}

/**
 * Context backup info
 */
export interface ContextBackup {
  id: string;
  contextId: string;
  contextType: ContextType;
  version: number;
  createdAt: Date;
  size: number;
  description?: string;
  isAutomatic: boolean;
}

/**
 * Context synchronization state
 */
export interface ContextSyncState {
  contextId: string;
  lastSyncAt: Date;
  syncVersion: number;
  pendingChanges: number;
  conflictCount: number;
  syncStatus: 'synced' | 'pending' | 'conflict' | 'error';
  errorMessage?: string;
}

/**
 * Context merge strategy
 */
export enum ContextMergeStrategy {
  OVERWRITE = 'overwrite',
  MERGE_DEEP = 'merge_deep',
  MERGE_SHALLOW = 'merge_shallow',
  KEEP_BOTH = 'keep_both',
  USER_CHOICE = 'user_choice'
}

/**
 * Context merge conflict
 */
export interface ContextMergeConflict {
  field: string;
  localValue: any;
  remoteValue: any;
  baseValue?: any;
  resolution?: 'local' | 'remote' | 'merged' | 'custom';
  customValue?: any;
}

/**
 * Context merge result
 */
export interface ContextMergeResult {
  success: boolean;
  mergedContext?: BaseContext;
  conflicts: ContextMergeConflict[];
  strategy: ContextMergeStrategy;
  timestamp: Date;
}

/**
 * Context export format
 */
export interface ContextExportFormat {
  version: string;
  exportedAt: Date;
  contexts: Array<{
    type: ContextType;
    data: BaseContext;
    versions?: ContextVersion[];
    branches?: ContextBranch[];
  }>;
  metadata: {
    totalSize: number;
    contextCount: number;
    includeHistory: boolean;
    includeBranches: boolean;
    compression: boolean;
  };
}

/**
 * Context import options
 */
export interface ContextImportOptions {
  overwriteExisting: boolean;
  mergeStrategy: ContextMergeStrategy;
  preserveIds: boolean;
  validateBeforeImport: boolean;
  createBackup: boolean;
  importHistory: boolean;
  importBranches: boolean;
}

/**
 * Context import result
 */
export interface ContextImportResult {
  success: boolean;
  importedCount: number;
  skippedCount: number;
  errorCount: number;
  conflicts: ContextMergeConflict[];
  errors: Array<{
    contextId: string;
    error: string;
  }>;
  warnings: string[];
}

/**
 * Context search index entry
 */
export interface ContextSearchIndex {
  contextId: string;
  contextType: ContextType;
  searchableText: string;
  keywords: string[];
  tags: string[];
  lastIndexed: Date;
  relevanceScore?: number;
}

/**
 * Context search result
 */
export interface ContextSearchResult {
  context: BaseContext;
  relevanceScore: number;
  matchedFields: string[];
  highlights: Array<{
    field: string;
    text: string;
    start: number;
    end: number;
  }>;
}

/**
 * Context performance metrics
 */
export interface ContextPerformanceMetrics {
  operationType: string;
  contextType: ContextType;
  duration: number; // milliseconds
  dataSize: number; // bytes
  timestamp: Date;
  success: boolean;
  errorMessage?: string;
}

/**
 * Context cache entry
 */
export interface ContextCacheEntry {
  contextId: string;
  data: BaseContext;
  cachedAt: Date;
  expiresAt: Date;
  accessCount: number;
  lastAccessed: Date;
  size: number;
  priority: number; // for cache eviction
}

/**
 * Context event for pub/sub system
 */
export interface ContextEvent {
  type: 'created' | 'updated' | 'deleted' | 'branched' | 'merged' | 'restored';
  contextId: string;
  contextType: ContextType;
  timestamp: Date;
  userId?: string;
  data?: any;
  metadata?: Record<string, any>;
}

/**
 * Context subscription for event listening
 */
export interface ContextSubscription {
  id: string;
  contextId?: string;
  contextType?: ContextType;
  eventTypes: string[];
  callback: (event: ContextEvent) => void;
  createdAt: Date;
  isActive: boolean;
}
