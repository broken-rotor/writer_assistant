import { TestBed } from '@angular/core/testing';
import { LoadingService } from './loading.service';

describe('LoadingService', () => {
  let service: LoadingService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(LoadingService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should initially not be loading', (done) => {
    service.loading$.subscribe(state => {
      expect(state.isLoading).toBe(false);
      done();
    });
  });

  it('should show loading with message', (done) => {
    service.show('Test message', 'test-operation');

    service.loading$.subscribe(state => {
      expect(state.isLoading).toBe(true);
      expect(state.message).toBe('Test message');
      expect(state.operation).toBe('test-operation');
      done();
    });
  });

  it('should hide loading', (done) => {
    service.show('Test message');
    service.hide();

    service.loading$.subscribe(state => {
      expect(state.isLoading).toBe(false);
      done();
    });
  });

  it('should return current loading state', () => {
    expect(service.isLoading).toBe(false);
    service.show('Test');
    expect(service.isLoading).toBe(true);
    service.hide();
    expect(service.isLoading).toBe(false);
  });
});
