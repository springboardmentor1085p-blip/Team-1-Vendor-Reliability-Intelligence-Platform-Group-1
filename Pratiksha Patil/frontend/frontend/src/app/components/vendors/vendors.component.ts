import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { VendorService } from '../../services/vendor.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-vendors',
  templateUrl: './vendors.component.html',
  styleUrls: ['./vendors.component.css']
})
export class VendorsComponent implements OnInit {
  vendors: any[] = [];
  filteredVendors: any[] = [];
  categories = [
    'Raw Material Supplier',
    'Equipment Vendor',
    'IT Vendor',
    'Service Provider',
    'Logistics Partner',
    'Maintenance Vendor'
  ];
  statuses = ['Pending Approval', 'Active', 'Inactive', 'Rejected'];
  
  // Filters
  searchQuery = '';
  selectedCategory = '';
  selectedStatus = '';

  // Vendor Form
  vendorForm!: FormGroup;
  showCreateModal = false;
  loading = false;
  submitting = false;
  error = '';
  success = '';

  constructor(
    private vendorService: VendorService,
    private authService: AuthService,
    private fb: FormBuilder,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    this.route.queryParams.subscribe(params => {
      this.searchQuery = params['q'] || '';
      this.applyFilters();
    });
    this.loadVendors();
    this.initForm();
  }

  initForm(): void {
    this.vendorForm = this.fb.group({
      name: ['', [Validators.required, Validators.minLength(2)]],
      category: ['Raw Material Supplier', Validators.required],
      contact_person: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      phone: ['', Validators.required],
      address: ['']
    });
  }

  loadVendors(): void {
    this.loading = true;
    this.vendorService.getVendors().subscribe({
      next: (data) => {
        this.vendors = data;
        this.applyFilters();
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading vendors', err);
        this.loading = false;
      }
    });
  }

  applyFilters(): void {
    this.filteredVendors = this.vendors.filter(v => {
      const matchesSearch = !this.searchQuery || 
        v.name.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
        (v.contact_person && v.contact_person.toLowerCase().includes(this.searchQuery.toLowerCase()));
      
      const matchesCategory = !this.selectedCategory || v.category === this.selectedCategory;
      const matchesStatus = !this.selectedStatus || v.status === this.selectedStatus;

      return matchesSearch && matchesCategory && matchesStatus;
    });
  }

  hasAccess(roles: string[]): boolean {
    return this.authService.hasRole(roles);
  }

  openModal(): void {
    this.showCreateModal = true;
    this.initForm();
    this.error = '';
    this.success = '';
  }

  closeModal(): void {
    this.showCreateModal = false;
  }

  onSubmit(): void {
    if (this.vendorForm.invalid) return;

    this.submitting = true;
    this.error = '';
    this.success = '';

    this.vendorService.createVendor(this.vendorForm.value).subscribe({
      next: () => {
        this.submitting = false;
        this.success = 'Vendor successfully created!';
        this.loadVendors();
        setTimeout(() => this.closeModal(), 1500);
      },
      error: (err) => {
        this.submitting = false;
        this.error = err.error?.detail || 'Failed to register vendor.';
      }
    });
  }

  updateStatus(vendorId: number, status: string): void {
    if (!confirm(`Are you sure you want to set this vendor status to ${status}?`)) return;
    
    this.vendorService.updateVendorStatus(vendorId, status).subscribe({
      next: () => {
        this.loadVendors();
      },
      error: (err) => {
        alert(err.error?.detail || 'Failed to update vendor status.');
      }
    });
  }
}
