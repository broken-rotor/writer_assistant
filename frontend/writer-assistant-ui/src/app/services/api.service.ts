import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Story, StoryCreate, StoryUpdate } from '../models/story.model';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly baseUrl = 'http://localhost:8000/api/v1';

  constructor(private http: HttpClient) {}

  // Story endpoints
  createStory(storyData: StoryCreate): Observable<Story> {
    return this.http.post<Story>(`${this.baseUrl}/stories/`, storyData);
  }

  getStories(): Observable<Story[]> {
    return this.http.get<Story[]>(`${this.baseUrl}/stories/`);
  }

  getStory(storyId: string): Observable<Story> {
    return this.http.get<Story>(`${this.baseUrl}/stories/${storyId}`);
  }

  updateStory(storyId: string, storyUpdate: StoryUpdate): Observable<Story> {
    return this.http.put<Story>(`${this.baseUrl}/stories/${storyId}`, storyUpdate);
  }

  deleteStory(storyId: string): Observable<{message: string}> {
    return this.http.delete<{message: string}>(`${this.baseUrl}/stories/${storyId}`);
  }
}