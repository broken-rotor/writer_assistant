import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { PlotOutlineTabComponent } from './plot-outline-tab.component';
import { Story } from '../../models/story.model';

describe('PlotOutlineTabComponent', () => {
  let component: PlotOutlineTabComponent;
  let fixture: ComponentFixture<PlotOutlineTabComponent>;
  let mockStory: Story;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PlotOutlineTabComponent, FormsModule]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PlotOutlineTabComponent);
    component = fixture.componentInstance;

    // Create mock story with plot outline
    mockStory = {
      id: 'test-story',
      general: {
        title: 'Test Story',
        systemPrompts: {
          mainPrefix: '',
          mainSuffix: '',
          assistantPrompt: '',
          editorPrompt: ''
        },
        worldbuilding: ''
      },
      characters: [],
      raters: [],
      chapters: [],
      plotOutline: {
        content: 'Test plot outline content',
        status: 'draft',
        chatHistory: [],
        raterFeedback: new Map(),
        metadata: {
          created: new Date(),
          lastModified: new Date(),
          version: 1
        }
      },
      chapterCompose: {
        phases: {
          plotOutline: {
            status: 'not_started',
            outline: {
              items: new Map(),
              structure: []
            },
            draftSummary: '',
            progress: {
              totalItems: 0,
              completedItems: 0,
              lastActivity: new Date()
            }
          },
          chapterDetail: {
            status: 'not_started',
            chapters: new Map(),
            progress: {
              totalChapters: 0,
              completedChapters: 0,
              lastActivity: new Date()
            }
          },
          finalEdit: {
            status: 'not_started',
            finalStory: '',
            editorSuggestions: [],
            progress: {
              totalSuggestions: 0,
              appliedSuggestions: 0,
              lastActivity: new Date()
            }
          }
        },
        currentPhase: 'plot_outline',
        metadata: {
          created: new Date(),
          lastModified: new Date(),
          version: 1
        }
      },
      metadata: {
        created: new Date(),
        lastModified: new Date(),
        version: 1
      }
    } as Story;

    component.story = mockStory;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with default values', () => {
    expect(component.showChat).toBe(true);
    expect(component.chatInput).toBe('');
    expect(component.isGeneratingAI).toBe(false);
    expect(component.isResearching).toBe(false);
  });

  it('should display plot outline content', () => {
    const textarea = fixture.nativeElement.querySelector('.outline-editor');
    expect(textarea.value).toBe('Test plot outline content');
  });

  it('should emit outlineUpdated when content changes', () => {
    spyOn(component.outlineUpdated, 'emit');
    
    component.onOutlineChange();
    
    expect(component.outlineUpdated.emit).toHaveBeenCalledWith('Test plot outline content');
    expect(component.story.plotOutline.metadata.lastModified).toBeInstanceOf(Date);
  });

  it('should return correct status display', () => {
    expect(component.getStatusDisplay()).toBe('Draft');
    
    component.story.plotOutline.status = 'under_review';
    expect(component.getStatusDisplay()).toBe('Under Review');
    
    component.story.plotOutline.status = 'approved';
    expect(component.getStatusDisplay()).toBe('Approved');
    
    component.story.plotOutline.status = 'needs_revision';
    expect(component.getStatusDisplay()).toBe('Needs Revision');
  });

  it('should handle AI expand outline', () => {
    spyOn(console, 'log');
    
    component.aiExpandOutline();
    
    expect(console.log).toHaveBeenCalledWith('AI expand outline - to be implemented');
    expect(component.isGeneratingAI).toBe(true);
  });

  it('should handle research outline', () => {
    spyOn(console, 'log');
    
    component.researchOutline();
    
    expect(console.log).toHaveBeenCalledWith('Research outline - to be implemented');
    expect(component.isResearching).toBe(true);
  });

  it('should save outline', () => {
    spyOn(component.outlineUpdated, 'emit');
    spyOn(console, 'log');
    
    component.saveOutline();
    
    expect(console.log).toHaveBeenCalledWith('Save outline - to be implemented');
    expect(component.outlineUpdated.emit).toHaveBeenCalledWith('Test plot outline content');
  });

  it('should reset outline', () => {
    spyOn(component.outlineUpdated, 'emit');
    spyOn(console, 'log');
    
    component.resetOutline();
    
    expect(console.log).toHaveBeenCalledWith('Reset outline - to be implemented');
    expect(component.story.plotOutline.content).toBe('');
    expect(component.story.plotOutline.status).toBe('draft');
    expect(component.outlineUpdated.emit).toHaveBeenCalledWith('');
  });

  it('should send chat message', () => {
    spyOn(console, 'log');
    component.chatInput = 'Test message';
    
    component.sendChatMessage();
    
    expect(console.log).toHaveBeenCalledWith('Send chat message - to be implemented');
    expect(component.story.plotOutline.chatHistory.length).toBe(1);
    expect(component.story.plotOutline.chatHistory[0].content).toBe('Test message');
    expect(component.story.plotOutline.chatHistory[0].type).toBe('user');
    expect(component.chatInput).toBe('');
  });

  it('should not send empty chat message', () => {
    component.chatInput = '   ';
    const initialLength = component.story.plotOutline.chatHistory.length;
    
    component.sendChatMessage();
    
    expect(component.story.plotOutline.chatHistory.length).toBe(initialLength);
  });

  it('should clear chat', () => {
    spyOn(console, 'log');
    component.story.plotOutline.chatHistory = [
      {
        id: 'test-msg',
        type: 'user',
        content: 'Test message',
        timestamp: new Date()
      }
    ];
    
    component.clearChat();
    
    expect(console.log).toHaveBeenCalledWith('Clear chat - to be implemented');
    expect(component.story.plotOutline.chatHistory.length).toBe(0);
  });

  it('should handle disabled state', () => {
    component.disabled = true;
    fixture.detectChanges();
    
    const textarea = fixture.nativeElement.querySelector('.outline-editor');
    const buttons = fixture.nativeElement.querySelectorAll('button');
    const chatInput = fixture.nativeElement.querySelector('.chat-input');
    
    expect(textarea.disabled).toBe(true);
    expect(chatInput.disabled).toBe(true);
    
    buttons.forEach((button: HTMLButtonElement) => {
      expect(button.disabled).toBe(true);
    });
  });

  it('should display empty chat message when no chat history', () => {
    const emptyChat = fixture.nativeElement.querySelector('.empty-chat');
    expect(emptyChat.textContent.trim()).toBe('Start a conversation about your plot outline...');
  });

  it('should display chat messages', () => {
    component.story.plotOutline.chatHistory = [
      {
        id: 'msg-1',
        type: 'user',
        content: 'User message',
        timestamp: new Date()
      },
      {
        id: 'msg-2',
        type: 'assistant',
        content: 'AI response',
        timestamp: new Date()
      }
    ];
    fixture.detectChanges();
    
    const messages = fixture.nativeElement.querySelectorAll('.chat-message');
    expect(messages.length).toBe(2);
    expect(messages[0].classList.contains('user-message')).toBe(true);
    expect(messages[1].classList.contains('ai-message')).toBe(true);
  });
});
