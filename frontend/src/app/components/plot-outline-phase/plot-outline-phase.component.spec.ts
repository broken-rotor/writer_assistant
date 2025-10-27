import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { DragDropModule } from '@angular/cdk/drag-drop';
import { of, throwError } from 'rxjs';

import { PlotOutlinePhaseComponent } from './plot_outline-phase.component';
import { GenerationService } from '../../services/generation.service';
import { ArchiveService } from '../../services/archive.service';
import { ConversationService } from '../../services/conversation.service';
import { PhaseStateService } from '../../services/phase-state.service';
import { StoryService } from '../../services/story.service';
import { ToastService } from '../../services/toast.service';
import { Story, ChatMessage } from '../../models/story.model';
import { NewlineToBrPipe } from '../../pipes/newline-to-br.pipe';

describe('PlotOutlinePhaseComponent', () => {
  let component: PlotOutlinePhaseComponent;
  let fixture: ComponentFixture<PlotOutlinePhaseComponent>;
  let mockGenerationService: jasmine.SpyObj<GenerationService>;
  let mockArchiveService: jasmine.SpyObj<ArchiveService>;
  let mockConversationService: jasmine.SpyObj<ConversationService>;
  let mockPhaseStateService: jasmine.SpyObj<PhaseStateService>;
  let mockStoryService: jasmine.SpyObj<StoryService>;
  let mockToastService: jasmine.SpyObj<ToastService>;

  const mockStory: Story = {
    id: 'test-story-1',
    general: {
      title: 'Test Story',
      systemPrompts: {
        mainPrefix: '',
        mainSuffix: '',
        assistantPrompt: '',
        editorPrompt: ''
      },
      worldbuilding: 'Test worldbuilding'
    },
    characters: new Map(),
    raters: new Map(),
    story: {
      summary: 'Test summary',
      chapters: []
    },
    chapterCreation: {
      plotPoint: 'Test plot point',
      incorporatedFeedback: [],
      feedbackRequests: new Map()
    },
    metadata: {
      version: '1.0.0',
      created: new Date(),
      lastModified: new Date()
    }
  };

  beforeEach(async () => {
    const generationServiceSpy = jasmine.createSpyObj('GenerationService', ['fleshOut']);
    const archiveServiceSpy = jasmine.createSpyObj('ArchiveService', ['ragQuery']);
    const conversationServiceSpy = jasmine.createSpyObj('ConversationService', ['sendMessage', 'initializeConversation']);
    const phaseStateServiceSpy = jasmine.createSpyObj('PhaseStateService', ['updatePhaseValidation']);
    const storyServiceSpy = jasmine.createSpyObj('StoryService', ['saveStory']);
    const toastServiceSpy = jasmine.createSpyObj('ToastService', ['showSuccess', 'showError']);

    await TestBed.configureTestingModule({
      imports: [
        PlotOutlinePhaseComponent,
        FormsModule,
        DragDropModule,
        NewlineToBrPipe
      ],
      providers: [
        { provide: GenerationService, useValue: generationServiceSpy },
        { provide: ArchiveService, useValue: archiveServiceSpy },
        { provide: ConversationService, useValue: conversationServiceSpy },
        { provide: PhaseStateService, useValue: phaseStateServiceSpy },
        { provide: StoryService, useValue: storyServiceSpy },
        { provide: ToastService, useValue: toastServiceSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(PlotOutlinePhaseComponent);
    component = fixture.componentInstance;
    component.story = mockStory;
    component.chapterNumber = 1;

    mockGenerationService = TestBed.inject(GenerationService) as jasmine.SpyObj<GenerationService>;
    mockArchiveService = TestBed.inject(ArchiveService) as jasmine.SpyObj<ArchiveService>;
    mockConversationService = TestBed.inject(ConversationService) as jasmine.SpyObj<ConversationService>;
    mockPhaseStateService = TestBed.inject(PhaseStateService) as jasmine.SpyObj<PhaseStateService>;
    mockStoryService = TestBed.inject(StoryService) as jasmine.SpyObj<StoryService>;
    mockToastService = TestBed.inject(ToastService) as jasmine.SpyObj<ToastService>;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with basic outline from story plot point', () => {
    fixture.detectChanges();
    expect(component.basicOutline).toBe('Test plot point');
  });

  it('should setup chat config with story id and chapter number', () => {
    fixture.detectChanges();
    expect(component.chatConfig.storyId).toBe('test-story-1');
    expect(component.chatConfig.chapterNumber).toBe(1);
    expect(component.chatConfig.phase).toBe('plot_outline');
  });

  describe('Basic Outline Functionality', () => {
    it('should update story plot point when basic outline changes', () => {
      fixture.detectChanges();
      component.basicOutline = 'Updated plot point';
      component.onBasicOutlineChange();
      
      expect(component.story.chapterCreation.plotPoint).toBe('Updated plot point');
      expect(mockStoryService.saveStory).toHaveBeenCalledWith(component.story);
    });

    it('should validate phase completion when basic outline changes', () => {
      fixture.detectChanges();
      component.basicOutline = 'Updated plot point';
      component.onBasicOutlineChange();
      
      expect(mockPhaseStateService.updatePhaseValidation).toHaveBeenCalled();
    });
  });

  describe('AI Flesh Out Functionality', () => {
    it('should show error if no basic outline is provided', async () => {
      component.basicOutline = '';
      await component.aiFleshOutPlotPoint();
      
      expect(mockToastService.showError).toHaveBeenCalledWith('Please enter a plot point to flesh out');
      expect(mockGenerationService.fleshOut).not.toHaveBeenCalled();
    });

    it('should call generation service and add to chat on success', async () => {
      const mockResponse = { fleshedOutText: 'Fleshed out content' };
      const mockMessage: ChatMessage = {
        id: 'msg-1',
        type: 'assistant',
        content: 'Fleshed out content',
        timestamp: new Date()
      };
      
      mockGenerationService.fleshOut.and.returnValue(of(mockResponse));
      mockConversationService.sendMessage.and.returnValue(mockMessage);
      
      component.basicOutline = 'Test plot point';
      await component.aiFleshOutPlotPoint();
      
      expect(mockGenerationService.fleshOut).toHaveBeenCalledWith(
        component.story,
        'Test plot point',
        'plot outline development'
      );
      expect(mockConversationService.sendMessage).toHaveBeenCalledTimes(2);
      expect(component.showChat).toBe(true);
      expect(mockToastService.showSuccess).toHaveBeenCalledWith('Plot point fleshed out! Check the chat for details.');
    });

    it('should handle generation service error', async () => {
      mockGenerationService.fleshOut.and.returnValue(throwError('Generation failed'));
      
      component.basicOutline = 'Test plot point';
      await component.aiFleshOutPlotPoint();
      
      expect(mockToastService.showError).toHaveBeenCalledWith('Failed to flesh out plot point. Please try again.');
      expect(component.isGeneratingFleshOut).toBe(false);
    });
  });

  describe('Research Archive Functionality', () => {
    it('should show error if no basic outline is provided', async () => {
      component.basicOutline = '';
      await component.researchPlotPoint();
      
      expect(mockToastService.showError).toHaveBeenCalledWith('Please enter a plot point to research');
      expect(mockArchiveService.ragQuery).not.toHaveBeenCalled();
    });

    it('should call archive service and show results on success', async () => {
      const mockResponse = {
        query: 'Test plot point',
        answer: 'Research results',
        sources: [
          {
            file_path: 'test.txt',
            file_name: 'test.txt',
            matching_section: 'Source content',
            similarity_score: 0.8
          }
        ],
        total_sources: 1
      };
      
      mockArchiveService.ragQuery.and.returnValue(of(mockResponse));
      mockConversationService.sendMessage.and.returnValue({} as ChatMessage);
      
      component.basicOutline = 'Test plot point';
      await component.researchPlotPoint();
      
      expect(mockArchiveService.ragQuery).toHaveBeenCalledWith('Test plot point');
      expect(component.researchData).toBe(mockResponse);
      expect(component.showResearchSidebar).toBe(true);
      expect(component.showChat).toBe(true);
      expect(mockToastService.showSuccess).toHaveBeenCalledWith('Archive research completed! Check the chat and sidebar for results.');
    });

    it('should handle archive service error', async () => {
      mockArchiveService.ragQuery.and.returnValue(throwError('Research failed'));
      
      component.basicOutline = 'Test plot point';
      await component.researchPlotPoint();
      
      expect(component.researchError).toBe('Failed to research archive. Please try again.');
      expect(mockToastService.showError).toHaveBeenCalledWith('Failed to research archive. Please try again.');
    });
  });

  describe('Draft Outline Builder', () => {
    it('should add item to draft outline', () => {
      const content = 'New outline item content';
      component.addToDraft(content);
      
      expect(component.draftOutlineItems.length).toBe(1);
      expect(component.draftOutlineItems[0].description).toBe(content);
      expect(component.draftOutlineItems[0].order).toBe(0);
      expect(mockToastService.showSuccess).toHaveBeenCalledWith('Added to draft outline!');
    });

    it('should extract title from content', () => {
      const content = 'This is a long content that should be truncated for the title. It has multiple sentences.';
      component.addToDraft(content);
      
      const addedItem = component.draftOutlineItems[0];
      expect(addedItem.title.length).toBeLessThanOrEqual(50);
      expect(addedItem.title).toContain('This is a long content');
    });

    it('should start editing an item', () => {
      component.addToDraft('Test content');
      const item = component.draftOutlineItems[0];
      
      component.startEditingItem(item);
      
      expect(component.editingItemId).toBe(item.id);
      expect(component.editingTitle).toBe(item.title);
      expect(component.editingDescription).toBe(item.description);
      expect(item.isEditing).toBe(true);
    });

    it('should save item edit', () => {
      component.addToDraft('Test content');
      const item = component.draftOutlineItems[0];
      
      component.startEditingItem(item);
      component.editingTitle = 'Updated title';
      component.editingDescription = 'Updated description';
      component.saveItemEdit();
      
      expect(item.title).toBe('Updated title');
      expect(item.description).toBe('Updated description');
      expect(item.isEditing).toBe(false);
      expect(component.editingItemId).toBe(null);
    });

    it('should cancel item edit', () => {
      component.addToDraft('Test content');
      const item = component.draftOutlineItems[0];
      const originalTitle = item.title;
      
      component.startEditingItem(item);
      component.editingTitle = 'Changed title';
      component.cancelItemEdit();
      
      expect(item.title).toBe(originalTitle);
      expect(item.isEditing).toBe(false);
      expect(component.editingItemId).toBe(null);
    });

    it('should remove item from draft outline', () => {
      component.addToDraft('Item 1');
      component.addToDraft('Item 2');
      component.addToDraft('Item 3');
      
      const itemToRemove = component.draftOutlineItems[1];
      component.removeItem(itemToRemove.id);
      
      expect(component.draftOutlineItems.length).toBe(2);
      expect(component.draftOutlineItems.find(item => item.id === itemToRemove.id)).toBeUndefined();
      
      // Check that order is updated
      expect(component.draftOutlineItems[0].order).toBe(0);
      expect(component.draftOutlineItems[1].order).toBe(1);
      
      expect(mockToastService.showSuccess).toHaveBeenCalledWith('Outline item removed');
    });
  });

  describe('Phase Completion Validation', () => {
    it('should not allow phase advancement with empty basic outline', () => {
      component.basicOutline = '';
      component.addToDraft('Item 1 with sufficient detail for validation');
      component.addToDraft('Item 2 with sufficient detail for validation');
      component.addToDraft('Item 3 with sufficient detail for validation');
      
      expect(component.canAdvancePhase()).toBe(false);
    });

    it('should not allow phase advancement with insufficient draft items', () => {
      component.basicOutline = 'Basic outline';
      component.addToDraft('Item 1 with sufficient detail for validation');
      component.addToDraft('Item 2 with sufficient detail for validation');
      
      expect(component.canAdvancePhase()).toBe(false);
    });

    it('should not allow phase advancement with insufficient item detail', () => {
      component.basicOutline = 'Basic outline';
      component.addToDraft('Short');
      component.addToDraft('Also short');
      component.addToDraft('Still short');
      
      expect(component.canAdvancePhase()).toBe(false);
    });

    it('should allow phase advancement when all criteria are met', () => {
      component.basicOutline = 'Basic outline';
      component.addToDraft('Item 1 with sufficient detail for validation to pass the minimum character requirement');
      component.addToDraft('Item 2 with sufficient detail for validation to pass the minimum character requirement');
      component.addToDraft('Item 3 with sufficient detail for validation to pass the minimum character requirement');
      
      expect(component.canAdvancePhase()).toBe(true);
    });

    it('should calculate completion percentage correctly', () => {
      component.addToDraft('Item 1 with sufficient detail for validation to pass the minimum character requirement');
      component.addToDraft('Short item');
      component.addToDraft('Item 3 with sufficient detail for validation to pass the minimum character requirement');
      
      // 2 out of 3 items are complete (67%)
      const percentage = component.getCompletionPercentage();
      expect(percentage).toBe(67);
    });

    it('should return 0% completion for empty outline', () => {
      expect(component.getCompletionPercentage()).toBe(0);
    });
  });

  describe('UI Helpers', () => {
    it('should toggle chat visibility', () => {
      expect(component.showChat).toBe(false);
      
      component.toggleChat();
      expect(component.showChat).toBe(true);
      
      component.toggleChat();
      expect(component.showChat).toBe(false);
    });

    it('should close research sidebar', () => {
      component.showResearchSidebar = true;
      component.researchData = { query: 'test', answer: 'test', sources: [], total_sources: 0 };
      component.researchError = 'test error';
      
      component.closeResearchSidebar();
      
      expect(component.showResearchSidebar).toBe(false);
      expect(component.researchData).toBeNull();
      expect(component.researchError).toBeNull();
    });

    it('should track items by id', () => {
      const item = { id: 'test-id', title: 'Test', description: 'Test', order: 0 };
      const result = component.trackByItemId(0, item);
      expect(result).toBe('test-id');
    });
  });

  describe('Data Persistence', () => {
    it('should save story when draft outline is updated', () => {
      component.addToDraft('Test item');
      expect(mockStoryService.saveStory).toHaveBeenCalledWith(component.story);
    });

    it('should initialize chapter compose state if not present', () => {
      component.story.chapterCompose = undefined;
      component.addToDraft('Test item');
      
      expect(component.story.chapterCompose).toBeDefined();
      expect(component.story.chapterCompose!.currentPhase).toBe('plot_outline');
      expect(component.story.chapterCompose!.phases.plotOutline).toBeDefined();
    });

    it('should update plot outline phase progress', () => {
      component.addToDraft('Item with sufficient detail for validation to pass the minimum character requirement');
      component.addToDraft('Short item');
      
      const plotOutlinePhase = component.story.chapterCompose?.phases.plotOutline;
      expect(plotOutlinePhase?.progress.totalItems).toBe(2);
      expect(plotOutlinePhase?.progress.completedItems).toBe(1);
    });
  });

  describe('Event Handlers', () => {
    it('should handle message sent event', () => {
      const message: ChatMessage = {
        id: 'msg-1',
        type: 'user',
        content: 'Test message',
        timestamp: new Date()
      };
      
      spyOn(console, 'log');
      component.onMessageSent(message);
      expect(console.log).toHaveBeenCalledWith('Message sent:', message);
    });

    it('should handle message action event', () => {
      const message: ChatMessage = {
        id: 'msg-1',
        type: 'user',
        content: 'Test message',
        timestamp: new Date()
      };
      
      const event = {
        action: 'edit' as const,
        message,
        data: { newContent: 'Updated content' }
      };
      
      spyOn(console, 'log');
      component.onMessageAction(event);
      expect(console.log).toHaveBeenCalledWith('Edit message:', message, event.data);
    });

    it('should handle branch changed event', () => {
      spyOn(console, 'log');
      component.onBranchChanged('new-branch-id');
      expect(console.log).toHaveBeenCalledWith('Branch changed:', 'new-branch-id');
    });

    it('should handle conversation cleared event', () => {
      spyOn(console, 'log');
      component.onConversationCleared();
      expect(console.log).toHaveBeenCalledWith('Conversation cleared');
    });
  });
});
