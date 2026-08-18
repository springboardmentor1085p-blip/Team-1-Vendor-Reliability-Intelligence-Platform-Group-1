import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { VendorService } from '../../services/vendor.service';
import { ContractService } from '../../services/contract.service';
import { CommunicationService } from '../../services/communication.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-vendor-detail',
  templateUrl: './vendor-detail.component.html',
  styleUrls: ['./vendor-detail.component.css']
})
export class VendorDetailComponent implements OnInit {
  vendorId!: number;
  vendor: any = null;
  loadingVendor = true;
  activeTab = 'profile';

  // Sub-items
  performances: any[] = [];
  reliabilityHistory: any[] = [];
  contracts: any[] = [];
  messages: any[] = [];

  // Modals & Submitting States
  showPerfModal = false;
  showContractModal = false;
  showMsgModal = false;
  submitting = false;

  // Forms
  perfForm!: FormGroup;
  contractForm!: FormGroup;
  msgForm!: FormGroup;

  error = '';
  success = '';

  constructor(
    private route: ActivatedRoute,
    private vendorService: VendorService,
    private contractService: ContractService,
    private communicationService: CommunicationService,
    public authService: AuthService,
    private fb: FormBuilder
  ) {}

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam) {
      this.vendorId = parseInt(idParam, 10);
      this.loadVendorDetails();
      this.loadAllSubData();
    }
  }

  loadVendorDetails(): void {
    this.loadingVendor = true;
    this.vendorService.getVendor(this.vendorId).subscribe({
      next: (data) => {
        this.vendor = data;
        this.loadingVendor = false;
      },
      error: (err) => {
        console.error('Error loading vendor', err);
        this.loadingVendor = false;
      }
    });
  }

  loadAllSubData(): void {
    this.vendorService.getPerformanceLogs(this.vendorId).subscribe(data => this.performances = data);
    this.vendorService.getReliabilityHistory(this.vendorId).subscribe(data => this.reliabilityHistory = data);
    this.contractService.getContracts(undefined, this.vendorId).subscribe(data => this.contracts = data);
    this.communicationService.getCommunications(this.vendorId).subscribe(data => this.messages = data);
  }

  changeTab(tabName: string): void {
    this.activeTab = tabName;
  }

  recalculateReliability(): void {
    this.loadingVendor = true;
    this.vendorService.calculateReliability(this.vendorId).subscribe({
      next: () => {
        this.loadVendorDetails();
        this.vendorService.getReliabilityHistory(this.vendorId).subscribe(data => {
          this.reliabilityHistory = data;
          this.loadingVendor = false;
        });
      },
      error: (err) => {
        console.error('Error calculating score', err);
        this.loadingVendor = false;
      }
    });
  }

  // Performance Form Modal methods
  openPerfModal(): void {
    this.error = '';
    this.success = '';
    this.perfForm = this.fb.group({
      quality_rating: [90, [Validators.required, Validators.min(0), Validators.max(100)]],
      communication_rating: [90, [Validators.required, Validators.min(0), Validators.max(100)]],
      compliance_rating: [90, [Validators.required, Validators.min(0), Validators.max(100)]],
      issue_resolution_rating: [90, [Validators.required, Validators.min(0), Validators.max(100)]],
      delivery_on_time: [true, Validators.required],
      delivery_delay_days: [0, [Validators.required, Validators.min(0)]],
      comments: ['']
    });
    this.showPerfModal = true;
  }

  submitPerformance(): void {
    if (this.perfForm.invalid) return;
    this.submitting = true;
    const body = {
      vendor_id: this.vendorId,
      ...this.perfForm.value
    };

    this.vendorService.logPerformance(body).subscribe({
      next: () => {
        this.submitting = false;
        this.success = 'Performance successfully logged!';
        this.loadAllSubData();
        this.loadVendorDetails();
        setTimeout(() => this.showPerfModal = false, 1500);
      },
      error: (err) => {
        this.submitting = false;
        this.error = err.error?.detail || 'Failed to submit log.';
      }
    });
  }

  // Contract Form Modal methods
  openContractModal(): void {
    this.error = '';
    this.success = '';
    this.contractForm = this.fb.group({
      contract_number: ['', Validators.required],
      title: ['', Validators.required],
      value: [0, [Validators.required, Validators.min(0)]],
      start_date: ['', Validators.required],
      expiry_date: ['', Validators.required],
      compliance_status: ['Compliant', Validators.required],
      certification_details: ['']
    });
    this.showContractModal = true;
  }

  submitContract(): void {
    if (this.contractForm.invalid) return;
    this.submitting = true;
    const body = {
      vendor_id: this.vendorId,
      ...this.contractForm.value
    };

    this.contractService.createContract(body).subscribe({
      next: () => {
        this.submitting = false;
        this.success = 'Contract created successfully!';
        this.loadAllSubData();
        setTimeout(() => this.showContractModal = false, 1500);
      },
      error: (err) => {
        this.submitting = false;
        this.error = err.error?.detail || 'Failed to submit contract.';
      }
    });
  }

  // Message Modal methods
  openMsgModal(): void {
    this.error = '';
    this.success = '';
    this.msgForm = this.fb.group({
      subject: ['', Validators.required],
      message: ['', Validators.required]
    });
    this.showMsgModal = true;
  }

  submitMessage(): void {
    if (this.msgForm.invalid) return;
    this.submitting = true;
    const body = {
      vendor_id: this.vendorId,
      recipient_id: null, // Broadcast to related vendor contacts
      ...this.msgForm.value
    };

    // If logged in user is a Vendor, send to Admin (ID 1)
    if (this.authService.getRole() === 'Vendor') {
      body.recipient_id = 1; // Default to Admin user
    }

    this.communicationService.sendCommunication(body).subscribe({
      next: () => {
        this.submitting = false;
        this.success = 'Message sent!';
        this.loadAllSubData();
        setTimeout(() => this.showMsgModal = false, 1500);
      },
      error: (err) => {
        this.submitting = false;
        this.error = err.error?.detail || 'Failed to send message.';
      }
    });
  }
}
