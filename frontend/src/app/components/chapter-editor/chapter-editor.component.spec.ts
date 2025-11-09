import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { MatSnackBar } from '@angular/material/snack-bar';
import { of } from 'rxjs';

import { ChapterEditorComponent } from './chapter-editor.component';
import { ChapterEditorService } from '../../services/chapter-editor.service';
import { Chapter, Story } from '../../models/story.model';

describe('ChapterEditorComponent', () => {
  let component: ChapterEditorComponent;
  let fixture: ComponentFixture<ChapterEditorComponent>;
  let mockChapterEditorService: jasmine.SpyObj<ChapterEditorService>;
  let mockSnackBar: jasmine.SpyObj<MatSnackBar>;

  const mockChapter: Chapter = {
    id: '1',
    number: 1,
    title: 'Test Chapter',
    content: 'Test content',
    plotPoint: 'Test plot point',
    keyPlotItems: ['Item 1', 'Item 2'],
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

  beforeEach(async () => {
    const chapterEditorSpy = jasmine.createSpyObj('ChapterEditorService', [
      'initializeChapterEditing',
      'updateChapterTitle',
      'updateChapterContent',
      'updateChapterPlotPoint',
      'addKeyPlotItem',
      'removeKeyPlotItem',
      'generateChapterFromOutline',
      'sendChatMessage',
      'getCharacterFeedback',
      'getRaterFeedback',
      'applyUserGuidance',
      'clearFeedback',
      'clearChatHistory',
      'markAsSaved'
    ], {
      state$: of({
        currentChapter: mockChapter,
        isGenerating: false,
        isGettingFeedback: false,
        isApplyingGuidance: false,
        isChatting: false,
        chatHistory: [],
        characterFeedback: [],
        raterFeedback: [],
        userGuidance: '',
        hasUnsavedChanges: false
      }),
      error$: of()
    });

    const snackBarSpy = jasmine.createSpyObj('MatSnackBar', ['open']);

    await TestBed.configureTestingModule({
      imports: [
        ChapterEditorComponent,
        NoopAnimationsModule
      ],
      providers: [
        { provide: ChapterEditorService, useValue: chapterEditorSpy },
        { provide: MatSnackBar, useValue: snackBarSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ChapterEditorComponent);
    component = fixture.componentInstance;
    component.chapter = mockChapter;
    component.story = mockStory;
    
    mockChapterEditorService = TestBed.inject(ChapterEditorService) as jasmine.SpyObj<ChapterEditorService>;
    mockSnackBar = TestBed.inject(MatSnackBar) as jasmine.SpyObj<MatSnackBar>;
    
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize chapter editing on init', () => {
    expect(mockChapterEditorService.initializeChapterEditing).toHaveBeenCalledWith(mockChapter);
  });

  it('should update chapter title', () => {
    const newTitle = 'New Title';
    component.onTitleChange(newTitle);
    expect(mockChapterEditorService.updateChapterTitle).toHaveBeenCalledWith(newTitle);
  });

  it('should update chapter content', () => {
    const newContent = 'New content';
    component.onContentChange(newContent);
    expect(mockChapterEditorService.updateChapterContent).toHaveBeenCalledWith(newContent);
  });

  it('should update plot point', () => {
    const newPlotPoint = 'New plot point';
    component.onPlotPointChange(newPlotPoint);
    expect(mockChapterEditorService.updateChapterPlotPoint).toHaveBeenCalledWith(newPlotPoint);
  });

  it('should add plot item', () => {
    const newItem = 'New plot item';
    component.onAddPlotItem(newItem);
    expect(mockChapterEditorService.addKeyPlotItem).toHaveBeenCalledWith(newItem);
  });

  it('should not add empty plot item', () => {
    component.onAddPlotItem('   ');
    expect(mockChapterEditorService.addKeyPlotItem).not.toHaveBeenCalled();
  });

  it('should remove plot item', () => {
    const index = 1;
    component.onRemovePlotItem(index);
    expect(mockChapterEditorService.removeKeyPlotItem).toHaveBeenCalledWith(index);
  });

  it('should generate chapter', () => {
    mockChapterEditorService.generateChapterFromOutline.and.returnValue(of('Generated content'));
    
    component.onGenerateChapter();
    
    expect(mockChapterEditorService.generateChapterFromOutline).toHaveBeenCalledWith(mockStory);
    expect(mockSnackBar.open).toHaveBeenCalledWith('Chapter generated successfully!', 'Close', jasmine.any(Object));
  });

  it('should send chat message', () => {
    const message = 'Test message';
    mockChapterEditorService.sendChatMessage.and.returnValue(of('AI response'));
    
    component.onChatMessage(message);
    
    expect(mockChapterEditorService.sendChatMessage).toHaveBeenCalledWith(message, mockStory);
  });

  it('should apply user guidance', () => {
    component.userGuidanceText = 'Make it better';
    mockChapterEditorService.applyUserGuidance.and.returnValue(of('Modified content'));
    
    component.onApplyUserGuidance();
    
    expect(mockChapterEditorService.applyUserGuidance).toHaveBeenCalledWith('Make it better', mockStory);
    expect(component.userGuidanceText).toBe('');
  });

  it('should save chapter', () => {
    component.state.currentChapter = mockChapter;
    
    component.onSaveChapter();
    
    expect(mockChapterEditorService.markAsSaved).toHaveBeenCalled();
    expect(mockSnackBar.open).toHaveBeenCalledWith('Chapter saved!', 'Close', jasmine.any(Object));
  });

  it('should get word count', () => {
    component.state.currentChapter = mockChapter;
    expect(component.getWordCount()).toBe(2);
  });

  it('should check if has content', () => {
    component.state.currentChapter = mockChapter;
    expect(component.hasContent()).toBeTrue();
    
    component.state.currentChapter.content = '';
    expect(component.hasContent()).toBeFalse();
  });

  it('should check if can generate', () => {
    component.state.isGenerating = false;
    component.disabled = false;
    expect(component.canGenerate()).toBeTrue();
    
    component.state.isGenerating = true;
    expect(component.canGenerate()).toBeFalse();
  });
});
