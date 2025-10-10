import { Routes } from '@angular/router';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { StoryWorkspaceComponent } from './components/story-workspace/story-workspace.component';

export const routes: Routes = [
  { path: '', component: DashboardComponent },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'story/:id', component: StoryWorkspaceComponent },
  { path: '**', redirectTo: '/dashboard' }
];
