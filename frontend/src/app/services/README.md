# Structured Request API Services

This document provides comprehensive documentation for the new structured request API services implemented as part of WRI-72.

## Overview

The structured request system provides improved context management by separating individual context elements (plot outline, character feedback, user requests, system prompts, etc.) into structured components. This enables better context preservation, summarization, and optimization while maintaining backward compatibility with existing request formats.

## Architecture

The structured request system consists of several key services:

- **ApiService**: Core HTTP service with new structured endpoints
- **RequestConverterService**: Handles conversion between request formats
- **RequestValidatorService**: Provides comprehensive request validation
- **RequestOptimizerService**: Implements optimization strategies
- **GenerationService**: Enhanced with structured request methods

## New API Methods

### ApiService

The `ApiService` has been enhanced with four new structured request methods:

```typescript
// Structured Character Feedback
requestCharacterFeedbackStructured(request: StructuredCharacterFeedbackRequest): Observable<StructuredCharacterFeedbackResponse>

// Structured Rater Feedback
requestRaterFeedbackStructured(request: StructuredRaterFeedbackRequest): Observable<StructuredRaterFeedbackResponse>

// Structured Chapter Generation
generateChapterStructured(request: StructuredGenerateChapterRequest): Observable<StructuredGenerateChapterResponse>

// Structured Editor Review
requestEditorReviewStructured(request: StructuredEditorReviewRequest): Observable<StructuredEditorReviewResponse>
```

### GenerationService

The `GenerationService` has been enhanced with corresponding structured methods:

```typescript
// Request character feedback using structured context
requestCharacterFeedbackStructured(
  story: Story,
  character: Character,
  plotPoint: string,
  options?: { validate?: boolean; optimize?: boolean }
): Observable<StructuredCharacterFeedbackResponse>

// Request rater feedback using structured context
requestRaterFeedbackStructured(
  story: Story,
  rater: Rater,
  plotPoint: string,
  options?: { validate?: boolean; optimize?: boolean }
): Observable<StructuredRaterFeedbackResponse>

// Generate chapter using structured context
generateChapterStructuredNew(
  story: Story,
  options?: { validate?: boolean; optimize?: boolean }
): Observable<StructuredGenerateChapterResponse>

// Request editor review using structured context
requestEditorReviewStructured(
  story: Story,
  chapterText: string,
  options?: { validate?: boolean; optimize?: boolean }
): Observable<StructuredEditorReviewResponse>
```

## Request Format Detection and Conversion

### RequestConverterService

The `RequestConverterService` provides automatic format detection and conversion:

```typescript
// Convert any request format to structured format
convertToStructured<T>(
  request: any,
  options?: RequestConversionOptions
): RequestConversionResult<T>

// Convert structured request back to traditional format
convertToTraditional<T>(
  request: any,
  options?: RequestConversionOptions
): RequestConversionResult<T>
```

#### Conversion Options

```typescript
interface RequestConversionOptions {
  preserveMetadata?: boolean;        // Include conversion metadata
  addOptimizationHints?: boolean;    // Add optimization suggestions
  validateAfterConversion?: boolean; // Validate converted request
  includePhaseContext?: boolean;     // Include phase information
}
```

#### Example Usage

```typescript
// Convert traditional request to structured
const conversionResult = this.requestConverterService.convertToStructured<StructuredCharacterFeedbackRequest>(
  traditionalRequest,
  { 
    preserveMetadata: true,
    validateAfterConversion: true,
    addOptimizationHints: true
  }
);

if (conversionResult.success) {
  const structuredRequest = conversionResult.convertedRequest;
  // Use structured request...
} else {
  console.error('Conversion failed:', conversionResult.errors);
}
```

## Request Validation

### RequestValidatorService

The `RequestValidatorService` provides comprehensive validation for structured requests:

```typescript
// Validate structured character feedback request
validateCharacterFeedbackRequest(request: StructuredCharacterFeedbackRequest): StructuredRequestValidationResult

// Validate structured rater feedback request
validateRaterFeedbackRequest(request: StructuredRaterFeedbackRequest): StructuredRequestValidationResult

// Validate structured chapter generation request
validateGenerateChapterRequest(request: StructuredGenerateChapterRequest): StructuredRequestValidationResult

// Validate structured editor review request
validateEditorReviewRequest(request: StructuredEditorReviewRequest): StructuredRequestValidationResult
```

#### Validation Result

```typescript
interface StructuredRequestValidationResult {
  isValid: boolean;
  errors: StructuredRequestValidationError[];
  warnings: StructuredRequestValidationError[];
  optimizationSuggestions?: string[];
}
```

#### Example Usage

```typescript
const validationResult = this.requestValidatorService.validateCharacterFeedbackRequest(structuredRequest);

if (!validationResult.isValid) {
  console.error('Validation errors:', validationResult.errors);
  return;
}

if (validationResult.warnings.length > 0) {
  console.warn('Validation warnings:', validationResult.warnings);
}

if (validationResult.optimizationSuggestions) {
  console.info('Optimization suggestions:', validationResult.optimizationSuggestions);
}
```

## Request Optimization

### RequestOptimizerService

The `RequestOptimizerService` implements optimization strategies to improve performance and reduce token usage:

```typescript
// Optimize character feedback request
optimizeCharacterFeedbackRequest(
  request: StructuredCharacterFeedbackRequest,
  options?: OptimizationOptions
): OptimizationResult<StructuredCharacterFeedbackRequest>

// Optimize rater feedback request
optimizeRaterFeedbackRequest(
  request: StructuredRaterFeedbackRequest,
  options?: OptimizationOptions
): OptimizationResult<StructuredRaterFeedbackRequest>

// Optimize chapter generation request
optimizeGenerateChapterRequest(
  request: StructuredGenerateChapterRequest,
  options?: OptimizationOptions
): OptimizationResult<StructuredGenerateChapterRequest>

// Optimize editor review request
optimizeEditorReviewRequest(
  request: StructuredEditorReviewRequest,
  options?: OptimizationOptions
): OptimizationResult<StructuredEditorReviewRequest>
```

#### Optimization Options

```typescript
interface OptimizationOptions {
  maxTokens?: number;           // Maximum token limit
  prioritizeRecent?: boolean;   // Prioritize recent chapters
  summarizeContent?: boolean;   // Enable content summarization
  limitCharacters?: number;     // Maximum number of characters
  limitChapters?: number;       // Maximum number of chapters
  preserveQuality?: boolean;    // Maintain quality over optimization
}
```

#### Optimization Result

```typescript
interface OptimizationResult<T> {
  optimizedRequest: T;
  optimizationsApplied: string[];
  tokensSaved: number;
  originalTokenCount: number;
  optimizedTokenCount: number;
}
```

#### Example Usage

```typescript
const optimizationResult = this.requestOptimizerService.optimizeCharacterFeedbackRequest(
  structuredRequest,
  { 
    maxTokens: 6000,
    limitChapters: 3,
    prioritizeRecent: true
  }
);

console.log(`Optimizations applied: ${optimizationResult.optimizationsApplied.join(', ')}`);
console.log(`Tokens saved: ${optimizationResult.tokensSaved}`);

const optimizedRequest = optimizationResult.optimizedRequest;
```

## Structured Request Interfaces

### Base Structured Request

All structured requests extend from a base interface:

```typescript
interface BaseStructuredRequest {
  systemPrompts: StructuredSystemPrompts;
  worldbuilding: StructuredWorldbuilding;
  storySummary: StructuredStorySummary;
  previousChapters: StructuredChapterContext[];
  requestMetadata?: {
    requestId?: string;
    timestamp?: Date;
    requestSource?: string;
    optimizationHints?: string[];
  };
}
```

### Context Elements

#### System Prompts

```typescript
interface StructuredSystemPrompts {
  mainPrefix: string;
  mainSuffix: string;
  assistantPrompt?: string;
  editorPrompt?: string;
}
```

#### Worldbuilding

```typescript
interface StructuredWorldbuilding {
  content: string;
  lastModified?: Date;
  wordCount?: number;
}
```

#### Story Summary

```typescript
interface StructuredStorySummary {
  summary: string;
  lastModified?: Date;
  wordCount?: number;
}
```

#### Character Context

```typescript
interface StructuredCharacterContext {
  name: string;
  basicBio: string;
  sex: string;
  gender: string;
  sexualPreference: string;
  age: number;
  physicalAppearance: string;
  usualClothing: string;
  personality: string;
  motivations: string;
  fears: string;
  relationships: string;
  isHidden?: boolean;
}
```

#### Plot Context

```typescript
interface StructuredPlotContext {
  plotPoint: string;
  plotOutline?: string;
  plotOutlineStatus?: 'draft' | 'under_review' | 'approved' | 'needs_revision';
  relatedOutlineItems?: {
    title: string;
    description: string;
    order: number;
  }[];
}
```

#### Feedback Context

```typescript
interface StructuredFeedbackContext {
  incorporatedFeedback: {
    source: string;
    type: 'action' | 'dialog' | 'sensation' | 'emotion' | 'thought' | 'suggestion';
    content: string;
    incorporated: boolean;
  }[];
  pendingFeedback?: {
    source: string;
    type: string;
    content: string;
  }[];
}
```

## Migration Guide

### From Traditional to Structured Requests

1. **Automatic Conversion**: Use `RequestConverterService` to automatically convert existing requests:

```typescript
// Old way
const traditionalRequest: CharacterFeedbackRequest = {
  // ... traditional request structure
};

// New way with automatic conversion
const conversionResult = this.requestConverterService.convertToStructured<StructuredCharacterFeedbackRequest>(
  traditionalRequest
);

if (conversionResult.success) {
  const response = await this.apiService.requestCharacterFeedbackStructured(
    conversionResult.convertedRequest
  ).toPromise();
}
```

2. **Direct Structured Request Creation**: Build structured requests directly using `ContextBuilderService`:

```typescript
// Build structured request using context builder
const systemPromptsResult = this.contextBuilderService.buildSystemPromptsContext(story);
const worldbuildingResult = this.contextBuilderService.buildWorldbuildingContext(story);
// ... build other contexts

const structuredRequest: StructuredCharacterFeedbackRequest = {
  systemPrompts: systemPromptsResult.data,
  worldbuilding: worldbuildingResult.data,
  // ... other structured elements
};

const response = await this.apiService.requestCharacterFeedbackStructured(structuredRequest).toPromise();
```

3. **Using Enhanced Generation Service**: Use the new structured methods in `GenerationService`:

```typescript
// Old way
const response = await this.generationService.requestCharacterFeedback(
  story,
  character,
  plotPoint
).toPromise();

// New way
const response = await this.generationService.requestCharacterFeedbackStructured(
  story,
  character,
  plotPoint,
  { validate: true, optimize: true }
).toPromise();
```

## Error Handling

### Validation Errors

```typescript
try {
  const response = await this.generationService.requestCharacterFeedbackStructured(
    story,
    character,
    plotPoint,
    { validate: true }
  ).toPromise();
} catch (error) {
  if (error.message.includes('Request validation failed')) {
    // Handle validation errors
    console.error('Validation failed:', error.message);
  } else {
    // Handle other errors
    console.error('Request failed:', error);
  }
}
```

### Conversion Errors

```typescript
const conversionResult = this.requestConverterService.convertToStructured(request);

if (!conversionResult.success) {
  console.error('Conversion failed:', conversionResult.errors);
  // Handle conversion errors
  return;
}

// Use converted request
const structuredRequest = conversionResult.convertedRequest;
```

## Best Practices

### 1. Use Validation and Optimization

Always enable validation and optimization for better performance and error detection:

```typescript
const response = await this.generationService.requestCharacterFeedbackStructured(
  story,
  character,
  plotPoint,
  { validate: true, optimize: true }
).toPromise();
```

### 2. Handle Conversion Results

Always check conversion results before using converted requests:

```typescript
const conversionResult = this.requestConverterService.convertToStructured(request);

if (!conversionResult.success) {
  // Handle conversion failure
  return;
}

// Log optimization information
if (conversionResult.metadata?.optimizationsApplied) {
  console.log('Optimizations applied:', conversionResult.metadata.optimizationsApplied);
}
```

### 3. Monitor Performance

Use the metadata provided by conversion and optimization results to monitor performance:

```typescript
const optimizationResult = this.requestOptimizerService.optimizeCharacterFeedbackRequest(request);

console.log(`Original tokens: ${optimizationResult.originalTokenCount}`);
console.log(`Optimized tokens: ${optimizationResult.optimizedTokenCount}`);
console.log(`Tokens saved: ${optimizationResult.tokensSaved}`);
```

### 4. Gradual Migration

Migrate to structured requests gradually by using the conversion service initially, then moving to direct structured request creation:

```typescript
// Phase 1: Use conversion service
const conversionResult = this.requestConverterService.convertToStructured(traditionalRequest);

// Phase 2: Build structured requests directly
const structuredRequest = this.buildStructuredRequest(story, character, plotPoint);
```

## Testing

### Unit Tests

The structured request system includes comprehensive unit tests:

- `request-converter.service.spec.ts`: Tests for request conversion
- `request-validator.service.spec.ts`: Tests for request validation
- `request-optimizer.service.spec.ts`: Tests for request optimization

### Integration Tests

Test the complete flow from traditional to structured requests:

```typescript
it('should handle complete structured request flow', async () => {
  // Convert traditional to structured
  const conversionResult = service.convertToStructured(traditionalRequest);
  expect(conversionResult.success).toBe(true);

  // Validate structured request
  const validationResult = validatorService.validateCharacterFeedbackRequest(
    conversionResult.convertedRequest
  );
  expect(validationResult.isValid).toBe(true);

  // Optimize structured request
  const optimizationResult = optimizerService.optimizeCharacterFeedbackRequest(
    conversionResult.convertedRequest
  );
  expect(optimizationResult.tokensSaved).toBeGreaterThan(0);

  // Make API call
  const response = await apiService.requestCharacterFeedbackStructured(
    optimizationResult.optimizedRequest
  ).toPromise();
  expect(response).toBeDefined();
});
```

## Performance Considerations

### Token Usage Optimization

The structured request system includes several optimization strategies:

1. **Chapter Limiting**: Automatically limits the number of previous chapters based on request type
2. **Character Optimization**: Prioritizes relevant characters and summarizes long descriptions
3. **Content Summarization**: Summarizes long text fields while preserving meaning
4. **Context Prioritization**: Focuses on the most relevant context for each request type

### Caching

The `ContextBuilderService` includes caching to improve performance:

```typescript
// Context is cached automatically
const systemPromptsResult = this.contextBuilderService.buildSystemPromptsContext(
  story,
  { useCache: true, maxCacheAge: 5 * 60 * 1000 } // 5 minutes
);
```

### Memory Management

Structured requests are designed to be memory-efficient:

- Context elements are built on-demand
- Optimization reduces memory footprint
- Validation prevents oversized requests

## Troubleshooting

### Common Issues

1. **Validation Failures**: Check that all required fields are present and valid
2. **Conversion Errors**: Ensure the request format is supported
3. **Optimization Issues**: Verify optimization options are appropriate for the request type
4. **Performance Problems**: Enable optimization and check token usage

### Debug Information

Enable debug logging to troubleshoot issues:

```typescript
const conversionResult = this.requestConverterService.convertToStructured(
  request,
  { validateAfterConversion: true }
);

console.log('Conversion result:', conversionResult);
console.log('Validation warnings:', conversionResult.warnings);
console.log('Optimization metadata:', conversionResult.metadata);
```

## Future Enhancements

The structured request system is designed to be extensible. Future enhancements may include:

1. **Advanced Optimization**: Machine learning-based optimization strategies
2. **Context Summarization**: AI-powered context summarization
3. **Request Analytics**: Detailed analytics on request patterns and performance
4. **Batch Processing**: Support for batch structured requests
5. **Real-time Optimization**: Dynamic optimization based on current system load

## Support

For questions or issues with the structured request system:

1. Check this documentation first
2. Review the unit tests for usage examples
3. Check the validation errors for specific issues
4. Consult the type definitions for interface details
