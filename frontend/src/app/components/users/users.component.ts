import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { AdminService } from '../../services/admin.service';
import { VendorService } from '../../services/vendor.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-users',
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.css']
})
export class UsersComponent implements OnInit {
  users: any[] = [];
  vendors: any[] = [];
  loading = false;
  submitting = false;

  @ViewChild('fileInput') fileInput!: ElementRef;

  // Form states
  showCreateModal = false;
  userForm!: FormGroup;
  editingUserId: number | null = null;
  error = '';
  success = '';

  roles = [
    'Administrator',
    'Procurement Manager',
    'Supply Chain Manager',
    'Finance Officer',
    'Auditor',
    'Vendor'
  ];

  constructor(
    private adminService: AdminService,
    private vendorService: VendorService,
    public authService: AuthService,
    private fb: FormBuilder
  ) {}

  ngOnInit(): void {
    this.loadUsers();
    this.loadVendors();
    this.initForm();
  }

  initForm(): void {
    this.userForm = this.fb.group({
      username: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      full_name: ['', Validators.required],
      role: ['Procurement Manager', Validators.required],
      password: [''],
      vendor_id: [null],
      is_active: [true],
      avatar_url: [null]
    });

    // Toggle vendor selection validation conditionally
    this.userForm.get('role')?.valueChanges.subscribe(r => {
      const vendorCtrl = this.userForm.get('vendor_id');
      if (r === 'Vendor') {
        vendorCtrl?.setValidators([Validators.required]);
      } else {
        vendorCtrl?.clearValidators();
        vendorCtrl?.setValue(null);
      }
      vendorCtrl?.updateValueAndValidity();
    });
  }

  loadUsers(): void {
    this.loading = true;
    this.adminService.getUsers().subscribe({
      next: (data) => {
        this.users = data;
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading users', err);
        this.loading = false;
      }
    });
  }

  loadVendors(): void {
    this.vendorService.getVendors().subscribe(data => this.vendors = data);
  }

  openCreateModal(): void {
    this.editingUserId = null;
    this.initForm();
    // Password is required when creating a new user
    this.userForm.get('password')?.setValidators([Validators.required, Validators.minLength(6)]);
    this.userForm.get('password')?.updateValueAndValidity();
    
    if (this.fileInput) {
      this.fileInput.nativeElement.value = '';
    }

    this.error = '';
    this.success = '';
    this.showCreateModal = true;
  }

  openEditModal(user: any): void {
    this.editingUserId = user.id;
    this.initForm();
    
    // Password is not required when editing
    this.userForm.get('password')?.clearValidators();
    this.userForm.get('password')?.updateValueAndValidity();

    this.userForm.patchValue({
      username: user.username,
      email: user.email,
      full_name: user.full_name,
      role: user.role,
      vendor_id: user.vendor_id,
      is_active: user.is_active,
      avatar_url: user.avatar_url
    });

    if (this.fileInput) {
      this.fileInput.nativeElement.value = '';
    }

    this.error = '';
    this.success = '';
    this.showCreateModal = true;
  }

  closeModal(): void {
    this.showCreateModal = false;
    if (this.fileInput) {
      this.fileInput.nativeElement.value = '';
    }
  }

  onSubmit(): void {
    if (this.userForm.invalid) return;
    this.submitting = true;
    this.error = '';
    this.success = '';

    const val = this.userForm.value;
    if (!this.editingUserId) {
      // Create user
      this.adminService.createUser(val).subscribe({
        next: () => {
          this.submitting = false;
          this.success = 'User successfully created!';
          this.loadUsers();
          setTimeout(() => this.closeModal(), 1500);
        },
        error: (err) => {
          this.submitting = false;
          this.error = err.error?.detail || 'Failed to create user.';
        }
      });
    } else {
      // Update user. Clean null or empty password to prevent overriding
      const payload: any = { ...val };
      if (!payload.password) delete payload.password;

      this.adminService.updateUser(this.editingUserId, payload).subscribe({
        next: () => {
          this.submitting = false;
          this.success = 'User profile updated!';
          this.loadUsers();
          setTimeout(() => this.closeModal(), 1500);
        },
        error: (err) => {
          this.submitting = false;
          this.error = err.error?.detail || 'Failed to update user profile.';
        }
      });
    }
  }

  deleteUser(userId: number): void {
    if (userId === this.authService.currentUserValue.id) {
      alert("You cannot delete your own admin account.");
      return;
    }
    if (!confirm("Are you sure you want to permanently delete this user account?")) return;

    this.adminService.deleteUser(userId).subscribe({
      next: () => {
        this.loadUsers();
      },
      error: (err) => {
        alert(err.error?.detail || 'Failed to delete user.');
      }
    });
  }

  onFileSelected(event: any): void {
    const file = event.target.files[0];
    if (!file) return;

    // Validate size (2MB limit)
    if (file.size > 2 * 1024 * 1024) {
      this.error = 'File size exceeds the 2MB limit.';
      if (this.fileInput) this.fileInput.nativeElement.value = '';
      return;
    }

    // Validate mime/type
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      this.error = 'Unsupported file type. Only PNG, JPG, JPEG, and WebP are allowed.';
      if (this.fileInput) this.fileInput.nativeElement.value = '';
      return;
    }

    this.submitting = true;
    this.error = '';
    this.success = '';

    this.adminService.uploadAvatar(file).subscribe({
      next: (res) => {
        this.submitting = false;
        this.userForm.patchValue({ avatar_url: res.avatar_url });
        this.success = 'Avatar uploaded successfully!';
      },
      error: (err) => {
        this.submitting = false;
        this.error = err.error?.detail || 'Failed to upload avatar.';
        if (this.fileInput) this.fileInput.nativeElement.value = '';
      }
    });
  }

  clearAvatar(): void {
    this.userForm.patchValue({ avatar_url: null });
    if (this.fileInput) {
      this.fileInput.nativeElement.value = '';
    }
  }
}
