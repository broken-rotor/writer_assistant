/**
 * Context Builder Service Tests
 * 
 * Comprehensive unit tests for the ContextBuilderService covering all
 * context building scenarios, validation, error handling, and caching.
 */

import { TestBed } from '@angular/core/testing';
import { ContextBuilderService } from './context-builder.service';
import { TokenCountingService } from './token-counting.service';
import { Story, Character, FeedbackItem, ConversationThread } from '../models/story.model';
import {
  ContextBuildOptions
} from '../models/context-builder.model';

describe('ContextBuilderService', () => {
  let service: ContextBuilderService;
  let mockTokenCountingService: jasmine.SpyObj<TokenCountingService>;

  // Mock story data
  const mockStory: Story = {
    id: 'test-story-123',
    general: {
      title: 'Test Story Title',
      systemPrompts: {
        mainPrefix: 'Test main prefix',
        mainSuffix: 'Test main suffix',
        assistantPrompt: 'Test assistant prompt',
        editorPrompt: 'Test editor prompt'
      },
      worldbuilding: 'Test worldbuilding content with detailed universe information.'
    },
    story: {
      summary: 'Test story summary describing the main plot.',
      chapters: [
        {
          id: 'chapter-1',
          number: 1,
          title: 'Chapter One',
          content: 'This is the content of chapter one.',
          plotPoint: 'Introduction of main character',
          incorporatedFeedback: [],
          metadata: {
            created: new Date('2023-01-01'),
            lastModified: new Date('2023-01-01'),
            wordCount: 100
          }
        },
        {
          id: 'chapter-2',
          number: 2,
          title: 'Chapter Two',
          content: 'This is the content of chapter two.',
          plotPoint: 'First conflict arises',
          incorporatedFeedback: [],
          metadata: {
            created: new Date('2023-01-02'),
            lastModified: new Date('2023-01-02'),
            wordCount: 150
          }
        }
      ]
    },
    characters: new Map([
      ['char1', {
        id: 'char1',
        name: 'John Doe',
        basicBio: 'A brave hero',
        sex: 'male',
        gender: 'male',
        sexualPreference: 'heterosexual',
        age: 25,
        physicalAppearance: 'Tall and strong',
        usualClothing: 'Leather armor',
        personality: 'Brave and loyal',
        motivations: 'Save the kingdom',
        fears: 'Losing loved ones',
        relationships: 'Friend of Jane',
        isHidden: false,
        metadata: {
          creationSource: 'user' as const,
          lastModified: new Date('2023-01-01')
        }
      } as Character],
      ['char2', {
        id: 'char2',
        name: 'Jane Smith',
        basicBio: 'A wise mage',
        sex: 'female',
        gender: 'female',
        sexualPreference: 'heterosexual',
        age: 30,
        physicalAppearance: 'Elegant and mysterious',
        usualClothing: 'Robes',
        personality: 'Wise and cautious',
        motivations: 'Protect ancient knowledge',
        fears: 'Dark magic',
        relationships: 'Friend of John',
        isHidden: false,
        metadata: {
          creationSource: 'user' as const,
          lastModified: new Date('2023-01-01')
        }
      } as Character],
      ['char3', {
        id: 'char3',
        name: 'Hidden Character',
        basicBio: 'A secret character',
        sex: 'unknown',
        gender: 'unknown',
        sexualPreference: 'unknown',
        age: 0,
        physicalAppearance: 'Unknown',
        usualClothing: 'Unknown',
        personality: 'Mysterious',
        motivations: 'Unknown',
        fears: 'Unknown',
        relationships: 'Unknown',
        isHidden: true,
        metadata: {
          creationSource: 'ai_generated' as const,
          lastModified: new Date('2023-01-01')
        }
      } as Character]
    ]),
    raters: new Map(),
    plotOutline: {
      content: 'Test plot outline content',
      status: 'draft' as const,
      chatHistory: [],
      raterFeedback: new Map(),
      metadata: {
        created: new Date('2023-01-01'),
        lastModified: new Date('2023-01-01'),
        version: 1
      }
    },
    metadata: {
      version: '1.0.0',
      created: new Date('2023-01-01'),
      lastModified: new Date('2023-01-01')
    }
  } as Story;

  const mockFeedbackItems: FeedbackItem[] = [
    {
      source: 'Character Agent',
      content: 'Great character development',
      type: 'suggestion',
      incorporated: false
    },
    {
      source: 'Narrative Agent',
      content: 'Improve pacing',
      type: 'suggestion',
      incorporated: true
    }
  ];

  const mockConversationThread: ConversationThread = {
    id: 'thread1',
    currentBranchId: 'branch1',
    messages: [
      {
        id: 'msg1',
        type: 'user',
        content: 'Please write a dramatic scene',
        timestamp: new Date('2023-01-01T10:00:00Z')
      },
      {
        id: 'msg2',
        type: 'assistant',
        content: 'Here is a dramatic scene...',
        timestamp: new Date('2023-01-01T10:01:00Z')
      },
      {
        id: 'msg3',
        type: 'user',
        content: 'Make it more emotional',
        timestamp: new Date('2023-01-01T10:02:00Z')
      }
    ]
  } as ConversationThread;

  beforeEach(() => {
    const tokenCountingSpy = jasmine.createSpyObj('TokenCountingService', ['countWords']);

    TestBed.configureTestingModule({
      providers: [
        ContextBuilderService,
        { provide: TokenCountingService, useValue: tokenCountingSpy }
      ]
    });

    service = TestBed.inject(ContextBuilderService);
    mockTokenCountingService = TestBed.inject(TokenCountingService) as jasmine.SpyObj<TokenCountingService>;

    // Setup default mock behavior
    mockTokenCountingService.countWords.and.returnValue(10);
  });

  describe('Service Initialization', () => {
    it('should be created', () => {
      expect(service).toBeTruthy();
    });

    it('should initialize with empty cache', () => {
      expect(service['contextCache'].size).toBe(0);
    });
  });

  describe('buildSystemPromptsContext', () => {
    it('should build valid system prompts context', () => {
      const result = service.buildSystemPromptsContext(mockStory);

      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      expect(result.data!.mainPrefix).toBe('Test main prefix');
      expect(result.data!.mainSuffix).toBe('Test main suffix');
      expect(result.data!.assistantPrompt).toBe('Test assistant prompt');
      expect(result.fromCache).toBe(false);
    });

    it('should handle empty system prompts', () => {
      const storyWithEmptyPrompts = {
        ...mockStory,
        general: {
          ...mockStory.general,
          systemPrompts: {
            mainPrefix: '',
            mainSuffix: '',
            assistantPrompt: '',
            editorPrompt: ''
          }
        }
      };

      const result = service.buildSystemPromptsContext(storyWithEmptyPrompts);

      expect(result.success).toBe(true);
      expect(result.errors).toBeDefined();
      expect(result.errors!.length).toBe(1);
      expect(result.errors![0].field).toBe('assistantPrompt');
      expect(result.warnings).toBeDefined();
      expect(result.warnings!.length).toBe(1);
      expect(result.warnings![0].field).toBe('mainPrefix');
    });

    it('should use cache when available', () => {
      // First call
      const result1 = service.buildSystemPromptsContext(mockStory);
      expect(result1.fromCache).toBe(false);

      // Second call should use cache
      const result2 = service.buildSystemPromptsContext(mockStory);
      expect(result2.fromCache).toBe(true);
      expect(result2.cacheAge).toBeDefined();
    });

    it('should bypass cache when useCache is false', () => {
      const options: ContextBuildOptions = { useCache: false };
      
      const result1 = service.buildSystemPromptsContext(mockStory, options);
      const result2 = service.buildSystemPromptsContext(mockStory, options);

      expect(result1.fromCache).toBe(false);
      expect(result2.fromCache).toBe(false);
    });
  });

  describe('buildWorldbuildingContext', () => {
    it('should build valid worldbuilding context', () => {
      mockTokenCountingService.countWords.and.returnValue(8);

      const result = service.buildWorldbuildingContext(mockStory);

      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      expect(result.data!.content).toBe('Test worldbuilding content with detailed universe information.');
      expect(result.data!.isValid).toBe(true);
      expect(result.data!.wordCount).toBe(8);
      expect(result.data!.lastUpdated).toBeInstanceOf(Date);
    });

    it('should handle empty worldbuilding', () => {
      const storyWithEmptyWorldbuilding = {
        ...mockStory,
        general: {
          ...mockStory.general,
          worldbuilding: ''
        }
      };

      const result = service.buildWorldbuildingContext(storyWithEmptyWorldbuilding);

      expect(result.success).toBe(true);
      expect(result.data!.isValid).toBe(false);
      expect(result.warnings).toBeDefined();
      expect(result.warnings!.length).toBe(1);
      expect(result.warnings![0].field).toBe('content');
    });

    it('should warn about very long worldbuilding', () => {
      mockTokenCountingService.countWords.and.returnValue(6000);

      const result = service.buildWorldbuildingContext(mockStory);

      expect(result.success).toBe(true);
      expect(result.warnings).toBeDefined();
      expect(result.warnings!.some(w => w.message.includes('very long'))).toBe(true);
    });
  });

  describe('buildStorySummaryContext', () => {
    it('should build valid story summary context', () => {
      mockTokenCountingService.countWords.and.returnValue(7);

      const result = service.buildStorySummaryContext(mockStory);

      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      expect(result.data!.summary).toBe('Test story summary describing the main plot.');
      expect(result.data!.isValid).toBe(true);
      expect(result.data!.wordCount).toBe(7);
    });

    it('should handle empty story summary', () => {
      const storyWithEmptySummary = {
        ...mockStory,
        story: {
          ...mockStory.story,
          summary: ''
        }
      };

      const result = service.buildStorySummaryContext(storyWithEmptySummary);

      expect(result.success).toBe(true);
      expect(result.data!.isValid).toBe(false);
      expect(result.warnings).toBeDefined();
      expect(result.warnings!.length).toBe(1);
    });
  });

  describe('buildCharacterContext', () => {
    it('should build valid character context', () => {
      const result = service.buildCharacterContext(mockStory);

      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      expect(result.data!.characters.length).toBe(2); // Only visible characters
      expect(result.data!.totalCharacters).toBe(3); // All characters
      expect(result.data!.visibleCharacters).toBe(2);
      expect(result.data!.characters[0].name).toBe('John Doe');
      expect(result.data!.characters[1].name).toBe('Jane Smith');
    });

    it('should handle story with no characters', () => {
      const storyWithNoCharacters = {
        ...mockStory,
        characters: new Map()
      };

      const result = service.buildCharacterContext(storyWithNoCharacters);

      expect(result.success).toBe(true);
      expect(result.data!.visibleCharacters).toBe(0);
      expect(result.warnings).toBeDefined();
      expect(result.warnings!.some(w => w.message.includes('No visible characters'))).toBe(true);
    });

    it('should validate character names', () => {
      const storyWithInvalidCharacter = {
        ...mockStory,
        characters: new Map([
          ['char1', {
            id: 'char1',
            name: '', // Empty name
            basicBio: 'A character without a name',
            isHidden: false
          } as Character]
        ])
      };

      const result = service.buildCharacterContext(storyWithInvalidCharacter);

      expect(result.success).toBe(true);
      expect(result.errors).toBeDefined();
      expect(result.errors!.some(e => e.field.includes('name'))).toBe(true);
    });
  });

  describe('buildChaptersContext', () => {
    it('should build valid chapters context', () => {
      mockTokenCountingService.countWords.and.callFake((text: string) => {
        return text === 'This is the content of chapter one.' ? 7 : 8;
      });

      const result = service.buildChaptersContext(mockStory);

      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      expect(result.data!.chapters.length).toBe(2);
      expect(result.data!.totalChapters).toBe(2);
      expect(result.data!.totalWordCount).toBe(15); // 7 + 8
      expect(result.data!.chapters[0].number).toBe(1);
      expect(result.data!.chapters[0].title).toBe('Chapter One');
    });

    it('should handle story with many chapters', () => {
      const storyWithManyChapters = {
        ...mockStory,
        story: {
          ...mockStory.story,
          chapters: Array.from({ length: 60 }, (_, i) => ({
            id: `chapter-${i + 1}`,
            number: i + 1,
            title: `Chapter ${i + 1}`,
            content: `Content ${i + 1}`,
            plotPoint: `Plot point ${i + 1}`,
            incorporatedFeedback: [],
            metadata: {
              created: new Date(),
              lastModified: new Date(),
              wordCount: 50
            }
          }))
        }
      };

      const result = service.buildChaptersContext(storyWithManyChapters);

      expect(result.success).toBe(true);
      expect(result.warnings).toBeDefined();
      expect(result.warnings!.some(w => w.message.includes('Large number of chapters'))).toBe(true);
    });
  });

  describe('buildPlotContext', () => {
    it('should build valid plot context', () => {
      const plotPoint = 'The hero discovers a hidden truth about their past.';
      mockTokenCountingService.countWords.and.returnValue(9);

      const result = service.buildPlotContext(plotPoint);

      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      expect(result.data!.plotPoint).toBe(plotPoint);
      expect(result.data!.isValid).toBe(true);
      expect(result.data!.wordCount).toBe(9);
    });

    it('should handle empty plot point', () => {
      const result = service.buildPlotContext('');

      expect(result.success).toBe(true);
      expect(result.data!.isValid).toBe(false);
      expect(result.errors).toBeDefined();
      expect(result.errors!.some(e => e.message.includes('required'))).toBe(true);
    });
  });

  describe('buildFeedbackContext', () => {
    it('should build valid feedback context', () => {
      const result = service.buildFeedbackContext(mockFeedbackItems, []);

      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      expect(result.data!.incorporatedFeedback.length).toBe(2);
      expect(result.data!.selectedFeedback.length).toBe(0);
      expect(result.data!.totalFeedbackItems).toBe(2);
    });

    it('should handle large number of feedback items', () => {
      const manyFeedbackItems = Array.from({ length: 25 }, (_, i) => ({
        source: `Agent ${i}`,
        content: `Feedback ${i}`,
        type: 'suggestion' as const,
        incorporated: i % 2 === 0
      }));

      const result = service.buildFeedbackContext(manyFeedbackItems, []);

      expect(result.success).toBe(true);
      expect(result.warnings).toBeDefined();
      expect(result.warnings!.some(w => w.message.includes('Large number of feedback'))).toBe(true);
    });
  });

  describe('buildConversationContext', () => {
    it('should build valid conversation context', () => {
      const result = service.buildConversationContext(mockConversationThread, 5);

      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      expect(result.data!.messages.length).toBe(3);
      expect(result.data!.branchId).toBe('branch1');
      expect(result.data!.totalMessages).toBe(3);
      expect(result.data!.recentMessages.length).toBe(3);
      expect(result.data!.messages[0].role).toBe('user');
      expect(result.data!.messages[1].role).toBe('assistant');
    });

    it('should handle empty conversation thread', () => {
      const result = service.buildConversationContext(undefined);

      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      expect(result.data!.messages.length).toBe(0);
      expect(result.data!.totalMessages).toBe(0);
      expect(result.data!.branchId).toBe('');
    });

    it('should limit recent messages', () => {
      const result = service.buildConversationContext(mockConversationThread, 2);

      expect(result.success).toBe(true);
      expect(result.data!.recentMessages.length).toBe(2);
      expect(result.data!.recentMessages[0].content).toBe('Here is a dramatic scene...');
      expect(result.data!.recentMessages[1].content).toBe('Make it more emotional');
    });

    it('should warn about large conversation history', () => {
      const largeConversationThread = {
        ...mockConversationThread,
        messages: Array.from({ length: 150 }, (_, i) => ({
          id: `msg${i}`,
          type: i % 2 === 0 ? 'user' : 'assistant',
          content: `Message ${i}`,
          timestamp: new Date()
        }))
      } as ConversationThread;

      const result = service.buildConversationContext(largeConversationThread);

      expect(result.success).toBe(true);
      expect(result.warnings).toBeDefined();
      expect(result.warnings!.some(w => w.message.includes('Large conversation history'))).toBe(true);
    });
  });

  // buildPhaseContext tests removed - functionality no longer exists

  describe('buildChapterGenerationContext', () => {
    it('should build complete chapter generation context', () => {
      mockTokenCountingService.countWords.and.returnValue(10);

      const result = service.buildChapterGenerationContext(
        mockStory,
        'Hero discovers the truth',
        mockFeedbackItems,
        mockConversationThread
      );

      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      expect(result.data!.systemPrompts).toBeDefined();
      expect(result.data!.worldbuilding).toBeDefined();
      expect(result.data!.storySummary).toBeDefined();
      expect(result.data!.characters).toBeDefined();
      expect(result.data!.previousChapters).toBeDefined();
      expect(result.data!.plotPoint).toBeDefined();
      expect(result.data!.feedback).toBeDefined();
      expect(result.data!.conversation).toBeDefined();
    });

    it('should handle context building failures', () => {
      const invalidStory = {
        ...mockStory,
        general: {
          ...mockStory.general,
          systemPrompts: {
            mainPrefix: '',
            mainSuffix: '',
            assistantPrompt: '', // This will cause validation error
            editorPrompt: ''
          }
        }
      };

      const result = service.buildChapterGenerationContext(invalidStory, '');

      expect(result.success).toBe(true); // Service succeeds but has errors
      expect(result.errors).toBeDefined();
      expect(result.errors!.length).toBeGreaterThan(0);
    });
  });

  describe('Cache Management', () => {
    it('should clear all cache', () => {
      // Build some contexts to populate cache
      service.buildSystemPromptsContext(mockStory);
      service.buildWorldbuildingContext(mockStory);

      expect(service['contextCache'].size).toBeGreaterThan(0);

      service.clearCache();

      expect(service['contextCache'].size).toBe(0);
    });

    it('should clear story-specific cache', () => {
      // Build contexts for different stories
      service.buildSystemPromptsContext(mockStory);
      service.buildSystemPromptsContext({ ...mockStory, id: 'other-story' });

      expect(service['contextCache'].size).toBe(2);

      service.clearStoryCache('test-story-123');

      expect(service['contextCache'].size).toBe(1);
      expect(Array.from(service['contextCache'].keys())[0]).toContain('other-story');
    });

    it('should respect cache age limits', (done) => {
      const options: ContextBuildOptions = { maxCacheAge: 100 }; // 100ms

      const result1 = service.buildSystemPromptsContext(mockStory, options);
      expect(result1.fromCache).toBe(false);

      // Immediately should use cache
      const result2 = service.buildSystemPromptsContext(mockStory, options);
      expect(result2.fromCache).toBe(true);

      // After cache expires
      setTimeout(() => {
        const result3 = service.buildSystemPromptsContext(mockStory, options);
        expect(result3.fromCache).toBe(false);
        done();
      }, 150);
    });
  });

  describe('Error Handling', () => {
    it('should handle token counting service errors gracefully', () => {
      mockTokenCountingService.countWords.and.throwError('Token counting failed');

      const result = service.buildWorldbuildingContext(mockStory);

      expect(result.success).toBe(false);
      expect(result.errors).toBeDefined();
      expect(result.errors![0].message).toContain('Failed to build worldbuilding context');
    });

    it('should handle malformed story data', () => {
      const malformedStory = {
        id: 'test',
        general: null, // This will cause errors
        story: null,
        characters: null
      } as any;

      const result = service.buildSystemPromptsContext(malformedStory);

      expect(result.success).toBe(false);
      expect(result.errors).toBeDefined();
    });
  });

  describe('Validation Edge Cases', () => {
    it('should handle undefined optional fields gracefully', () => {
      const minimalStory = {
        id: 'minimal',
        general: {
          systemPrompts: {
            mainPrefix: undefined,
            mainSuffix: undefined,
            assistantPrompt: 'Required prompt'
          },
          worldbuilding: undefined
        },
        story: {
          summary: undefined,
          chapters: []
        },
        characters: new Map()
      } as any;

      const systemPromptsResult = service.buildSystemPromptsContext(minimalStory);
      const worldbuildingResult = service.buildWorldbuildingContext(minimalStory);
      const storySummaryResult = service.buildStorySummaryContext(minimalStory);

      expect(systemPromptsResult.success).toBe(true);
      expect(worldbuildingResult.success).toBe(true);
      expect(storySummaryResult.success).toBe(true);
    });
  });
});
