import { Routes } from '@angular/router';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { StoryCreationComponent } from './components/story-creation/story-creation.component';
import { StoryWorkspaceComponent } from './components/story-workspace/story-workspace.component';

export const routes: Routes = [
  { path: '', component: DashboardComponent },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'create-story', component: StoryCreationComponent },
  { path: 'story/:id', component: StoryWorkspaceComponent },
  { path: '**', redirectTo: '/dashboard' }
];
