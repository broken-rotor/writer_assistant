import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { StoryListComponent } from './features/story-list/story-list.component';
import { StoryInputComponent } from './features/story-input/story-input.component';
import { DraftReviewComponent } from './features/draft-review/draft-review.component';
import { CharacterDialogComponent } from './features/character-dialog/character-dialog.component';
import { ContentGenerationComponent } from './features/content-generation/content-generation.component';
import { RefinementComponent } from './features/refinement/refinement.component';
import { CharacterManagementComponent } from './features/character-management/character-management.component';

const routes: Routes = [
  { path: '', redirectTo: '/stories', pathMatch: 'full' },
  { path: 'stories', component: StoryListComponent },
  { path: 'story-input', component: StoryInputComponent },
  { path: 'draft-review/:id', component: DraftReviewComponent },
  { path: 'character-dialog/:id', component: CharacterDialogComponent },
  { path: 'character-management/:id', component: CharacterManagementComponent },
  { path: 'content-generation/:id', component: ContentGenerationComponent },
  { path: 'refinement/:id', component: RefinementComponent },
  { path: '**', redirectTo: '/stories' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }