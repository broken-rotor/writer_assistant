import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { CommonModule } from '@angular/common';
import { of } from 'rxjs';

import { WorldbuildingChatComponent } from './worldbuilding-chat.component';
import { ChatInterfaceComponent } from '../chat-interface/chat-interface.component';
import { ConversationService } from '../../services/conversation.service';
import { WorldbuildingSyncService } from '../../services/worldbuilding-sync.service';
import { Story } from '../../models/story.model';

describe('WorldbuildingChatComponent - Accessibility', () => {
  let component: WorldbuildingChatComponent;
  let fixture: ComponentFixture<WorldbuildingChatComponent>;

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
      worldbuilding: 'Test worldbuilding content'
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
    chapterCompose: {
      currentPhase: 'plot_outline',
      phases: {
        plotOutline: {
          conversation: {
            id: 'conv-1',
            messages: [],
            currentBranchId: 'main',
            branches: new Map(),
            metadata: {
              created: new Date(),
              lastModified: new Date(),
              phase: 'plot_outline'
            }
          },
          status: 'active',
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
        chapterDetailer: {
          conversation: {
            id: 'conv-2',
            messages: [],
            currentBranchId: 'main',
            branches: new Map(),
            metadata: {
              created: new Date(),
              lastModified: new Date(),
              phase: 'chapter_detail'
            }
          },
          chapterDraft: {
            content: '',
            title: '',
            plotPoint: '',
            wordCount: 0,
            status: 'drafting'
          },
          feedbackIntegration: {
            pendingFeedback: [],
            incorporatedFeedback: [],
            feedbackRequests: new Map()
          },
          status: 'active',
          progress: {
            feedbackIncorporated: 0,
            totalFeedbackItems: 0,
            lastActivity: new Date()
          }
        },
        finalEdit: {
          conversation: {
            id: 'conv-3',
            messages: [],
            currentBranchId: 'main',
            branches: new Map(),
            metadata: {
              created: new Date(),
              lastModified: new Date(),
              phase: 'final_edit'
            }
          },
          finalChapter: {
            content: '',
            title: '',
            wordCount: 0,
            version: 1
          },
          reviewSelection: {
            availableReviews: [],
            selectedReviews: [],
            appliedReviews: []
          },
          status: 'active',
          progress: {
            reviewsApplied: 0,
            totalReviews: 0,
            lastActivity: new Date()
          }
        }
      },
      sharedContext: {
        chapterNumber: 1
      },
      navigation: {
        phaseHistory: ['plot_outline'],
        canGoBack: false,
        canGoForward: false,
        branchNavigation: {
          currentBranchId: 'main',
          availableBranches: ['main'],
          branchHistory: [],
          canNavigateBack: false,
          canNavigateForward: false
        }
      },
      overallProgress: {
        currentStep: 1,
        totalSteps: 3,
        phaseCompletionStatus: {
          'plot_outline': false,
          'chapter_detail': false,
          'final_edit': false
        }
      },
      metadata: {
        created: new Date(),
        lastModified: new Date(),
        version: '1.0'
      }
    },
    chapterCreation: {
      plotPoint: '',
      incorporatedFeedback: [],
      feedbackRequests: new Map()
    },
    metadata: {
      created: new Date(),
      lastModified: new Date(),
      version: '1.0'
    }
  };

  beforeEach(async () => {
    const conversationServiceSpy = jasmine.createSpyObj('ConversationService', [
      'initializeConversation',
      'getCurrentThread',
      'sendMessage',
      'getCurrentBranchMessages',
      'getAvailableBranches'
    ], {
      currentThread$: of(null),
      branchNavigation$: of({ currentBranchId: 'main', availableBranches: ['main'], branchHistory: [], canNavigateBack: false, canNavigateForward: false }),
      isProcessing$: of(false)
    });
    const worldbuildingSyncServiceSpy = jasmine.createSpyObj('WorldbuildingSyncService', [
      'syncWorldbuildingFromConversation'
    ], {
      worldbuildingUpdated$: of('')
    });

    await TestBed.configureTestingModule({
      imports: [CommonModule, WorldbuildingChatComponent, ChatInterfaceComponent],
      providers: [
        { provide: ConversationService, useValue: conversationServiceSpy },
        { provide: WorldbuildingSyncService, useValue: worldbuildingSyncServiceSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(WorldbuildingChatComponent);
    component = fixture.componentInstance;
    component.story = mockStory;

    // Setup conversation service spy return values
    conversationServiceSpy.getCurrentBranchMessages.and.returnValue([]);
    conversationServiceSpy.getAvailableBranches.and.returnValue(['main']);
  });

  describe('ARIA Attributes and Roles', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should have proper application role on main container', () => {
      const container = fixture.debugElement.query(By.css('.worldbuilding-chat-container'));
      expect(container.nativeElement.getAttribute('role')).toBe('application');
      expect(container.nativeElement.getAttribute('aria-label')).toBe('Worldbuilding Chat Interface');
    });

    it('should have complementary role on summary panel', () => {
      const summaryPanel = fixture.debugElement.query(By.css('.worldbuilding-summary-panel'));
      expect(summaryPanel.nativeElement.getAttribute('role')).toBe('complementary');
      expect(summaryPanel.nativeElement.getAttribute('aria-label')).toContain('Current worldbuilding summary');
    });

    it('should have main role on chat panel', () => {
      const chatPanel = fixture.debugElement.query(By.css('.chat-panel'));
      expect(chatPanel.nativeElement.getAttribute('role')).toBe('main');
      expect(chatPanel.nativeElement.getAttribute('aria-label')).toBe('Worldbuilding chat assistant');
    });

    it('should have proper aria-live regions', () => {
      // Set worldbuilding content to trigger aria-live="polite"
      component.currentWorldbuilding = 'Test worldbuilding content';
      fixture.detectChanges();

      const worldbuildingContent = fixture.debugElement.query(By.css('.worldbuilding-content'));
      expect(worldbuildingContent.nativeElement.getAttribute('aria-live')).toBe('polite');

      const chatWrapper = fixture.debugElement.query(By.css('.chat-interface-wrapper'));
      expect(chatWrapper.nativeElement.getAttribute('aria-live')).toBe('polite');
    });

    it('should have proper heading structure', () => {
      const summaryHeading = fixture.debugElement.query(By.css('#summary-heading'));
      const chatHeading = fixture.debugElement.query(By.css('#chat-heading'));
      
      expect(summaryHeading.nativeElement.tagName).toBe('H3');
      expect(chatHeading.nativeElement.tagName).toBe('H3');
      expect(summaryHeading.nativeElement.textContent).toBe('Current Worldbuilding');
      expect(chatHeading.nativeElement.textContent).toBe('Worldbuilding Assistant');
    });

    it('should have proper toolbar role and labels', () => {
      const toolbar = fixture.debugElement.query(By.css('[role="toolbar"]'));
      expect(toolbar.nativeElement.getAttribute('aria-label')).toBe('Worldbuilding actions');
    });

    it('should have proper button labels and descriptions', () => {
      const syncButton = fixture.debugElement.query(By.css('.sync-button'));
      expect(syncButton.nativeElement.getAttribute('aria-label')).toBe('Sync worldbuilding content from conversation');
      expect(syncButton.nativeElement.getAttribute('aria-describedby')).toContain('sync-help-');
    });
  });

  describe('Screen Reader Support', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should have screen reader instructions', () => {
      const instructions = fixture.debugElement.query(By.css('.sr-only'));
      expect(instructions.nativeElement.textContent).toContain('Interactive worldbuilding interface');
      expect(instructions.nativeElement.textContent).toContain('Ctrl+Slash for keyboard shortcuts help');
    });

    it('should have skip links for navigation', () => {
      const skipLinks = fixture.debugElement.queryAll(By.css('.skip-link'));
      expect(skipLinks.length).toBe(2);
      expect(skipLinks[0].nativeElement.textContent.trim()).toBe('Skip to worldbuilding summary');
      expect(skipLinks[1].nativeElement.textContent.trim()).toBe('Skip to chat interface');
    });

    it('should have proper empty state announcements', () => {
      component.currentWorldbuilding = '';
      fixture.detectChanges();

      const emptyState = fixture.debugElement.query(By.css('.empty-state'));
      expect(emptyState.nativeElement.getAttribute('role')).toBe('status');
      expect(emptyState.nativeElement.getAttribute('aria-live')).toBe('polite');
    });

    it('should have proper error announcements', () => {
      component.error = 'Test error message';
      fixture.detectChanges();

      const errorMessage = fixture.debugElement.query(By.css('.error-message'));
      expect(errorMessage.nativeElement.getAttribute('role')).toBe('alert');
      expect(errorMessage.nativeElement.getAttribute('aria-live')).toBe('assertive');
    });

    it('should have proper loading state announcements', () => {
      component.isInitialized = false;
      fixture.detectChanges();

      const loadingState = fixture.debugElement.query(By.css('.loading-state'));
      expect(loadingState.nativeElement.getAttribute('role')).toBe('status');
      expect(loadingState.nativeElement.getAttribute('aria-live')).toBe('polite');
    });
  });

  describe('Keyboard Navigation', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should handle Ctrl+/ keyboard shortcut for help', () => {
      spyOn(component, 'toggleKeyboardHelp');
      
      const event = new KeyboardEvent('keydown', { key: '/', ctrlKey: true });
      document.dispatchEvent(event);
      
      expect(component.toggleKeyboardHelp).toHaveBeenCalled();
    });

    it('should handle Ctrl+S keyboard shortcut for sync', () => {
      spyOn(component, 'syncWorldbuilding');
      
      const event = new KeyboardEvent('keydown', { key: 's', ctrlKey: true });
      document.dispatchEvent(event);
      
      expect(component.syncWorldbuilding).toHaveBeenCalled();
    });

    it('should handle Escape key to close help dialog', () => {
      component.showKeyboardHelpDialog = true;
      spyOn(component, 'hideKeyboardHelp');
      
      const event = new KeyboardEvent('keydown', { key: 'Escape' });
      document.dispatchEvent(event);
      
      expect(component.hideKeyboardHelp).toHaveBeenCalled();
    });

    it('should handle Alt+1 and Alt+2 for mobile panel switching', () => {
      component.isMobileView = true;
      spyOn(component, 'switchToPanel');
      
      const event1 = new KeyboardEvent('keydown', { key: '1', altKey: true });
      const event2 = new KeyboardEvent('keydown', { key: '2', altKey: true });
      
      document.dispatchEvent(event1);
      document.dispatchEvent(event2);
      
      expect(component.switchToPanel).toHaveBeenCalledWith('summary');
      expect(component.switchToPanel).toHaveBeenCalledWith('chat');
    });

    it('should have proper tabindex values for focusable elements', () => {
      const summaryPanel = fixture.debugElement.query(By.css('.worldbuilding-summary-panel'));
      const chatPanel = fixture.debugElement.query(By.css('.chat-panel'));
      const worldbuildingContent = fixture.debugElement.query(By.css('.worldbuilding-content'));
      
      expect(summaryPanel.nativeElement.getAttribute('tabindex')).toBe('-1');
      expect(chatPanel.nativeElement.getAttribute('tabindex')).toBe('-1');
      expect(worldbuildingContent.nativeElement.getAttribute('tabindex')).toBe('0');
    });
  });

  describe('Focus Management', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should focus summary panel when skip link is activated', () => {
      const summaryPanel = fixture.debugElement.query(By.css('.worldbuilding-summary-panel'));
      spyOn(summaryPanel.nativeElement, 'focus');
      
      const event = new Event('click');
      component.focusSummaryPanel(event);
      
      expect(summaryPanel.nativeElement.focus).toHaveBeenCalled();
      expect(component.focusedPanel).toBe('summary');
    });

    it('should focus chat panel when skip link is activated', () => {
      const chatPanel = fixture.debugElement.query(By.css('.chat-panel'));
      spyOn(chatPanel.nativeElement, 'focus');
      
      const event = new Event('click');
      component.focusChatPanel(event);
      
      expect(chatPanel.nativeElement.focus).toHaveBeenCalled();
      expect(component.focusedPanel).toBe('chat');
    });

    it('should manage focus when switching panels in mobile view', (done) => {
      component.isMobileView = true;
      const chatPanel = fixture.debugElement.query(By.css('.chat-panel'));
      spyOn(chatPanel.nativeElement, 'focus');

      component.switchToPanel('chat');

      setTimeout(() => {
        expect(chatPanel.nativeElement.focus).toHaveBeenCalled();
        done();
      }, 150);
    });
  });

  describe('Mobile Accessibility', () => {
    beforeEach(() => {
      component.isMobileView = true;
      fixture.detectChanges();
    });

    it('should show mobile panel navigation', () => {
      const mobileNav = fixture.debugElement.query(By.css('.mobile-panel-nav'));
      expect(mobileNav).toBeTruthy();
      expect(mobileNav.nativeElement.getAttribute('role')).toBe('tablist');
    });

    it('should have proper tab roles and attributes for mobile navigation', () => {
      const panelTabs = fixture.debugElement.queryAll(By.css('.panel-tab'));
      
      panelTabs.forEach(tab => {
        expect(tab.nativeElement.getAttribute('role')).toBe('tab');
        expect(tab.nativeElement.hasAttribute('aria-selected')).toBe(true);
        expect(tab.nativeElement.hasAttribute('aria-controls')).toBe(true);
      });
    });

    it('should handle panel switching with proper ARIA states', () => {
      component.switchToPanel('summary');
      fixture.detectChanges();
      
      const summaryTab = fixture.debugElement.query(By.css('.panel-tab[aria-controls*="summary"]'));
      const chatTab = fixture.debugElement.query(By.css('.panel-tab[aria-controls*="chat"]'));
      
      expect(summaryTab.nativeElement.getAttribute('aria-selected')).toBe('true');
      expect(chatTab.nativeElement.getAttribute('aria-selected')).toBe('false');
    });
  });

  describe('Keyboard Shortcuts Help', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should show keyboard shortcuts help dialog with proper ARIA attributes', () => {
      component.showKeyboardHelpDialog = true;
      fixture.detectChanges();
      
      const helpDialog = fixture.debugElement.query(By.css('.keyboard-help-overlay'));
      expect(helpDialog.nativeElement.getAttribute('role')).toBe('dialog');
      expect(helpDialog.nativeElement.getAttribute('aria-modal')).toBe('true');
      expect(helpDialog.nativeElement.getAttribute('aria-labelledby')).toBe('keyboard-help-title');
    });

    it('should have proper list structure for shortcuts', () => {
      component.showKeyboardHelpDialog = true;
      fixture.detectChanges();
      
      const shortcutsList = fixture.debugElement.query(By.css('.shortcuts-list'));
      const shortcutItems = fixture.debugElement.queryAll(By.css('.shortcut-item'));
      
      expect(shortcutsList.nativeElement.getAttribute('role')).toBe('list');
      shortcutItems.forEach(item => {
        expect(item.nativeElement.getAttribute('role')).toBe('listitem');
      });
    });

    it('should have proper close button accessibility', () => {
      component.showKeyboardHelpDialog = true;
      fixture.detectChanges();
      
      const closeButton = fixture.debugElement.query(By.css('.close-button'));
      expect(closeButton.nativeElement.getAttribute('aria-label')).toBe('Close keyboard shortcuts help');
    });
  });

  describe('Screen Reader Announcements', () => {
    it('should announce panel switches', fakeAsync(() => {
      spyOn(component as any, 'announceToScreenReader');

      // Mock the ViewChild ElementRefs
      (component as any).summaryPanel = { nativeElement: { focus: jasmine.createSpy('focus') } };
      (component as any).chatPanel = { nativeElement: { focus: jasmine.createSpy('focus') } };

      component.switchToPanel('summary');
      tick(100);

      expect((component as any).announceToScreenReader).toHaveBeenCalledWith('Switched to summary panel');
    }));

    it('should announce sync actions', () => {
      spyOn(component as any, 'announceToScreenReader');
      
      component.syncWorldbuilding();
      
      expect((component as any).announceToScreenReader).toHaveBeenCalledWith('Worldbuilding content synchronized from conversation');
    });

    it('should announce help dialog state changes', () => {
      spyOn(component as any, 'announceToScreenReader');
      
      component.showKeyboardHelp();
      expect((component as any).announceToScreenReader).toHaveBeenCalledWith('Keyboard shortcuts help opened');
      
      component.hideKeyboardHelp();
      expect((component as any).announceToScreenReader).toHaveBeenCalledWith('Keyboard shortcuts help closed');
    });
  });

  describe('Responsive Accessibility', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should update mobile view state on window resize', () => {
      spyOn(component, 'updateMobileView' as any);
      
      window.dispatchEvent(new Event('resize'));
      
      expect((component as any).updateMobileView).toHaveBeenCalled();
    });

    it('should adjust ARIA attributes based on screen size', () => {
      component.isMobileView = false;
      fixture.detectChanges();
      
      const summaryPanel = fixture.debugElement.query(By.css('.worldbuilding-summary-panel'));
      expect(summaryPanel.nativeElement.getAttribute('aria-expanded')).toBe('true');
      
      component.isMobileView = true;
      component.focusedPanel = 'chat';
      fixture.detectChanges();
      
      expect(summaryPanel.nativeElement.getAttribute('aria-expanded')).toBe('false');
    });
  });

  describe('Error Handling Accessibility', () => {
    it('should properly announce initialization errors', () => {
      component.story = null as any;
      component.ngOnInit();
      fixture.detectChanges();
      
      const errorState = fixture.debugElement.query(By.css('.error-state'));
      expect(errorState.nativeElement.getAttribute('role')).toBe('alert');
      expect(errorState.nativeElement.getAttribute('aria-live')).toBe('assertive');
    });

    it('should have descriptive error messages for screen readers', () => {
      component.error = 'Test error';
      fixture.detectChanges();
      
      const errorHelp = fixture.debugElement.query(By.css('[id*="error-help-"]'));
      expect(errorHelp.nativeElement.textContent).toContain('An error occurred in the worldbuilding chat interface');
    });
  });
});
