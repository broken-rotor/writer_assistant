import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { ChapterEditorService } from './chapter-editor.service';
import { GenerationService } from './generation.service';
import { ApiService } from './api.service';
import { ContextBuilderService } from './context-builder.service';
import { Chapter, Story } from '../models/story.model';

describe('ChapterEditorService', () => {
  let service: ChapterEditorService;
  let mockGenerationService: jasmine.SpyObj<GenerationService>;
  let mockApiService: jasmine.SpyObj<ApiService>;
  let mockContextBuilder: jasmine.SpyObj<ContextBuilderService>;

  const mockChapter: Chapter = {
    id: '1',
    number: 1,
    title: 'Test Chapter',
    content: 'Test content',
    plotPoint: 'Test plot point',
    incorporatedFeedback: [],
    metadata: {
      created: new Date(),
      lastModified: new Date(),
      wordCount: 2
    }
  };

  const mockStory: Story = {
    id: '1',
    general: {
      title: 'Test Story',
      systemPrompts: {
        mainPrefix: '',
        mainSuffix: '',
        assistantPrompt: '',
        editorPrompt: ''
      },
      worldbuilding: 'Test world'
    },
    characters: new Map(),
    raters: new Map(),
    story: {
      summary: 'Test summary',
      chapters: [mockChapter]
    },
    plotOutline: {
      content: 'Test outline',
      status: 'draft',
      chatHistory: [],
      raterFeedback: new Map(),
      metadata: {
        created: new Date(),
        lastModified: new Date(),
        version: 1
      }
    },
    metadata: {
      version: '1.0',
      created: new Date(),
      lastModified: new Date()
    }
  };

  beforeEach(() => {
    const generationSpy = jasmine.createSpyObj('GenerationService', [
      'generateChapter',
      'modifyChapter',
      'requestCharacterFeedback',
      'requestRaterFeedback'
    ]);
    const apiSpy = jasmine.createSpyObj('ApiService', ['llmChat']);
    const contextSpy = jasmine.createSpyObj('ContextBuilderService', [
      'buildChapterGenerationContext',
      'buildStorySummaryContext'
    ]);

    TestBed.configureTestingModule({
      providers: [
        ChapterEditorService,
        { provide: GenerationService, useValue: generationSpy },
        { provide: ApiService, useValue: apiSpy },
        { provide: ContextBuilderService, useValue: contextSpy }
      ]
    });

    service = TestBed.inject(ChapterEditorService);
    mockGenerationService = TestBed.inject(GenerationService) as jasmine.SpyObj<GenerationService>;
    mockApiService = TestBed.inject(ApiService) as jasmine.SpyObj<ApiService>;
    mockContextBuilder = TestBed.inject(ContextBuilderService) as jasmine.SpyObj<ContextBuilderService>;
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should initialize chapter editing', () => {
    service.initializeChapterEditing(mockChapter);
    
    service.state$.subscribe(state => {
      expect(state.currentChapter).toEqual(mockChapter);
      expect(state.hasUnsavedChanges).toBeFalse();
    });
  });

  it('should update chapter content', () => {
    service.initializeChapterEditing(mockChapter);
    const newContent = 'Updated content';
    
    service.updateChapterContent(newContent);
    
    service.state$.subscribe(state => {
      expect(state.currentChapter?.content).toBe(newContent);
      expect(state.hasUnsavedChanges).toBeTrue();
      expect(state.currentChapter?.metadata.wordCount).toBe(2); // "Updated content" = 2 words
    });
  });

  it('should update chapter title', () => {
    service.initializeChapterEditing(mockChapter);
    const newTitle = 'Updated Title';
    
    service.updateChapterTitle(newTitle);
    
    service.state$.subscribe(state => {
      expect(state.currentChapter?.title).toBe(newTitle);
      expect(state.hasUnsavedChanges).toBeTrue();
    });
  });

  it('should generate chapter from outline', () => {
    const mockResponse = { chapterText: 'Generated content' };
    // No context builder call needed - generateChapter handles it internally
    mockGenerationService.generateChapter.and.returnValue(of(mockResponse));
    
    service.initializeChapterEditing(mockChapter);
    
    service.generateChapterFromOutline(mockStory).subscribe(content => {
      expect(content).toBe('Generated content');
    });
    
    service.state$.subscribe(state => {
      expect(state.currentChapter?.content).toBe('Generated content');
      expect(state.hasUnsavedChanges).toBeTrue();
    });
  });

  it('should handle generation error', () => {
    const error = new Error('Generation failed');
    // No context builder call needed - generateChapter handles it internally
    mockGenerationService.generateChapter.and.returnValue(throwError(() => error));
    
    service.initializeChapterEditing(mockChapter);
    
    service.generateChapterFromOutline(mockStory).subscribe({
      next: () => fail('Should have failed'),
      error: (err) => {
        expect(err).toBe(error);
      }
    });
    
    service.error$.subscribe(errorMessage => {
      expect(errorMessage).toContain('Failed to generate chapter');
    });
  });

  it('should send chat message', () => {
    const mockResponse = { 
      message: { role: 'assistant' as const, content: 'AI response' },
      agent_type: 'writer' as const,
      metadata: {}
    };
    mockContextBuilder.buildStorySummaryContext.and.returnValue({ 
      success: true,
      data: { 
        summary: 'Test summary', 
        isValid: true, 
        wordCount: 100, 
        lastUpdated: new Date() 
      } 
    });
    mockApiService.llmChat.and.returnValue(of(mockResponse));
    
    service.initializeChapterEditing(mockChapter);
    
    service.sendChatMessage('Test message', mockStory).subscribe(response => {
      expect(response).toBe('AI response');
    });
    
    service.state$.subscribe(state => {
      expect(state.chatHistory.length).toBe(2); // User message + AI response
      expect(state.chatHistory[0].content).toBe('Test message');
      expect(state.chatHistory[1].content).toBe('AI response');
    });
  });

  it('should apply user guidance', () => {
    const mockResponse = { 
      modifiedChapter: 'Modified content',
      wordCount: 2,
      changesSummary: 'Applied guidance'
    };
    // No context builder call needed - modifyChapter handles it internally
    mockGenerationService.modifyChapter.and.returnValue(of(mockResponse));
    
    service.initializeChapterEditing(mockChapter);
    
    service.applyUserGuidance('Make it better', mockStory).subscribe(content => {
      expect(content).toBe('Modified content');
    });
    
    service.state$.subscribe(state => {
      expect(state.currentChapter?.content).toBe('Modified content');
      expect(state.hasUnsavedChanges).toBeTrue();
    });
  });

  it('should clear chat history', () => {
    const mockResponse = {
      message: { role: 'assistant' as const, content: 'Test response' },
      agent_type: 'writer' as const,
      metadata: {}
    };
    mockContextBuilder.buildStorySummaryContext.and.returnValue({
      success: true,
      data: {
        summary: 'Test summary',
        isValid: true,
        wordCount: 100,
        lastUpdated: new Date()
      }
    });
    mockApiService.llmChat.and.returnValue(of(mockResponse));

    service.initializeChapterEditing(mockChapter);

    // Add some chat history first by sending a message
    service.sendChatMessage('Test message', mockStory).subscribe();

    // Verify chat history has messages
    const stateBeforeClear = service['stateSubject'].value;
    expect(stateBeforeClear.chatHistory.length).toBe(2); // User message + AI response

    service.clearChatHistory();

    // Verify chat history is cleared
    const stateAfterClear = service['stateSubject'].value;
    expect(stateAfterClear.chatHistory.length).toBe(0);
  });

  it('should mark as saved', () => {
    service.initializeChapterEditing(mockChapter);
    service.updateChapterContent('New content'); // This sets hasUnsavedChanges to true
    
    service.markAsSaved();
    
    service.state$.subscribe(state => {
      expect(state.hasUnsavedChanges).toBeFalse();
    });
  });

  it('should reset service state', () => {
    service.initializeChapterEditing(mockChapter);
    service.updateChapterContent('New content');
    
    service.reset();
    
    service.state$.subscribe(state => {
      expect(state.currentChapter).toBeNull();
      expect(state.hasUnsavedChanges).toBeFalse();
      expect(state.chatHistory.length).toBe(0);
    });
  });
});
