/**
 * Unit tests for RequestConverterService
 */

import { TestBed } from '@angular/core/testing';
import { RequestConverterService } from './request-converter.service';
import { ContextBuilderService } from './context-builder.service';
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
  StructuredEditorReviewRequest
} from '../models/structured-request.model';

describe('RequestConverterService', () => {
  let service: RequestConverterService;
  let mockContextBuilderService: jasmine.SpyObj<ContextBuilderService>;

  beforeEach(() => {
    const contextBuilderSpy = jasmine.createSpyObj('ContextBuilderService', [
      'buildSystemPromptsContext',
      'buildWorldbuildingContext',
      'buildStorySummaryContext',
      'buildChaptersContext',
      'buildCharactersContext'
    ]);

    TestBed.configureTestingModule({
      providers: [
        RequestConverterService,
        { provide: ContextBuilderService, useValue: contextBuilderSpy }
      ]
    });

    service = TestBed.inject(RequestConverterService);
    mockContextBuilderService = TestBed.inject(ContextBuilderService) as jasmine.SpyObj<ContextBuilderService>;
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('convertToStructured', () => {
    it('should convert traditional character feedback request to structured format', () => {
      const traditionalRequest: CharacterFeedbackRequest = {
        systemPrompts: {
          mainPrefix: 'Test prefix',
          mainSuffix: 'Test suffix'
        },
        worldbuilding: 'Test worldbuilding',
        storySummary: 'Test summary',
        previousChapters: [
          { number: 1, title: 'Chapter 1', content: 'Chapter content' }
        ],
        character: {
          name: 'Test Character',
          basicBio: 'Test bio',
          sex: 'female',
          gender: 'female',
          sexualPreference: 'heterosexual',
          age: 25,
          physicalAppearance: 'Test appearance',
          usualClothing: 'Test clothing',
          personality: 'Test personality',
          motivations: 'Test motivations',
          fears: 'Test fears',
          relationships: 'Test relationships'
        },
        plotPoint: 'Test plot point'
      };

      const result = service.convertToStructured<StructuredCharacterFeedbackRequest>(traditionalRequest);

      expect(result.success).toBe(true);
      expect(result.convertedRequest).toBeDefined();
      expect(result.originalFormat).toBe('traditional');
      expect(result.targetFormat).toBe('structured');

      const structuredRequest = result.convertedRequest!;
      expect(structuredRequest.systemPrompts.mainPrefix).toBe('Test prefix');
      expect(structuredRequest.worldbuilding.content).toBe('Test worldbuilding');
      expect(structuredRequest.character.name).toBe('Test Character');
      expect(structuredRequest.plotContext.plotPoint).toBe('Test plot point');
    });

    it('should convert traditional rater feedback request to structured format', () => {
      const traditionalRequest: RaterFeedbackRequest = {
        systemPrompts: {
          mainPrefix: 'Test prefix',
          mainSuffix: 'Test suffix'
        },
        raterPrompt: 'Test rater prompt',
        worldbuilding: 'Test worldbuilding',
        storySummary: 'Test summary',
        previousChapters: [
          { number: 1, title: 'Chapter 1', content: 'Chapter content' }
        ],
        plotPoint: 'Test plot point'
      };

      const result = service.convertToStructured<StructuredRaterFeedbackRequest>(traditionalRequest);

      expect(result.success).toBe(true);
      expect(result.convertedRequest).toBeDefined();
      expect(result.originalFormat).toBe('traditional');
      expect(result.targetFormat).toBe('structured');

      const structuredRequest = result.convertedRequest!;
      expect(structuredRequest.raterPrompt).toBe('Test rater prompt');
      expect(structuredRequest.plotContext.plotPoint).toBe('Test plot point');
    });

    it('should convert traditional chapter generation request to structured format', () => {
      const traditionalRequest: GenerateChapterRequest = {
        systemPrompts: {
          mainPrefix: 'Test prefix',
          mainSuffix: 'Test suffix',
          assistantPrompt: 'Test assistant prompt'
        },
        worldbuilding: 'Test worldbuilding',
        storySummary: 'Test summary',
        previousChapters: [
          { number: 1, title: 'Chapter 1', content: 'Chapter content' }
        ],
        characters: [
          {
            name: 'Test Character',
            basicBio: 'Test bio',
            sex: 'female',
            gender: 'female',
            sexualPreference: 'heterosexual',
            age: 25,
            physicalAppearance: 'Test appearance',
            usualClothing: 'Test clothing',
            personality: 'Test personality',
            motivations: 'Test motivations',
            fears: 'Test fears',
            relationships: 'Test relationships'
          }
        ],
        plotPoint: 'Test plot point',
        incorporatedFeedback: [
          {
            source: 'Test source',
            type: 'suggestion',
            content: 'Test feedback',
            incorporated: true
          }
        ]
      };

      const result = service.convertToStructured<StructuredGenerateChapterRequest>(traditionalRequest);

      expect(result.success).toBe(true);
      expect(result.convertedRequest).toBeDefined();
      expect(result.originalFormat).toBe('traditional');
      expect(result.targetFormat).toBe('structured');

      const structuredRequest = result.convertedRequest!;
      expect(structuredRequest.characters.length).toBe(1);
      expect(structuredRequest.characters[0].name).toBe('Test Character');
      expect(structuredRequest.feedbackContext.incorporatedFeedback.length).toBe(1);
    });

    it('should handle already structured requests', () => {
      const structuredRequest: StructuredCharacterFeedbackRequest = {
        systemPrompts: {
          mainPrefix: 'Test prefix',
          mainSuffix: 'Test suffix'
        },
        worldbuilding: {
          content: 'Test worldbuilding',
          lastModified: new Date(),
          wordCount: 2
        },
        storySummary: {
          summary: 'Test summary',
          lastModified: new Date(),
          wordCount: 2
        },
        previousChapters: [
          { number: 1, title: 'Chapter 1', content: 'Chapter content', wordCount: 2 }
        ],
        character: {
          name: 'Test Character',
          basicBio: 'Test bio',
          sex: 'female',
          gender: 'female',
          sexualPreference: 'heterosexual',
          age: 25,
          physicalAppearance: 'Test appearance',
          usualClothing: 'Test clothing',
          personality: 'Test personality',
          motivations: 'Test motivations',
          fears: 'Test fears',
          relationships: 'Test relationships'
        },
        plotContext: {
          plotPoint: 'Test plot point'
        }
      };

      const result = service.convertToStructured<StructuredCharacterFeedbackRequest>(structuredRequest);

      expect(result.success).toBe(true);
      expect(result.convertedRequest).toBe(structuredRequest);
      expect(result.originalFormat).toBe('structured');
      expect(result.warnings).toBeDefined();
      expect(result.warnings![0].message).toContain('already in structured format');
    });

    it('should handle conversion errors gracefully', () => {
      const invalidRequest = null;

      const result = service.convertToStructured(invalidRequest);

      expect(result.success).toBe(false);
      expect(result.errors).toBeDefined();
      expect(result.errors![0].severity).toBe('error');
    });

    it('should validate after conversion when requested', () => {
      const traditionalRequest: CharacterFeedbackRequest = {
        systemPrompts: {
          mainPrefix: '',  // Empty prefix should trigger validation warning
          mainSuffix: 'Test suffix'
        },
        worldbuilding: 'Test worldbuilding',
        storySummary: 'Test summary',
        previousChapters: [],
        character: {
          name: 'Test Character',
          basicBio: 'Test bio',
          sex: 'female',
          gender: 'female',
          sexualPreference: 'heterosexual',
          age: 25,
          physicalAppearance: 'Test appearance',
          usualClothing: 'Test clothing',
          personality: 'Test personality',
          motivations: 'Test motivations',
          fears: 'Test fears',
          relationships: 'Test relationships'
        },
        plotPoint: 'Test plot point'
      };

      const result = service.convertToStructured<StructuredCharacterFeedbackRequest>(
        traditionalRequest,
        { validateAfterConversion: true }
      );

      expect(result.success).toBe(true);
      expect(result.warnings).toBeDefined();
      expect(result.warnings!.length).toBeGreaterThan(0);
    });
  });

  describe('convertToTraditional', () => {
    it('should convert structured character feedback request to traditional format', () => {
      const structuredRequest: StructuredCharacterFeedbackRequest = {
        systemPrompts: {
          mainPrefix: 'Test prefix',
          mainSuffix: 'Test suffix'
        },
        worldbuilding: {
          content: 'Test worldbuilding',
          lastModified: new Date(),
          wordCount: 2
        },
        storySummary: {
          summary: 'Test summary',
          lastModified: new Date(),
          wordCount: 2
        },
        previousChapters: [
          { number: 1, title: 'Chapter 1', content: 'Chapter content', wordCount: 2 }
        ],
        character: {
          name: 'Test Character',
          basicBio: 'Test bio',
          sex: 'female',
          gender: 'female',
          sexualPreference: 'heterosexual',
          age: 25,
          physicalAppearance: 'Test appearance',
          usualClothing: 'Test clothing',
          personality: 'Test personality',
          motivations: 'Test motivations',
          fears: 'Test fears',
          relationships: 'Test relationships'
        },
        plotContext: {
          plotPoint: 'Test plot point'
        }
      };

      const result = service.convertToTraditional<CharacterFeedbackRequest>(structuredRequest);

      expect(result.success).toBe(true);
      expect(result.convertedRequest).toBeDefined();
      expect(result.originalFormat).toBe('structured');
      expect(result.targetFormat).toBe('traditional');

      const traditionalRequest = result.convertedRequest!;
      expect(traditionalRequest.systemPrompts.mainPrefix).toBe('Test prefix');
      expect(traditionalRequest.worldbuilding).toBe('Test worldbuilding');
      expect(traditionalRequest.character.name).toBe('Test Character');
      expect(traditionalRequest.plotPoint).toBe('Test plot point');
    });

    it('should handle unsupported request types', () => {
      const unsupportedRequest = { unsupported: true };

      const result = service.convertToTraditional(unsupportedRequest);

      expect(result.success).toBe(false);
      expect(result.errors).toBeDefined();
      expect(result.errors![0].message).toContain('Unsupported structured request type');
    });
  });

  describe('optimization options', () => {
    it('should preserve metadata when requested', () => {
      const traditionalRequest: CharacterFeedbackRequest = {
        systemPrompts: {
          mainPrefix: 'Test prefix',
          mainSuffix: 'Test suffix'
        },
        worldbuilding: 'Test worldbuilding',
        storySummary: 'Test summary',
        previousChapters: [],
        character: {
          name: 'Test Character',
          basicBio: 'Test bio',
          sex: 'female',
          gender: 'female',
          sexualPreference: 'heterosexual',
          age: 25,
          physicalAppearance: 'Test appearance',
          usualClothing: 'Test clothing',
          personality: 'Test personality',
          motivations: 'Test motivations',
          fears: 'Test fears',
          relationships: 'Test relationships'
        },
        plotPoint: 'Test plot point'
      };

      const result = service.convertToStructured<StructuredCharacterFeedbackRequest>(
        traditionalRequest,
        { preserveMetadata: true }
      );

      expect(result.success).toBe(true);
      expect(result.convertedRequest!.requestMetadata).toBeDefined();
      expect(result.convertedRequest!.requestMetadata!.requestSource).toBe('traditional_conversion');
    });

    it('should add optimization hints when requested', () => {
      const traditionalRequest: CharacterFeedbackRequest = {
        systemPrompts: {
          mainPrefix: 'Test prefix',
          mainSuffix: 'Test suffix'
        },
        worldbuilding: 'Test worldbuilding',
        storySummary: 'Test summary',
        previousChapters: [],
        character: {
          name: 'Test Character',
          basicBio: 'Test bio',
          sex: 'female',
          gender: 'female',
          sexualPreference: 'heterosexual',
          age: 25,
          physicalAppearance: 'Test appearance',
          usualClothing: 'Test clothing',
          personality: 'Test personality',
          motivations: 'Test motivations',
          fears: 'Test fears',
          relationships: 'Test relationships'
        },
        plotPoint: 'Test plot point'
      };

      const result = service.convertToStructured<StructuredCharacterFeedbackRequest>(
        traditionalRequest,
        { preserveMetadata: true, addOptimizationHints: true }
      );

      expect(result.success).toBe(true);
      expect(result.convertedRequest!.requestMetadata!.optimizationHints).toBeDefined();
      expect(result.convertedRequest!.requestMetadata!.optimizationHints).toContain('character_feedback');
    });
  });

  describe('performance', () => {
    it('should complete conversion within reasonable time', () => {
      const traditionalRequest: GenerateChapterRequest = {
        systemPrompts: {
          mainPrefix: 'Test prefix',
          mainSuffix: 'Test suffix',
          assistantPrompt: 'Test assistant prompt'
        },
        worldbuilding: 'Test worldbuilding',
        storySummary: 'Test summary',
        previousChapters: Array.from({ length: 10 }, (_, i) => ({
          number: i + 1,
          title: `Chapter ${i + 1}`,
          content: `Chapter ${i + 1} content`.repeat(100)
        })),
        characters: Array.from({ length: 5 }, (_, i) => ({
          name: `Character ${i + 1}`,
          basicBio: `Bio ${i + 1}`,
          sex: 'female',
          gender: 'female',
          sexualPreference: 'heterosexual',
          age: 25 + i,
          physicalAppearance: `Appearance ${i + 1}`,
          usualClothing: `Clothing ${i + 1}`,
          personality: `Personality ${i + 1}`,
          motivations: `Motivations ${i + 1}`,
          fears: `Fears ${i + 1}`,
          relationships: `Relationships ${i + 1}`
        })),
        plotPoint: 'Test plot point',
        incorporatedFeedback: []
      };

      const startTime = Date.now();
      const result = service.convertToStructured<StructuredGenerateChapterRequest>(traditionalRequest);
      const endTime = Date.now();

      expect(result.success).toBe(true);
      expect(endTime - startTime).toBeLessThan(100); // Should complete within 100ms
      expect(result.metadata!.conversionTime).toBeLessThan(100);
    });
  });
});
