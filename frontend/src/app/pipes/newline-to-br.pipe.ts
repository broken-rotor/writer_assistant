import { Pipe, PipeTransform, inject } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

@Pipe({
  name: 'newlineToBr',
  standalone: true
})
export class NewlineToBrPipe implements PipeTransform {
  private sanitizer = inject(DomSanitizer);

  transform(value: string): SafeHtml {
    if (!value) return '';

    // Replace newlines with <br> tags and sanitize
    const html = value.replace(/\n/g, '<br>');
    return this.sanitizer.sanitize(1, html) || ''; // 1 = SecurityContext.HTML
  }
}
