import { TestBed } from '@angular/core/testing';
import { PhaseStateService } from './phase-state.service';
import { LocalStorageService } from './local-storage.service';
import { ChapterComposeState } from '../models/story.model';

describe('PhaseStateService', () => {
  let service: PhaseStateService;
  let localStorageServiceSpy: jasmine.SpyObj<LocalStorageService>;

  beforeEach(() => {
    const spy = jasmine.createSpyObj('LocalStorageService', ['saveStory', 'loadStory']);

    TestBed.configureTestingModule({
      providers: [
        PhaseStateService,
        { provide: LocalStorageService, useValue: spy }
      ]
    });
    
    service = TestBed.inject(PhaseStateService);
    localStorageServiceSpy = TestBed.inject(LocalStorageService) as jasmine.SpyObj<LocalStorageService>;
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('initializeChapterComposeState', () => {
    it('should create initial chapter compose state', () => {
      const storyId = 'test-story';
      const chapterNumber = 1;

      const state = service.initializeChapterComposeState(storyId, chapterNumber);

      expect(state).toBeDefined();
      expect(state.currentPhase).toBe('plot_outline');
      expect(state.sharedContext.chapterNumber).toBe(chapterNumber);
      expect(state.phases.plotOutline.status).toBe('active');
      expect(state.phases.chapterDetailer.status).toBe('paused');
      expect(state.phases.finalEdit.status).toBe('paused');
    });

    it('should set up proper navigation state', () => {
      const state = service.initializeChapterComposeState('test-story', 1);

      expect(state.navigation.phaseHistory).toEqual(['plot_outline']);
      expect(state.navigation.canGoBack).toBe(false);
      expect(state.navigation.canGoForward).toBe(false);
    });

    it('should initialize progress tracking', () => {
      const state = service.initializeChapterComposeState('test-story', 1);

      expect(state.overallProgress.currentStep).toBe(1);
      expect(state.overallProgress.totalSteps).toBe(3);
      expect(state.overallProgress.phaseCompletionStatus['plot_outline']).toBe(false);
      expect(state.overallProgress.phaseCompletionStatus['chapter_detail']).toBe(false);
      expect(state.overallProgress.phaseCompletionStatus['final_edit']).toBe(false);
    });
  });

  describe('loadChapterComposeState', () => {
    it('should load existing state and update observables', () => {
      const mockState = service.initializeChapterComposeState('test-story', 2);
      mockState.currentPhase = 'chapter_detail';

      service.loadChapterComposeState(mockState);

      expect(service.getCurrentPhase()).toBe('chapter_detail');
      expect(service.getCurrentState()).toEqual(mockState);
    });
  });

  describe('phase validation', () => {
    let mockState: ChapterComposeState;

    beforeEach(() => {
      mockState = service.initializeChapterComposeState('test-story', 1);
    });

    it('should not allow advance from plot_outline without requirements', () => {
      service.loadChapterComposeState(mockState);

      expect(service.canAdvance()).toBe(false);
    });

    it('should allow advance from plot_outline with requirements met', () => {
      // Set up requirements for advancing from plot_outline
      mockState.phases.plotOutline.outline.structure = ['item1'];
      mockState.phases.plotOutline.draftSummary = 'Test summary';
      
      service.loadChapterComposeState(mockState);

      expect(service.canAdvance()).toBe(true);
    });

    it('should not allow advance from chapter_detail without requirements', () => {
      mockState.currentPhase = 'chapter_detail';
      mockState.phases.chapterDetailer.status = 'active';
      
      service.loadChapterComposeState(mockState);

      expect(service.canAdvance()).toBe(false);
    });

    it('should allow advance from chapter_detail with requirements met', () => {
      mockState.currentPhase = 'chapter_detail';
      mockState.phases.chapterDetailer.status = 'active';
      mockState.phases.chapterDetailer.chapterDraft.content = 'Test content with more than 500 words. '.repeat(50);
      mockState.phases.chapterDetailer.chapterDraft.wordCount = 600;
      
      service.loadChapterComposeState(mockState);

      expect(service.canAdvance()).toBe(true);
    });

    it('should not allow advance from final_edit phase', () => {
      mockState.currentPhase = 'final_edit';
      mockState.phases.finalEdit.status = 'active';
      
      service.loadChapterComposeState(mockState);

      expect(service.canAdvance()).toBe(false);
    });

    it('should not allow revert from plot_outline', () => {
      service.loadChapterComposeState(mockState);

      expect(service.canRevert()).toBe(false);
    });

    it('should allow revert from later phases', () => {
      mockState.currentPhase = 'chapter_detail';
      mockState.navigation.phaseHistory = ['plot_outline', 'chapter_detail'];
      
      service.loadChapterComposeState(mockState);

      expect(service.canRevert()).toBe(true);
    });
  });

  describe('phase transitions', () => {
    let mockState: ChapterComposeState;

    beforeEach(() => {
      mockState = service.initializeChapterComposeState('test-story', 1);
      // Set up requirements for advancing
      mockState.phases.plotOutline.outline.structure = ['item1'];
      mockState.phases.plotOutline.draftSummary = 'Test summary';
    });

    it('should advance to next phase successfully', async () => {
      service.loadChapterComposeState(mockState);

      const result = await service.advanceToNext();

      expect(result).toBe(true);
      expect(service.getCurrentPhase()).toBe('chapter_detail');
    });

    it('should update phase status on advance', async () => {
      service.loadChapterComposeState(mockState);

      await service.advanceToNext();
      const currentState = service.getCurrentState();

      expect(currentState?.phases.plotOutline.status).toBe('completed');
      expect(currentState?.phases.chapterDetailer.status).toBe('active');
    });

    it('should update progress on advance', async () => {
      service.loadChapterComposeState(mockState);

      await service.advanceToNext();
      const currentState = service.getCurrentState();

      expect(currentState?.overallProgress.currentStep).toBe(2);
      expect(currentState?.overallProgress.phaseCompletionStatus['plot_outline']).toBe(true);
    });

    it('should not advance if validation fails', async () => {
      // Clear requirements
      mockState.phases.plotOutline.outline.structure = [];
      mockState.phases.plotOutline.draftSummary = '';
      service.loadChapterComposeState(mockState);

      const result = await service.advanceToNext();

      expect(result).toBe(false);
      expect(service.getCurrentPhase()).toBe('plot_outline');
    });

    it('should revert to previous phase successfully', async () => {
      // Set up state in chapter_detail phase
      mockState.currentPhase = 'chapter_detail';
      mockState.navigation.phaseHistory = ['plot_outline', 'chapter_detail'];
      mockState.phases.chapterDetailer.status = 'active';
      service.loadChapterComposeState(mockState);

      const result = await service.revertToPrevious();

      expect(result).toBe(true);
      expect(service.getCurrentPhase()).toBe('plot_outline');
    });
  });

  describe('phase progress tracking', () => {
    let mockState: ChapterComposeState;

    beforeEach(() => {
      mockState = service.initializeChapterComposeState('test-story', 1);
      service.loadChapterComposeState(mockState);
    });

    it('should update phase progress', () => {
      const progressUpdate = { completedItems: 2, totalItems: 5 };

      service.updatePhaseProgress('plot_outline', progressUpdate);
      const currentState = service.getCurrentState();

      expect(currentState?.phases.plotOutline.progress.completedItems).toBe(2);
      expect(currentState?.phases.plotOutline.progress.totalItems).toBe(5);
    });

    it('should update last modified timestamp on progress update', () => {
      const beforeUpdate = mockState.metadata.lastModified;
      
      // Wait a bit to ensure timestamp difference
      setTimeout(() => {
        service.updatePhaseProgress('plot_outline', { completedItems: 1 });
        const currentState = service.getCurrentState();
        
        expect(currentState?.metadata.lastModified.getTime()).toBeGreaterThan(beforeUpdate.getTime());
      }, 10);
    });
  });

  describe('utility methods', () => {
    it('should return correct phase display names', () => {
      expect(service.getPhaseDisplayName('plot_outline')).toBe('Draft');
      expect(service.getPhaseDisplayName('chapter_detail')).toBe('Refined');
      expect(service.getPhaseDisplayName('final_edit')).toBe('Approved');
    });

    it('should return correct phase descriptions', () => {
      expect(service.getPhaseDescription('plot_outline')).toContain('plot outline');
      expect(service.getPhaseDescription('chapter_detail')).toContain('chapter content');
      expect(service.getPhaseDescription('final_edit')).toContain('finalize');
    });
  });

  describe('observables', () => {
    it('should emit current phase changes', (done) => {
      const mockState = service.initializeChapterComposeState('test-story', 1);
      
      service.currentPhase$.subscribe(phase => {
        if (phase === 'plot_outline') {
          done();
        }
      });

      service.loadChapterComposeState(mockState);
    });

    it('should emit validation result changes', (done) => {
      const mockState = service.initializeChapterComposeState('test-story', 1);
      
      service.validationResult$.subscribe(result => {
        expect(result).toBeDefined();
        expect(result.canAdvance).toBeDefined();
        expect(result.canRevert).toBeDefined();
        done();
      });

      service.loadChapterComposeState(mockState);
    });

    it('should emit chapter compose state changes', (done) => {
      const mockState = service.initializeChapterComposeState('test-story', 1);
      
      service.chapterComposeState$.subscribe(state => {
        if (state) {
          expect(state.currentPhase).toBe('plot_outline');
          done();
        }
      });

      service.loadChapterComposeState(mockState);
    });
  });
});
