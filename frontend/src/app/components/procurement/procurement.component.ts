import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ProcurementService } from '../../services/procurement.service';
import { VendorService } from '../../services/vendor.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-procurement',
  templateUrl: './procurement.component.html',
  styleUrls: ['./procurement.component.css']
})
export class ProcurementComponent implements OnInit {
  requests: any[] = [];
  filteredRequests: any[] = [];
  vendors: any[] = [];
  loading = false;
  submitting = false;

  // Filter bindings
  searchQuery = '';
  selectedStatus = '';
  selectedPriority = '';

  // Create Form
  showCreateModal = false;
  requestForm!: FormGroup;
  error = '';
  success = '';

  priorities = ['Low', 'Medium', 'High', 'Critical'];
  statuses = ['Pending', 'Approved', 'Rejected', 'Cancelled', 'Ordered', 'Delivered', 'Completed'];

  constructor(
    private procurementService: ProcurementService,
    private vendorService: VendorService,
    public authService: AuthService,
    private fb: FormBuilder
  ) {}

  ngOnInit(): void {
    this.loadRequests();
    this.loadVendors();
    this.initForm();
  }

  initForm(): void {
    this.requestForm = this.fb.group({
      title: ['', Validators.required],
      description: [''],
      priority: ['Medium', Validators.required],
      estimated_cost: [0, [Validators.required, Validators.min(0)]],
      vendor_id: [null]
    });
  }

  loadRequests(): void {
    this.loading = true;
    this.procurementService.getProcurementRequests().subscribe({
      next: (data) => {
        this.requests = data;
        this.applyFilters();
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading requests', err);
        this.loading = false;
      }
    });
  }

  loadVendors(): void {
    if (this.authService.getRole() !== 'Vendor') {
      this.vendorService.getVendors('Active').subscribe(data => this.vendors = data);
    }
  }

  applyFilters(): void {
    this.filteredRequests = this.requests.filter(r => {
      const matchesSearch = !this.searchQuery || 
        r.title.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
        (r.description && r.description.toLowerCase().includes(this.searchQuery.toLowerCase()));
      const matchesStatus = !this.selectedStatus || r.status === this.selectedStatus;
      const matchesPriority = !this.selectedPriority || r.priority === this.selectedPriority;
      return matchesSearch && matchesStatus && matchesPriority;
    });
  }

  openModal(): void {
    this.initForm();
    this.error = '';
    this.success = '';
    this.showCreateModal = true;
  }

  closeModal(): void {
    this.showCreateModal = false;
  }

  onSubmit(): void {
    if (this.requestForm.invalid) return;
    this.submitting = true;
    this.error = '';
    this.success = '';

    this.procurementService.createProcurementRequest(this.requestForm.value).subscribe({
      next: () => {
        this.submitting = false;
        this.success = 'Procurement request submitted successfully!';
        this.loadRequests();
        setTimeout(() => this.closeModal(), 1500);
      },
      error: (err) => {
        this.submitting = false;
        this.error = err.error?.detail || 'Failed to submit request.';
      }
    });
  }

  updateStatus(requestId: number, newStatus: string): void {
    if (!confirm(`Are you sure you want to update request status to ${newStatus}?`)) return;

    this.procurementService.updateProcurementRequestStatus(requestId, newStatus).subscribe({
      next: () => {
        this.loadRequests();
      },
      error: (err) => {
        alert(err.error?.detail || 'Failed to update request status.');
      }
    });
  }
}
