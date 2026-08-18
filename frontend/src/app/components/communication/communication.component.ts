import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { CommunicationService } from '../../services/communication.service';
import { AdminService } from '../../services/admin.service';
import { VendorService } from '../../services/vendor.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-communication',
  templateUrl: './communication.component.html',
  styleUrls: ['./communication.component.css']
})
export class CommunicationComponent implements OnInit {
  messages: any[] = [];
  users: any[] = [];
  vendors: any[] = [];
  loading = false;
  submitting = false;

  // Compose Message Form
  showComposeModal = false;
  msgForm!: FormGroup;
  error = '';
  success = '';

  // File Sharing
  selectedFile: File | null = null;
  uploadProgress = false;
  uploadError = '';

  constructor(
    private communicationService: CommunicationService,
    private adminService: AdminService,
    private vendorService: VendorService,
    public authService: AuthService,
    private fb: FormBuilder
  ) {}

  ngOnInit(): void {
    this.loadMessages();
    this.loadUsersAndVendors();
    this.initForm();
  }

  initForm(): void {
    this.msgForm = this.fb.group({
      recipient_id: [null],
      vendor_id: [null],
      subject: ['', Validators.required],
      message: ['', Validators.required]
    });

    // Conditional validator based on role
    const role = this.authService.getRole();
    if (role !== 'Vendor') {
      this.msgForm.get('recipient_id')?.setValidators([Validators.required]);
      this.msgForm.get('vendor_id')?.setValidators([Validators.required]);
    } else {
      // Vendor sends to Admin (ID 1) by default
      this.msgForm.get('recipient_id')?.setValue(1); 
    }
  }

  loadMessages(): void {
    this.loading = true;
    this.communicationService.getCommunications().subscribe({
      next: (data) => {
        this.messages = data;
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading communications', err);
        this.loading = false;
      }
    });
  }

  loadUsersAndVendors(): void {
    const role = this.authService.getRole();
    if (role !== 'Vendor') {
      // Load user accounts for recipient dropdown
      this.adminService.getUsers().subscribe(data => {
        // Exclude current user from receiving from self
        const me = this.authService.currentUserValue;
        this.users = data.filter(u => u.id !== me.id);
      });
      // Load active vendors
      this.vendorService.getVendors('Active').subscribe(data => this.vendors = data);
    }
  }

  openModal(): void {
    this.initForm();
    this.selectedFile = null;
    this.uploadError = '';
    this.error = '';
    this.success = '';
    this.showComposeModal = true;
  }

  closeModal(): void {
    this.showComposeModal = false;
  }

  onFileSelected(event: any): void {
    const file = event.target.files[0];
    if (!file) return;

    this.uploadError = '';
    
    // Check file size (10 MB limit)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      this.uploadError = 'File size exceeds the 10 MB limit.';
      this.selectedFile = null;
      return;
    }

    // Check extension
    const allowedExtensions = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'png', 'jpg', 'jpeg', 'txt'];
    const extension = file.name.split('.').pop().toLowerCase();
    if (!allowedExtensions.includes(extension)) {
      this.uploadError = 'Allowed file formats: PDF, DOC, DOCX, XLS, XLSX, CSV, PNG, JPG, JPEG, TXT.';
      this.selectedFile = null;
      return;
    }

    this.selectedFile = file;
  }

  removeAttachment(): void {
    this.selectedFile = null;
    this.uploadError = '';
  }

  onSubmit(): void {
    if (this.msgForm.invalid) return;
    this.submitting = true;
    this.error = '';
    this.success = '';

    const body = { ...this.msgForm.value };
    // If current user is a Vendor, attach their linked vendor id automatically
    if (this.authService.getRole() === 'Vendor') {
      body.vendor_id = this.authService.currentUserValue.vendor_id;
    }

    if (this.selectedFile) {
      this.uploadProgress = true;
      this.communicationService.uploadFile(this.selectedFile).subscribe({
        next: (uploadRes) => {
          body.attachment_name = uploadRes.attachment_name;
          body.attachment_path = uploadRes.attachment_path;
          body.attachment_size = uploadRes.attachment_size;
          body.attachment_type = uploadRes.attachment_type;
          
          this.sendMsg(body);
        },
        error: (err) => {
          this.submitting = false;
          this.uploadProgress = false;
          this.error = err.error?.detail || 'Failed to upload attachment.';
        }
      });
    } else {
      this.sendMsg(body);
    }
  }

  sendMsg(body: any): void {
    this.communicationService.sendCommunication(body).subscribe({
      next: () => {
        this.submitting = false;
        this.uploadProgress = false;
        this.selectedFile = null;
        this.success = 'Message sent successfully!';
        this.loadMessages();
        setTimeout(() => this.closeModal(), 1500);
      },
      error: (err) => {
        this.submitting = false;
        this.uploadProgress = false;
        this.error = err.error?.detail || 'Failed to send message.';
      }
    });
  }

  downloadFile(msg: any): void {
    if (!msg.attachment_path) return;
    
    this.communicationService.downloadAttachment(msg.id).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = msg.attachment_name;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      },
      error: (err) => {
        alert('Failed to download attachment. You may not have access rights.');
      }
    });
  }

  formatBytes(bytes: number, decimals = 2): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }

  markAsRead(msgId: number): void {
    this.communicationService.markAsRead(msgId).subscribe({
      next: () => {
        this.loadMessages();
      }
    });
  }
}
