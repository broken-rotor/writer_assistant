import { Routes } from '@angular/router';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { StoryWorkspaceComponent } from './components/story-workspace/story-workspace.component';
import { ArchiveComponent } from './components/archive/archive.component';

export const routes: Routes = [
  { path: '', component: DashboardComponent },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'archive', component: ArchiveComponent },
  { path: 'story/:id', component: StoryWorkspaceComponent },
  { path: '**', redirectTo: '/dashboard' }
];
