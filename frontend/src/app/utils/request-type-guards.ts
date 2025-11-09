/**
 * Request Type Guards
 * 
 * Type guard functions to detect and validate different request formats.
 */

import {
  CharacterFeedbackRequest,
  RaterFeedbackRequest,
  GenerateChapterRequest,
  EditorReviewRequest
} from '../models/story.model';

import {
  StructuredCharacterFeedbackRequest,
  StructuredRaterFeedbackRequest,
  StructuredGenerateChapterRequest,
  StructuredEditorReviewRequest,
  RequestFormatDetectionResult
} from '../models/structured-request.model';

// ============================================================================
// TYPE GUARD FUNCTIONS
// ============================================================================

/**
 * Check if an object has the basic structure of a traditional request
 */
function hasTraditionalRequestStructure(obj: any): boolean {
  return obj && 
         typeof obj === 'object' &&
         obj.systemPrompts &&
         typeof obj.systemPrompts === 'object' &&
         typeof obj.worldbuilding === 'string' &&
         typeof obj.storySummary === 'string' &&
         Array.isArray(obj.previousChapters);
}

/**
 * Check if an object has structured request features
 */
function hasStructuredRequestFeatures(obj: any): boolean {
  return obj &&
         typeof obj === 'object' &&
         obj.systemPrompts &&
         typeof obj.systemPrompts === 'object' &&
         obj.worldbuilding &&
         typeof obj.worldbuilding === 'object' &&
         obj.storySummary &&
         typeof obj.storySummary === 'object' &&
         Array.isArray(obj.previousChapters) &&
         obj.previousChapters.length > 0 &&
         typeof obj.previousChapters[0] === 'object' &&
         obj.previousChapters[0].number !== undefined;
}

// ============================================================================
// CHARACTER FEEDBACK REQUEST TYPE GUARDS
// ============================================================================

/**
 * Type guard for traditional character feedback request
 */
export function isTraditionalCharacterFeedbackRequest(obj: any): obj is CharacterFeedbackRequest {
  return hasTraditionalRequestStructure(obj) &&
         obj.character &&
         typeof obj.character === 'object' &&
         typeof obj.character.name === 'string' &&
         typeof obj.plotPoint === 'string' &&
         !hasStructuredRequestFeatures(obj);
}

/**
 * Type guard for structured character feedback request
 */
export function isStructuredCharacterFeedbackRequest(obj: any): obj is StructuredCharacterFeedbackRequest {
  return hasStructuredRequestFeatures(obj) &&
         obj.character &&
         typeof obj.character === 'object' &&
         obj.plotContext &&
         typeof obj.plotContext === 'object' &&
         typeof obj.plotContext.plotPoint === 'string';
}

// ============================================================================
// RATER FEEDBACK REQUEST TYPE GUARDS
// ============================================================================

/**
 * Type guard for traditional rater feedback request
 */
export function isTraditionalRaterFeedbackRequest(obj: any): obj is RaterFeedbackRequest {
  return hasTraditionalRequestStructure(obj) &&
         typeof obj.raterPrompt === 'string' &&
         typeof obj.plotPoint === 'string' &&
         !hasStructuredRequestFeatures(obj);
}

/**
 * Type guard for structured rater feedback request
 */
export function isStructuredRaterFeedbackRequest(obj: any): obj is StructuredRaterFeedbackRequest {
  return hasStructuredRequestFeatures(obj) &&
         typeof obj.raterPrompt === 'string' &&
         obj.plotContext &&
         typeof obj.plotContext === 'object' &&
         typeof obj.plotContext.plotPoint === 'string';
}

// ============================================================================
// CHAPTER GENERATION REQUEST TYPE GUARDS
// ============================================================================

/**
 * Type guard for traditional chapter generation request
 */
export function isTraditionalGenerateChapterRequest(obj: any): obj is GenerateChapterRequest {
  return hasTraditionalRequestStructure(obj) &&
         Array.isArray(obj.characters) &&
         typeof obj.plotPoint === 'string' &&
         Array.isArray(obj.incorporatedFeedback) &&
         !hasStructuredRequestFeatures(obj);
}

/**
 * Type guard for structured chapter generation request
 */
export function isStructuredGenerateChapterRequest(obj: any): obj is StructuredGenerateChapterRequest {
  return hasStructuredRequestFeatures(obj) &&
         Array.isArray(obj.characters) &&
         obj.plotContext &&
         typeof obj.plotContext === 'object' &&
         obj.feedbackContext &&
         typeof obj.feedbackContext === 'object';
}

// ============================================================================
// EDITOR REVIEW REQUEST TYPE GUARDS
// ============================================================================

/**
 * Type guard for traditional editor review request
 */
export function isTraditionalEditorReviewRequest(obj: any): obj is EditorReviewRequest {
  return hasTraditionalRequestStructure(obj) &&
         Array.isArray(obj.characters) &&
         typeof obj.chapterToReview === 'string' &&
         !hasStructuredRequestFeatures(obj);
}

/**
 * Type guard for structured editor review request
 */
export function isStructuredEditorReviewRequest(obj: any): obj is StructuredEditorReviewRequest {
  return hasStructuredRequestFeatures(obj) &&
         Array.isArray(obj.characters) &&
         typeof obj.chapterToReview === 'string';
}

// ============================================================================
// FORMAT DETECTION FUNCTIONS
// ============================================================================

/**
 * Detect the format of a character feedback request
 */
export function detectCharacterFeedbackRequestFormat(obj: any): RequestFormatDetectionResult {
  const detectedFeatures: string[] = [];
  let confidence = 0;
  let format: 'traditional' | 'structured' | 'enhanced' | 'unknown' = 'unknown';

  if (!obj || typeof obj !== 'object') {
    return { format: 'unknown', confidence: 0, detectedFeatures: [] };
  }

  // Check for basic request structure
  if (hasTraditionalRequestStructure(obj)) {
    detectedFeatures.push('traditional_structure');
    confidence += 30;
  }

  // Check for character field
  if (obj.character && typeof obj.character === 'object') {
    detectedFeatures.push('character_field');
    confidence += 20;
  }

  // Check for structured features
  if (hasStructuredRequestFeatures(obj)) {
    detectedFeatures.push('structured_features');
    confidence += 25;
    format = 'structured';
  }

  // Check for plot context vs plot point
  if (obj.plotContext && typeof obj.plotContext === 'object') {
    detectedFeatures.push('structured_plot_context');
    confidence += 20;
    format = 'structured';
  } else if (typeof obj.plotPoint === 'string') {
    detectedFeatures.push('traditional_plot_point');
    confidence += 15;
    if (format === 'unknown') format = 'traditional';
  }

  // Final format determination
  if (confidence >= 70) {
    if (isStructuredCharacterFeedbackRequest(obj)) {
      format = 'structured';
      confidence = Math.min(confidence + 10, 100);
      confidence = Math.min(confidence + 10, 100);
    } else if (isTraditionalCharacterFeedbackRequest(obj)) {
      format = 'traditional';
      confidence = Math.min(confidence + 10, 100);
    }
  }

  return { format, confidence, detectedFeatures };
}

/**
 * Detect the format of any request object
 */
export function detectRequestFormat(obj: any): RequestFormatDetectionResult {
  if (!obj || typeof obj !== 'object') {
    return { format: 'unknown', confidence: 0, detectedFeatures: [] };
  }

  // Try to detect specific request types
  if (obj.character) {
    return detectCharacterFeedbackRequestFormat(obj);
  }

  if (obj.raterPrompt) {
    // Similar logic for rater feedback requests
    const detectedFeatures: string[] = [];
    let confidence = 0;
    let format: 'traditional' | 'structured' | 'enhanced' | 'unknown' = 'unknown';

    if (hasTraditionalRequestStructure(obj)) {
      detectedFeatures.push('traditional_structure');
      confidence += 30;
    }

    if (hasStructuredRequestFeatures(obj)) {
      detectedFeatures.push('structured_features');
      format = 'structured';
      confidence += 25;
    }

    if (obj.plotContext) {
      detectedFeatures.push('structured_plot_context');
      format = 'structured';
      confidence += 20;
    } else if (obj.plotPoint) {
      detectedFeatures.push('traditional_plot_point');
      if (format === 'unknown') format = 'traditional';
      confidence += 15;
    }

    return { format, confidence, detectedFeatures };
  }

  if (obj.characters && Array.isArray(obj.characters)) {
    // Chapter generation or editor review request
    const detectedFeatures: string[] = [];
    let confidence = 0;
    let format: 'traditional' | 'structured' | 'enhanced' | 'unknown' = 'unknown';

    if (hasTraditionalRequestStructure(obj)) {
      detectedFeatures.push('traditional_structure');
      confidence += 30;
    }

    if (hasStructuredRequestFeatures(obj)) {
      detectedFeatures.push('structured_features');
      format = 'structured';
      confidence += 25;
    }

    if (obj.feedbackContext) {
      detectedFeatures.push('structured_feedback_context');
      format = 'structured';
      confidence += 20;
    } else if (obj.incorporatedFeedback) {
      detectedFeatures.push('traditional_incorporated_feedback');
      if (format === 'unknown') format = 'traditional';
      confidence += 15;
    }

    return { format, confidence, detectedFeatures };
  }

  // Generic detection for unknown request types
  const detectedFeatures: string[] = [];
  let confidence = 0;
  let format: 'traditional' | 'structured' | 'enhanced' | 'unknown' = 'unknown';

  if (hasTraditionalRequestStructure(obj)) {
    detectedFeatures.push('traditional_structure');
    format = 'traditional';
    confidence += 40;
  }

  if (hasStructuredRequestFeatures(obj)) {
    detectedFeatures.push('structured_features');
    format = 'structured';
    confidence += 30;
  }

  return { format, confidence, detectedFeatures };
}
