import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router, RouterModule } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatChipsModule } from '@angular/material/chips';
import { MatMenuModule } from '@angular/material/menu';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatDividerModule } from '@angular/material/divider';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { of } from 'rxjs';
import { StoryListComponent } from './story-list.component';
import { LocalStorageService } from '../../core/services/local-storage.service';
import { Story } from '../../shared/models';

describe('StoryListComponent', () => {
  let component: StoryListComponent;
  let fixture: ComponentFixture<StoryListComponent>;
  let mockLocalStorageService: jasmine.SpyObj<LocalStorageService>;
  let mockRouter: jasmine.SpyObj<Router>;
  let mockDialog: jasmine.SpyObj<MatDialog>;
  let mockSnackBar: jasmine.SpyObj<MatSnackBar>;

  const mockStories: Story[] = [
    {
      id: 'story-1',
      title: 'Test Story 1',
      genre: 'Mystery',
      length: 'short_story',
      theme: 'A detective investigates a mysterious case',
      style: 'Literary',
      focusAreas: ['character', 'plot'],
      createdAt: new Date('2024-01-01'),
      lastModified: new Date('2024-01-02'),
      currentPhase: 'draft',
      progress: 25,
      storageSize: 1024
    },
    {
      id: 'story-2',
      title: 'Test Story 2',
      genre: 'Romance',
      length: 'novella',
      theme: 'A love story that transcends time',
      style: 'Contemporary',
      focusAreas: ['character'],
      createdAt: new Date('2024-01-03'),
      lastModified: new Date('2024-01-04'),
      currentPhase: 'completed',
      progress: 100,
      storageSize: 2048
    }
  ];

  const mockStorageInfo = {
    storiesCount: 2,
    usedSpace: 3072,
    availableSpace: 5000000,
    percentUsed: 0.06,
    lastBackup: new Date('2024-01-01')
  };

  beforeEach(async () => {
    // Create spies
    mockLocalStorageService = jasmine.createSpyObj('LocalStorageService', [
      'getAllStories',
      'getStory',
      'saveStory',
      'deleteStory',
      'duplicateStory',
      'exportStory',
      'importStory',
      'backupAllData',
      'getStorageInfo$'
    ]);
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);
    mockDialog = jasmine.createSpyObj('MatDialog', ['open']);
    mockSnackBar = jasmine.createSpyObj('MatSnackBar', ['open']);

    // Set up return values
    mockLocalStorageService.getAllStories.and.returnValue(mockStories);
    mockLocalStorageService.getStorageInfo$.and.returnValue(of(mockStorageInfo));

    await TestBed.configureTestingModule({
      declarations: [StoryListComponent],
      imports: [
        BrowserAnimationsModule,
        RouterModule.forRoot([]),
        MatTableModule,
        MatButtonModule,
        MatIconModule,
        MatCardModule,
        MatCheckboxModule,
        MatChipsModule,
        MatMenuModule,
        MatProgressBarModule,
        MatDividerModule
      ],
      providers: [
        { provide: LocalStorageService, useValue: mockLocalStorageService },
        { provide: Router, useValue: mockRouter },
        { provide: MatDialog, useValue: mockDialog },
        { provide: MatSnackBar, useValue: mockSnackBar }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(StoryListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('Initialization', () => {
    it('should load stories on init', () => {
      expect(component.stories.length).toBe(2);
      expect(component.stories[0].title).toBe('Test Story 2'); // Most recent first
    });

    it('should load storage info observable', (done) => {
      component.storageInfo$.subscribe(info => {
        expect(info.storiesCount).toBe(2);
        expect(info.usedSpace).toBe(3072);
        done();
      });
    });

    it('should initialize displayed columns', () => {
      expect(component.displayedColumns.length).toBe(5);
      expect(component.displayedColumns).toContain('title');
      expect(component.displayedColumns).toContain('actions');
    });
  });

  describe('Navigation', () => {
    it('should navigate to create new story', () => {
      component.onCreateNew();

      expect(mockRouter.navigate).toHaveBeenCalledWith(['/story-input']);
    });

    it('should navigate to draft phase', () => {
      const story: Story = { ...mockStories[0], currentPhase: 'draft' as const };

      component.onContinueStory(story);

      expect(mockRouter.navigate).toHaveBeenCalledWith(['/draft-review', 'story-1']);
    });

    it('should navigate to character dialog phase', () => {
      const story: Story = { ...mockStories[0], currentPhase: 'character_dialog' as const };

      component.onContinueStory(story);

      expect(mockRouter.navigate).toHaveBeenCalledWith(['/character-dialog', 'story-1']);
    });

    it('should navigate to detailed content phase', () => {
      const story: Story = { ...mockStories[0], currentPhase: 'detailed_content' as const };

      component.onContinueStory(story);

      expect(mockRouter.navigate).toHaveBeenCalledWith(['/content-generation', 'story-1']);
    });

    it('should navigate to refinement phase', () => {
      const story: Story = { ...mockStories[0], currentPhase: 'refinement' as const };

      component.onContinueStory(story);

      expect(mockRouter.navigate).toHaveBeenCalledWith(['/refinement', 'story-1']);
    });

    it('should navigate to completed story view', () => {
      const story: Story = { ...mockStories[0], currentPhase: 'completed' as const };

      component.onContinueStory(story);

      expect(mockRouter.navigate).toHaveBeenCalledWith(['/story-view', 'story-1']);
    });
  });

  describe('Story Management', () => {
    it('should duplicate story', () => {
      const duplicatedStory = { ...mockStories[0], id: 'story-1-copy', title: 'Test Story 1 (Copy)' };
      mockLocalStorageService.duplicateStory.and.returnValue(duplicatedStory);

      component.onDuplicateStory(mockStories[0]);

      expect(mockLocalStorageService.duplicateStory).toHaveBeenCalledWith('story-1');
      expect(mockSnackBar.open).toHaveBeenCalledWith(
        'Story "Test Story 1 (Copy)" duplicated successfully!',
        'Close',
        { duration: 3000 }
      );
    });

    it('should handle failed duplication', () => {
      mockLocalStorageService.duplicateStory.and.returnValue(null);

      component.onDuplicateStory(mockStories[0]);

      expect(mockSnackBar.open).toHaveBeenCalledWith(
        'Failed to duplicate story',
        'Close',
        { duration: 3000 }
      );
    });

    it('should delete story with confirmation', () => {
      spyOn(window, 'confirm').and.returnValue(true);

      component.onDeleteStory(mockStories[0]);

      expect(mockLocalStorageService.deleteStory).toHaveBeenCalledWith('story-1');
      expect(mockSnackBar.open).toHaveBeenCalledWith(
        'Story "Test Story 1" deleted successfully',
        'Close',
        { duration: 3000 }
      );
    });

    it('should not delete story without confirmation', () => {
      spyOn(window, 'confirm').and.returnValue(false);

      component.onDeleteStory(mockStories[0]);

      expect(mockLocalStorageService.deleteStory).not.toHaveBeenCalled();
    });
  });

  describe('Export and Import', () => {
    it('should export story', () => {
      const exportData = JSON.stringify({ story: mockStories[0] });
      mockLocalStorageService.exportStory.and.returnValue(exportData);
      spyOn(component as any, 'downloadFile');

      component.onExportStory(mockStories[0]);

      expect(mockLocalStorageService.exportStory).toHaveBeenCalledWith('story-1');
      expect(mockSnackBar.open).toHaveBeenCalledWith(
        'Story exported successfully!',
        'Close',
        { duration: 3000 }
      );
    });

    it('should import story', () => {
      const importedStory = mockStories[0];
      mockLocalStorageService.importStory.and.returnValue(importedStory);

      const fileContent = JSON.stringify({ story: importedStory });
      const blob = new Blob([fileContent], { type: 'application/json' });
      const file = new File([blob], 'test.json');

      const event = {
        target: {
          files: [file],
          value: ''
        }
      } as any;

      component.onImportStory(event);

      // Wait for file reading
      setTimeout(() => {
        expect(mockSnackBar.open).toHaveBeenCalled();
      }, 100);
    });

    it('should backup all data', () => {
      const backupData = JSON.stringify({ stories: mockStories });
      mockLocalStorageService.backupAllData.and.returnValue(backupData);
      spyOn(component as any, 'downloadFile');

      component.onBackupAll();

      expect(mockLocalStorageService.backupAllData).toHaveBeenCalled();
      expect(mockSnackBar.open).toHaveBeenCalledWith(
        'Complete backup created successfully!',
        'Close',
        { duration: 3000 }
      );
    });
  });

  describe('Story Selection', () => {
    it('should toggle story selection', () => {
      component.onToggleStorySelection('story-1');
      expect(component.selectedStories.has('story-1')).toBeTruthy();

      component.onToggleStorySelection('story-1');
      expect(component.selectedStories.has('story-1')).toBeFalsy();
    });

    it('should toggle all selection', () => {
      component.onToggleAllSelection();
      expect(component.selectedStories.size).toBe(2);

      component.onToggleAllSelection();
      expect(component.selectedStories.size).toBe(0);
    });

    it('should check hasSelectedStories getter', () => {
      expect(component.hasSelectedStories).toBeFalsy();

      component.selectedStories.add('story-1');
      expect(component.hasSelectedStories).toBeTruthy();
    });

    it('should check isAllSelected getter', () => {
      expect(component.isAllSelected).toBeFalsy();

      component.stories.forEach(story => component.selectedStories.add(story.id));
      expect(component.isAllSelected).toBeTruthy();
    });

    it('should check isIndeterminate getter', () => {
      expect(component.isIndeterminate).toBeFalsy();

      component.selectedStories.add('story-1');
      expect(component.isIndeterminate).toBeTruthy();
    });
  });

  describe('Bulk Operations', () => {
    beforeEach(() => {
      component.selectedStories.add('story-1');
      component.selectedStories.add('story-2');
    });

    it('should bulk export stories', () => {
      mockLocalStorageService.exportStory.and.returnValue(JSON.stringify({ story: mockStories[0] }));
      spyOn(component as any, 'downloadFile');

      component.onBulkExport();

      expect(mockSnackBar.open).toHaveBeenCalledWith(
        '2 stories exported successfully!',
        'Close',
        { duration: 3000 }
      );
    });

    it('should bulk delete stories with confirmation', () => {
      spyOn(window, 'confirm').and.returnValue(true);

      component.onBulkDelete();

      expect(mockLocalStorageService.deleteStory).toHaveBeenCalledTimes(2);
      expect(component.selectedStories.size).toBe(0);
    });

    it('should not bulk delete without confirmation', () => {
      spyOn(window, 'confirm').and.returnValue(false);

      component.onBulkDelete();

      expect(mockLocalStorageService.deleteStory).not.toHaveBeenCalled();
    });

    it('should not bulk export if no stories selected', () => {
      component.selectedStories.clear();
      spyOn(component as any, 'downloadFile');

      component.onBulkExport();

      expect(mockLocalStorageService.exportStory).not.toHaveBeenCalled();
    });
  });

  describe('Helper Methods', () => {
    it('should get phase progress', () => {
      expect(component.getPhaseProgress('draft')).toBe(25);
      expect(component.getPhaseProgress('character_dialog')).toBe(50);
      expect(component.getPhaseProgress('detailed_content')).toBe(75);
      expect(component.getPhaseProgress('refinement')).toBe(90);
      expect(component.getPhaseProgress('completed')).toBe(100);
    });

    it('should get phase color', () => {
      expect(component.getPhaseColor('draft')).toBe('accent');
      expect(component.getPhaseColor('character_dialog')).toBe('primary');
      expect(component.getPhaseColor('completed')).toBe('primary');
    });

    it('should provide phase labels', () => {
      expect(component.phaseLabels['draft']).toBe('Draft Development');
      expect(component.phaseLabels['completed']).toBe('Completed');
    });
  });
});
