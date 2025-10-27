import { Injectable } from '@angular/core';

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  suggestions: string[];
}

export interface ContentStatistics {
  characterCount: number;
  wordCount: number;
  lineCount: number;
  paragraphCount: number;
  headerCount: number;
  averageParagraphLength: number;
  topicsIdentified: string[];
  estimatedReadingTimeMinutes: number;
}

@Injectable({
  providedIn: 'root'
})
export class WorldbuildingValidatorService {
  private readonly maxContentLength = 10000;
  private readonly minContentLength = 10;
  private readonly maxTopicSections = 20;

  /**
   * Validate worldbuilding content on the frontend
   */
  validateContent(content: string, strict: boolean = false): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    const suggestions: string[] = [];

    // Length validation
    const lengthResult = this.validateLength(content, strict);
    errors.push(...lengthResult.errors);
    warnings.push(...lengthResult.warnings);
    suggestions.push(...lengthResult.suggestions);

    // Structure validation
    const structureResult = this.validateStructure(content);
    warnings.push(...structureResult.warnings);
    suggestions.push(...structureResult.suggestions);

    // Basic security validation
    const securityResult = this.validateSecurity(content);
    errors.push(...securityResult.errors);
    warnings.push(...securityResult.warnings);

    // Format validation
    const formatResult = this.validateFormat(content);
    suggestions.push(...formatResult.suggestions);

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      suggestions
    };
  }

  private validateLength(content: string, strict: boolean): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    const suggestions: string[] = [];

    const contentLength = content.trim().length;

    if (contentLength === 0) {
      errors.push('Content cannot be empty');
    } else if (contentLength < this.minContentLength) {
      if (strict) {
        errors.push(`Content too short (minimum ${this.minContentLength} characters)`);
      } else {
        warnings.push(`Content is quite short (minimum ${this.minContentLength} characters recommended)`);
      }
    } else if (contentLength > this.maxContentLength) {
      errors.push(`Content too long (maximum ${this.maxContentLength} characters)`);
    }

    if (contentLength < 100) {
      suggestions.push('Consider adding more detail to make your worldbuilding more immersive');
    }

    return { isValid: errors.length === 0, errors, warnings, suggestions };
  }

  private validateStructure(content: string): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    const suggestions: string[] = [];

    // Check for topic headers
    const headers = content.match(/^##\s+(.+)$/gm) || [];

    if (headers.length === 0) {
      suggestions.push('Consider organizing content with topic headers (## Topic Name)');
    } else if (headers.length > this.maxTopicSections) {
      warnings.push(`Too many topic sections (${headers.length}). Consider consolidating.`);
    }

    // Check for paragraph structure
    const paragraphs = content.split('\n\n').filter(p => p.trim().length > 0);

    if (paragraphs.length < 2 && content.trim().length > 200) {
      suggestions.push('Consider breaking content into paragraphs for better readability');
    }

    // Check for very long paragraphs
    const longParagraphs = paragraphs.filter(p => p.length > 1000);
    if (longParagraphs.length > 0) {
      suggestions.push('Some paragraphs are very long. Consider breaking them up.');
    }

    // Check for duplicate headers
    const headerTexts = headers.map(h => h.replace(/^##\s+/, ''));
    if (headerTexts.length !== new Set(headerTexts).size) {
      warnings.push('Duplicate topic headers found. Consider merging or renaming.');
    }

    return { isValid: errors.length === 0, errors, warnings, suggestions };
  }

  private validateSecurity(content: string): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    const suggestions: string[] = [];

    // Check for script injection
    const scriptPatterns = [
      /<script[^>]*>/i,
      /javascript:/i,
      /data:text\/html/i,
      /vbscript:/i,
      /onload\s*=/i,
      /onerror\s*=/i,
      /onclick\s*=/i
    ];

    for (const pattern of scriptPatterns) {
      if (pattern.test(content)) {
        errors.push(`Potentially dangerous content detected: ${pattern.source}`);
      }
    }

    // Check for excessive HTML tags
    const htmlTags = content.match(/<[^>]+>/g) || [];
    if (htmlTags.length > 10) {
      warnings.push('Content contains many HTML tags. Consider using plain text.');
    }

    return { isValid: errors.length === 0, errors, warnings, suggestions };
  }

  private validateFormat(content: string): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    const suggestions: string[] = [];

    // Check for excessive whitespace
    if (/\n\s*\n\s*\n\s*\n/.test(content)) {
      suggestions.push('Consider reducing excessive blank lines for better formatting');
    }

    // Check for trailing whitespace
    const lines = content.split('\n');
    const linesWithTrailingSpace = lines.filter(line => /\s$/.test(line));
    if (linesWithTrailingSpace.length > 0) {
      suggestions.push('Consider removing trailing whitespace from lines');
    }

    return { isValid: errors.length === 0, errors, warnings, suggestions };
  }

  /**
   * Get content statistics
   */
  getContentStatistics(content: string): ContentStatistics {
    const lines = content.split('\n');
    const paragraphs = content.split('\n\n').filter(p => p.trim().length > 0);
    const headers = content.match(/^##\s+(.+)$/gm) || [];
    const words = content.split(/\s+/).filter(word => word.length > 0);

    return {
      characterCount: content.length,
      wordCount: words.length,
      lineCount: lines.length,
      paragraphCount: paragraphs.length,
      headerCount: headers.length,
      averageParagraphLength: paragraphs.length > 0 ? 
        paragraphs.reduce((sum, p) => sum + p.length, 0) / paragraphs.length : 0,
      topicsIdentified: headers.map(h => h.replace(/^##\s+/, '')),
      estimatedReadingTimeMinutes: Math.max(1, Math.floor(words.length / 200))
    };
  }

  /**
   * Generate improvement suggestions
   */
  suggestImprovements(content: string): string[] {
    const suggestions: string[] = [];
    const stats = this.getContentStatistics(content);

    // Length-based suggestions
    if (stats.wordCount < 50) {
      suggestions.push('Consider expanding your worldbuilding with more details and descriptions');
    } else if (stats.wordCount > 2000) {
      suggestions.push('Consider organizing this extensive content into multiple sections or documents');
    }

    // Structure suggestions
    if (stats.headerCount === 0) {
      suggestions.push('Add topic headers (## Topic Name) to organize your worldbuilding');
    } else if (stats.headerCount > 10) {
      suggestions.push('Consider consolidating some topics to improve organization');
    }

    if (stats.paragraphCount < 3 && stats.wordCount > 100) {
      suggestions.push('Break your content into multiple paragraphs for better readability');
    }

    // Content depth suggestions
    if (stats.averageParagraphLength < 50) {
      suggestions.push('Consider adding more detail to each section');
    } else if (stats.averageParagraphLength > 500) {
      suggestions.push('Consider breaking long paragraphs into smaller, more digestible sections');
    }

    // Topic coverage suggestions
    const commonTopics = ['geography', 'culture', 'history', 'politics', 'magic', 'technology'];
    const mentionedTopics = commonTopics.filter(topic => 
      stats.topicsIdentified.some(header => header.toLowerCase().includes(topic))
    );

    if (mentionedTopics.length < 3) {
      const missingTopics = commonTopics.filter(topic => !mentionedTopics.includes(topic));
      suggestions.push(`Consider adding sections about: ${missingTopics.slice(0, 3).join(', ')}`);
    }

    return suggestions;
  }

  /**
   * Basic content sanitization
   */
  sanitizeContent(content: string): string {
    // Remove script tags
    let sanitized = content.replace(/<script[^>]*>.*?<\/script>/gi, '');
    
    // Remove dangerous attributes
    sanitized = sanitized.replace(/on\w+\s*=\s*["'][^"']*["']/gi, '');
    
    // Remove javascript: and data: URLs
    sanitized = sanitized.replace(/javascript:[^"'\s]*/gi, '');
    sanitized = sanitized.replace(/data:text\/html[^"'\s]*/gi, '');
    
    // Normalize whitespace
    sanitized = sanitized.replace(/\s+/g, ' ');
    sanitized = sanitized.replace(/\n\s*\n\s*\n+/g, '\n\n');
    
    // Remove trailing whitespace from lines
    sanitized = sanitized.split('\n').map(line => line.trimEnd()).join('\n');
    
    return sanitized.trim();
  }
}
