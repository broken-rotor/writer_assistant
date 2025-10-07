import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { HttpClientModule } from '@angular/common/http';
import { ReactiveFormsModule } from '@angular/forms';

// Material Design Modules
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';
import { MatMenuModule } from '@angular/material/menu';
import { MatDialogModule } from '@angular/material/dialog';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatDividerModule } from '@angular/material/divider';
import { MatTooltipModule } from '@angular/material/tooltip';

// App Components
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';

// Feature Components
import { StoryListComponent } from './features/story-list/story-list.component';
import { StoryInputComponent } from './features/story-input/story-input.component';
import { DraftReviewComponent } from './features/draft-review/draft-review.component';
import { CharacterDialogComponent } from './features/character-dialog/character-dialog.component';
import { ContentGenerationComponent } from './features/content-generation/content-generation.component';
import { RefinementComponent } from './features/refinement/refinement.component';
import { CharacterManagementComponent } from './features/character-management/character-management.component';
import { AiExpansionDialogComponent } from './features/ai-expansion-dialog/ai-expansion-dialog.component';
import { CharacterInputDialogComponent } from './features/story-input/character-input-dialog.component';

// Services
import { ApiService } from './core/services/api.service';
import { LocalStorageService } from './core/services/local-storage.service';
import { CharacterService } from './core/services/character.service';

@NgModule({
  declarations: [
    AppComponent,
    StoryListComponent,
    StoryInputComponent,
    DraftReviewComponent,
    CharacterDialogComponent,
    ContentGenerationComponent,
    RefinementComponent,
    CharacterManagementComponent,
    AiExpansionDialogComponent,
    CharacterInputDialogComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    HttpClientModule,
    ReactiveFormsModule,
    AppRoutingModule,

    // Material Design Modules
    MatToolbarModule,
    MatButtonModule,
    MatIconModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatCheckboxModule,
    MatChipsModule,
    MatProgressBarModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatTableModule,
    MatMenuModule,
    MatDialogModule,
    MatExpansionModule,
    MatDividerModule,
    MatTooltipModule
  ],
  providers: [
    ApiService,
    LocalStorageService,
    CharacterService
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }