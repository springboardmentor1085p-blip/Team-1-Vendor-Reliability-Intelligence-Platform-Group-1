import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-profile',
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.css']
})
export class ProfileComponent implements OnInit {
  currentUser: any = null;
  uploading = false;
  avatarError = '';

  @ViewChild('fileInput') fileInput!: ElementRef;

  constructor(public authService: AuthService, private router: Router) {}

  ngOnInit(): void {
    this.authService.currentUser$.subscribe(user => {
      this.currentUser = user;
    });
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  triggerFileInput(): void {
    if (this.fileInput && !this.uploading) {
      this.fileInput.nativeElement.click();
    }
  }

  onFileSelected(event: any): void {
    const file = event.target.files[0];
    if (!file) return;

    // Validate size (2MB limit)
    if (file.size > 2 * 1024 * 1024) {
      this.avatarError = 'File size exceeds the 2MB limit.';
      this.clearFileInput();
      return;
    }

    // Validate type
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      this.avatarError = 'Unsupported format. Only PNG, JPG, JPEG, and WebP are allowed.';
      this.clearFileInput();
      return;
    }

    this.uploading = true;
    this.avatarError = '';

    this.authService.uploadMyAvatar(file).subscribe({
      next: () => {
        this.uploading = false;
        this.clearFileInput();
      },
      error: (err) => {
        this.uploading = false;
        this.avatarError = err.error?.detail || 'Upload failed.';
        this.clearFileInput();
      }
    });
  }

  removeAvatar(): void {
    if (!confirm('Are you sure you want to remove your profile picture?')) return;

    this.uploading = true;
    this.avatarError = '';

    this.authService.deleteMyAvatar().subscribe({
      next: () => {
        this.uploading = false;
        this.clearFileInput();
      },
      error: (err) => {
        this.uploading = false;
        this.avatarError = err.error?.detail || 'Failed to remove avatar.';
        this.clearFileInput();
      }
    });
  }

  private clearFileInput(): void {
    if (this.fileInput) {
      this.fileInput.nativeElement.value = '';
    }
  }
}
