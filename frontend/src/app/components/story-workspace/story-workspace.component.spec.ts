import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { of } from 'rxjs';
import { StoryWorkspaceComponent } from './story-workspace.component';
import { StoryService } from '../../services/story.service';
import { Story } from '../../models/story.model';

describe('StoryWorkspaceComponent', () => {
  let component: StoryWorkspaceComponent;
  let fixture: ComponentFixture<StoryWorkspaceComponent>;
  let storyServiceSpy: jasmine.SpyObj<StoryService>;
  let activatedRoute: any;

  beforeEach(async () => {
    const storySpy = jasmine.createSpyObj('StoryService', [
      'getStory',
      'saveStory',
      'deleteStory',
      'addCharacter',
      'updateCharacter',
      'hideCharacter',
      'deleteCharacter',
      'addRater',
      'updateRater',
      'deleteRater',
      'toggleRater',
      'addChapter',
      'deleteChapter'
    ]);

    activatedRoute = {
      params: of({ id: 'test-story-id' })
    };

    await TestBed.configureTestingModule({
      imports: [StoryWorkspaceComponent, FormsModule],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: StoryService, useValue: storySpy },
        { provide: ActivatedRoute, useValue: activatedRoute }
      ]
    }).compileComponents();

    storyServiceSpy = TestBed.inject(StoryService) as jasmine.SpyObj<StoryService>;
    fixture = TestBed.createComponent(StoryWorkspaceComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('ngOnInit', () => {
    it('should load story from route params', () => {
      const mockStory = createMockStory('test-story-id', 'Test Story');
      storyServiceSpy.getStory.and.returnValue(mockStory);

      fixture.detectChanges();

      expect(storyServiceSpy.getStory).toHaveBeenCalledWith('test-story-id');
      expect(component.story).toBe(mockStory);
      expect(component.loading).toBe(false);
    });

    it('should set error if story not found', () => {
      storyServiceSpy.getStory.and.returnValue(null);

      fixture.detectChanges();

      expect(component.error).toBe('Story not found');
      expect(component.loading).toBe(false);
    });
  });

  describe('selectTab', () => {
    it('should change active tab', () => {
      const mockStory = createMockStory('test-id', 'Test Story');
      storyServiceSpy.getStory.and.returnValue(mockStory);
      storyServiceSpy.saveStory.and.returnValue(true);

      fixture.detectChanges();

      component.selectTab('characters');

      expect(component.activeTab).toBe('characters');
      expect(storyServiceSpy.saveStory).toHaveBeenCalledWith(mockStory);
    });
  });

  describe('Character Management', () => {
    beforeEach(() => {
      const mockStory = createMockStory('test-id', 'Test Story');
      storyServiceSpy.getStory.and.returnValue(mockStory);
      fixture.detectChanges();
    });

    it('should add a new character', () => {
      const initialSize = component.story!.characters.size;
      component.addCharacter();

      expect(component.story!.characters.size).toBe(initialSize + 1);
      expect(component.selectedCharacterId).toBeTruthy();
    });

    it('should select a character for editing', () => {
      component.addCharacter();
      const characterId = component.selectedCharacterId!;

      component.selectCharacter(characterId);

      expect(component.editingCharacter).toBeTruthy();
      expect(component.editingCharacter.id).toBe(characterId);
    });

    it('should save character changes', () => {
      storyServiceSpy.saveStory.and.returnValue(true);
      component.addCharacter();
      component.editingCharacter!.name = 'Updated Name';

      component.saveCharacter();

      expect(storyServiceSpy.saveStory).toHaveBeenCalled();
    });

    it('should hide a character', () => {
      storyServiceSpy.saveStory.and.returnValue(true);
      component.addCharacter();
      const characterId = component.selectedCharacterId!;

      component.hideCharacter(characterId);

      const character = component.story!.characters.get(characterId);
      expect(character?.isHidden).toBe(true);
    });

    it('should remove a character', () => {
      spyOn(window, 'confirm').and.returnValue(true);
      storyServiceSpy.saveStory.and.returnValue(true);
      component.addCharacter();
      const characterId = component.selectedCharacterId!;
      const initialSize = component.story!.characters.size;

      component.removeCharacter(characterId);

      expect(component.story!.characters.size).toBe(initialSize - 1);
      expect(component.selectedCharacterId).toBeNull();
    });
  });

  describe('Rater Management', () => {
    beforeEach(() => {
      const mockStory = createMockStory('test-id', 'Test Story');
      storyServiceSpy.getStory.and.returnValue(mockStory);
      fixture.detectChanges();
    });

    it('should add a new rater', () => {
      const initialSize = component.story!.raters.size;
      component.addRater();

      expect(component.story!.raters.size).toBe(initialSize + 1);
      expect(component.selectedRaterId).toBeTruthy();
    });

    it('should toggle rater enabled state', () => {
      storyServiceSpy.saveStory.and.returnValue(true);
      component.addRater();
      const raterId = component.selectedRaterId!;
      const initialEnabled = component.story!.raters.get(raterId)!.enabled;

      component.toggleRater(raterId);

      expect(component.story!.raters.get(raterId)!.enabled).toBe(!initialEnabled);
    });

    it('should remove a rater', () => {
      spyOn(window, 'confirm').and.returnValue(true);
      storyServiceSpy.saveStory.and.returnValue(true);
      component.addRater();
      const raterId = component.selectedRaterId!;
      const initialSize = component.story!.raters.size;

      component.removeRater(raterId);

      expect(component.story!.raters.size).toBe(initialSize - 1);
      expect(component.selectedRaterId).toBeNull();
    });
  });

  describe('Chapter Creation', () => {
    beforeEach(() => {
      const mockStory = createMockStory('test-id', 'Test Story');
      storyServiceSpy.getStory.and.returnValue(mockStory);
      fixture.detectChanges();
    });

    it('should accept chapter and add to story', () => {
      storyServiceSpy.saveStory.and.returnValue(true);
      component.story!.chapterCreation.generatedChapter = {
        text: 'Generated chapter text',
        status: 'ready',
        metadata: {
          generatedAt: new Date(),
          model: 'test-model'
        }
      };
      component.story!.chapterCreation.plotPoint = 'Test plot point';

      const initialChapterCount = component.story!.story.chapters.length;

      component.acceptChapter();

      expect(component.story!.story.chapters.length).toBe(initialChapterCount + 1);
      expect(component.story!.chapterCreation.plotPoint).toBe('');
      expect(component.activeTab).toBe('story');
      expect(storyServiceSpy.saveStory).toHaveBeenCalled();
    });

    it('should remove feedback item', () => {
      component.story!.chapterCreation.incorporatedFeedback = [
        {
          source: 'Character 1',
          type: 'action',
          content: 'Test feedback',
          incorporated: true
        }
      ];

      component.removeFeedbackItem(0);

      expect(component.story!.chapterCreation.incorporatedFeedback.length).toBe(0);
    });
  });

  describe('Helper Methods', () => {
    beforeEach(() => {
      const mockStory = createMockStory('test-id', 'Test Story');
      storyServiceSpy.getStory.and.returnValue(mockStory);
      fixture.detectChanges();
    });

    it('should return active characters', () => {
      component.story!.characters.set('char1', {
        id: 'char1',
        name: 'Visible',
        basicBio: '',
        sex: 'Male',
        gender: 'Male',
        sexualPreference: 'Heterosexual',
        age: 30,
        physicalAppearance: '',
        usualClothing: '',
        personality: '',
        motivations: '',
        fears: '',
        relationships: '',
        isHidden: false,
        metadata: { creationSource: 'user', lastModified: new Date() }
      });
      component.story!.characters.set('char2', {
        id: 'char2',
        name: 'Hidden',
        basicBio: '',
        sex: 'Female',
        gender: 'Female',
        sexualPreference: 'Heterosexual',
        age: 25,
        physicalAppearance: '',
        usualClothing: '',
        personality: '',
        motivations: '',
        fears: '',
        relationships: '',
        isHidden: true,
        metadata: { creationSource: 'user', lastModified: new Date() }
      });

      const activeChars = component.activeCharacters;

      expect(activeChars.length).toBe(1);
      expect(activeChars[0].name).toBe('Visible');
    });

    it('should return enabled raters', () => {
      component.story!.raters.set('rater1', {
        id: 'rater1',
        name: 'Enabled',
        systemPrompt: '',
        enabled: true,
        metadata: { created: new Date(), lastModified: new Date() }
      });
      component.story!.raters.set('rater2', {
        id: 'rater2',
        name: 'Disabled',
        systemPrompt: '',
        enabled: false,
        metadata: { created: new Date(), lastModified: new Date() }
      });

      const enabledRaters = component.enabledRaters;

      expect(enabledRaters.length).toBe(1);
      expect(enabledRaters[0].name).toBe('Enabled');
    });
  });
});

function createMockStory(id: string, title: string): Story {
  return {
    id: id,
    general: {
      title: title,
      systemPrompts: {
        mainPrefix: '',
        mainSuffix: '',
        assistantPrompt: 'You are a creative writing assistant.',
        editorPrompt: 'You are an experienced editor.'
      },
      worldbuilding: ''
    },
    characters: new Map(),
    raters: new Map(),
    story: {
      summary: '',
      chapters: []
    },
    chapterCreation: {
      plotPoint: '',
      incorporatedFeedback: [],
      feedbackRequests: new Map()
    },
    metadata: {
      version: '1.0',
      created: new Date(),
      lastModified: new Date()
    }
  };
}
