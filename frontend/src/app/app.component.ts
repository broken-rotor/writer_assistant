import { Component, OnInit } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs/operators';
import { LocalStorageService } from './core/services/local-storage.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
  title = 'Writer Assistant';
  currentRoute = '';

  constructor(
    private router: Router,
    private localStorageService: LocalStorageService
  ) {}

  ngOnInit(): void {
    // Track current route for navigation highlighting
    this.router.events
      .pipe(filter((event): event is NavigationEnd => event instanceof NavigationEnd))
      .subscribe((event) => {
        this.currentRoute = event.url;
      });
  }

  onNavigateToStories(): void {
    this.router.navigate(['/stories']);
  }

  onCreateNewStory(): void {
    this.router.navigate(['/story-input']);
  }

  isCurrentRoute(route: string): boolean {
    return this.currentRoute.startsWith(route);
  }
}