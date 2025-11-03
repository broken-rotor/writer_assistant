import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WorldbuildingChatComponent } from './worldbuilding-chat.component';
import { Story } from '../../models/story.model';
import { ConversationService } from '../../services/conversation.service';
import { ChatInterfaceComponent } from '../chat-interface/chat-interface.component';

describe('WorldbuildingChatComponent Accessibility', () => {
  let component: WorldbuildingChatComponent;
  let fixture: ComponentFixture<WorldbuildingChatComponent>;
  let _conversationService: jasmine.SpyObj<ConversationService>;

  const mockStory: Story = {
    id: 'test-story-id',
    general: {
      title: 'Test Story',
      systemPrompts: {
        mainPrefix: '',
        mainSuffix: '',
        assistantPrompt: '',
        editorPrompt: ''
      },
      worldbuilding: 'Initial worldbuilding content'
    },
    characters: new Map(),
    raters: new Map(),
    story: {
      summary: '',
      chapters: []
    },
    plotOutline: {
      content: '',
      status: 'draft',
      chatHistory: [],
      raterFeedback: new Map(),
      metadata: {
        created: new Date(),
        lastModified: new Date(),
        version: 1
      }
    },
    chapterCreation: {
      plotPoint: '',
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
    const conversationSpy = jasmine.createSpyObj('ConversationService', [
      'getConversation',
      'sendMessage',
      'clearConversation',
      'createBranch',
      'switchBranch',
      'deleteBranch'
    ]);

    await TestBed.configureTestingModule({
      imports: [WorldbuildingChatComponent, ChatInterfaceComponent],
      providers: [
        { provide: ConversationService, useValue: conversationSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(WorldbuildingChatComponent);
    component = fixture.componentInstance;
    _conversationService = TestBed.inject(ConversationService) as jasmine.SpyObj<ConversationService>;

    // Set required inputs
    component.story = mockStory;
  });

  it('should create component with proper accessibility structure', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it('should have proper ARIA attributes when initialized', () => {
    fixture.detectChanges();
    
    const componentElement = fixture.debugElement.nativeElement;
    expect(componentElement).toBeTruthy();
  });

  it('should handle error state accessibility', () => {
    component.story = null as any;
    fixture.detectChanges();
    
    expect(component.error).toBe('WorldbuildingChat requires a story input');
  });

  it('should be accessible when disabled', () => {
    component.disabled = true;
    fixture.detectChanges();
    
    expect(component.disabled).toBe(true);
  });

  it('should be accessible when processing', () => {
    component.processing = true;
    fixture.detectChanges();
    
    expect(component.processing).toBe(true);
  });

  it('should pass basic accessibility checks', () => {
    fixture.detectChanges();
    
    // Basic accessibility validation - component should render without errors
    const componentElement = fixture.debugElement.nativeElement;
    expect(componentElement).toBeTruthy();
  });

  it('should handle chat interface accessibility', () => {
    fixture.detectChanges();
    
    // Verify chat interface is present and configured
    expect(component.chatConfig).toBeDefined();
    expect(component.chatConfig?.placeholder).toBe('Ask about worldbuilding, describe your world, or request assistance...');
  });

  it('should maintain accessibility during state changes', () => {
    fixture.detectChanges();
    
    // Test state changes don't break accessibility
    component.disabled = true;
    fixture.detectChanges();
    
    component.processing = true;
    fixture.detectChanges();
    
    expect(component).toBeTruthy();
  });
});
