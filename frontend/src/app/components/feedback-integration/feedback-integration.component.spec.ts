import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';

import { FeedbackIntegrationComponent } from './feedback-integration.component';
import { CharacterFeedbackResponse, RaterFeedbackResponse } from '../../models/story.model';

describe('FeedbackIntegrationComponent', () => {
  let component: FeedbackIntegrationComponent;
  let fixture: ComponentFixture<FeedbackIntegrationComponent>;

  const mockCharacterFeedback: CharacterFeedbackResponse[] = [
    {
      characterName: 'Sarah',
      feedback: {
        actions: ['Add more physical action'],
        dialog: ['Include more dialogue'],
        physicalSensations: ['Describe the cold'],
        emotions: ['Show more fear'],
        internalMonologue: ['Add inner thoughts']
      }
    }
  ];

  const mockRaterFeedback: RaterFeedbackResponse[] = [
    {
      raterName: 'Editor',
      feedback: {
        opinion: 'Good pacing but needs more description',
        suggestions: [
          {
            issue: 'Pacing',
            suggestion: 'Slow down the action',
            priority: 'high'
          }
        ]
      }
    }
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        FeedbackIntegrationComponent,
        NoopAnimationsModule
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(FeedbackIntegrationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should emit getFeedback for character feedback', () => {
    spyOn(component.getFeedback, 'emit');
    
    component.onGetCharacterFeedback();
    
    expect(component.getFeedback.emit).toHaveBeenCalledWith({ type: 'character' });
  });

  it('should emit getFeedback for rater feedback', () => {
    spyOn(component.getFeedback, 'emit');
    
    component.onGetRaterFeedback();
    
    expect(component.getFeedback.emit).toHaveBeenCalledWith({ type: 'rater' });
  });

  it('should emit getFeedback for all feedback', () => {
    spyOn(component.getFeedback, 'emit');
    
    component.onGetAllFeedback();
    
    expect(component.getFeedback.emit).toHaveBeenCalledWith({ type: 'both' });
  });

  it('should emit applyFeedback for character feedback', () => {
    spyOn(component.applyFeedback, 'emit');
    
    component.onApplyCharacterFeedback(mockCharacterFeedback[0], 'actions', 'Add more physical action');
    
    expect(component.applyFeedback.emit).toHaveBeenCalledWith({
      type: 'apply',
      feedbackType: 'character',
      source: 'Sarah',
      content: 'Add more physical action'
    });
  });

  it('should emit applyFeedback for rater feedback', () => {
    spyOn(component.applyFeedback, 'emit');
    
    component.onApplyRaterFeedback(mockRaterFeedback[0], mockRaterFeedback[0].feedback.suggestions[0]);
    
    expect(component.applyFeedback.emit).toHaveBeenCalledWith({
      type: 'apply',
      feedbackType: 'rater',
      source: 'Editor',
      content: 'Slow down the action'
    });
  });

  it('should emit clearFeedback', () => {
    spyOn(component.clearFeedback, 'emit');
    
    component.onClearAllFeedback();
    
    expect(component.clearFeedback.emit).toHaveBeenCalled();
  });

  it('should check if has any feedback', () => {
    expect(component.hasAnyFeedback()).toBeFalse();
    
    component.characterFeedback = mockCharacterFeedback;
    expect(component.hasAnyFeedback()).toBeTrue();
    
    component.characterFeedback = [];
    component.raterFeedback = mockRaterFeedback;
    expect(component.hasAnyFeedback()).toBeTrue();
  });

  it('should get feedback type icon', () => {
    expect(component.getFeedbackTypeIcon('actions')).toBe('🎬');
    expect(component.getFeedbackTypeIcon('dialog')).toBe('💬');
    expect(component.getFeedbackTypeIcon('unknown')).toBe('📝');
  });

  it('should get priority color', () => {
    expect(component.getPriorityColor('high')).toBe('warn');
    expect(component.getPriorityColor('medium')).toBe('accent');
    expect(component.getPriorityColor('low')).toBe('primary');
    expect(component.getPriorityColor('unknown')).toBe('primary');
  });

  it('should toggle panel expansion', () => {
    const panelId = 'character-0';
    
    expect(component.isPanelExpanded(panelId)).toBeFalse();
    
    component.togglePanel(panelId);
    expect(component.isPanelExpanded(panelId)).toBeTrue();
    
    component.togglePanel(panelId);
    expect(component.isPanelExpanded(panelId)).toBeFalse();
  });

  it('should auto-expand first panel on init', () => {
    component.characterFeedback = mockCharacterFeedback;
    component.ngOnInit();
    
    expect(component.isPanelExpanded('character-0')).toBeTrue();
  });
});
