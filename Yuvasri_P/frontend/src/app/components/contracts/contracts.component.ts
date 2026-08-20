import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ContractService } from '../../services/contract.service';
import { VendorService } from '../../services/vendor.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-contracts',
  templateUrl: './contracts.component.html',
  styleUrls: ['./contracts.component.css']
})
export class ContractsComponent implements OnInit {
  contracts: any[] = [];
  filteredContracts: any[] = [];
  vendors: any[] = [];
  loading = false;
  submitting = false;

  // Filter bindings
  searchQuery = '';
  selectedStatus = '';
  selectedCompliance = '';

  // Contract Form
  showCreateModal = false;
  contractForm!: FormGroup;
  error = '';
  success = '';

  statuses = ['Active', 'Expiring Soon', 'Expired', 'Renewed', 'Terminated'];
  compliances = ['Compliant', 'Non-Compliant', 'Under Review'];

  constructor(
    private contractService: ContractService,
    private vendorService: VendorService,
    public authService: AuthService,
    private fb: FormBuilder
  ) {}

  ngOnInit(): void {
    this.loadContracts();
    this.loadVendors();
    this.initForm();
  }

  initForm(): void {
    this.contractForm = this.fb.group({
      contract_number: ['', Validators.required],
      vendor_id: [null, Validators.required],
      title: ['', Validators.required],
      value: [0, [Validators.required, Validators.min(0)]],
      start_date: ['', Validators.required],
      expiry_date: ['', Validators.required],
      compliance_status: ['Compliant', Validators.required],
      certification_details: ['']
    });
  }

  loadContracts(): void {
    this.loading = true;
    this.contractService.getContracts().subscribe({
      next: (data) => {
        this.contracts = data;
        this.applyFilters();
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading contracts', err);
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
    this.filteredContracts = this.contracts.filter(c => {
      const matchesSearch = !this.searchQuery || 
        c.contract_number.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
        c.title.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
        c.vendor.name.toLowerCase().includes(this.searchQuery.toLowerCase());
      
      const matchesStatus = !this.selectedStatus || c.status === this.selectedStatus;
      const matchesCompliance = !this.selectedCompliance || c.compliance_status === this.selectedCompliance;

      return matchesSearch && matchesStatus && matchesCompliance;
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
    if (this.contractForm.invalid) return;
    this.submitting = true;
    this.error = '';
    this.success = '';

    this.contractService.createContract(this.contractForm.value).subscribe({
      next: () => {
        this.submitting = false;
        this.success = 'Contract created successfully!';
        this.loadContracts();
        setTimeout(() => this.closeModal(), 1500);
      },
      error: (err) => {
        this.submitting = false;
        this.error = err.error?.detail || 'Failed to submit contract.';
      }
    });
  }
}
