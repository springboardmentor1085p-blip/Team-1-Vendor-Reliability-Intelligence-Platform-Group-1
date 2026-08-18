import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ProcurementService } from '../../services/procurement.service';
import { VendorService } from '../../services/vendor.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-purchase-orders',
  templateUrl: './purchase-orders.component.html',
  styleUrls: ['./purchase-orders.component.css']
})
export class PurchaseOrdersComponent implements OnInit {
  orders: any[] = [];
  filteredOrders: any[] = [];
  approvedRequests: any[] = [];
  vendors: any[] = [];
  loading = false;
  submitting = false;

  // Filter bindings
  searchQuery = '';
  selectedStatus = '';
  selectedInvoice = '';

  // Modal Form
  showCreateModal = false;
  poForm!: FormGroup;
  error = '';
  success = '';

  statuses = ['Pending Approval', 'Approved', 'Ordered', 'Delivered', 'Completed', 'Cancelled'];
  invoices = ['Unpaid', 'Paid', 'Invoiced'];

  constructor(
    private procurementService: ProcurementService,
    private vendorService: VendorService,
    public authService: AuthService,
    private fb: FormBuilder
  ) {}

  ngOnInit(): void {
    this.loadOrders();
    this.loadApprovedRequests();
    this.loadVendors();
    this.initForm();
  }

  initForm(): void {
    this.poForm = this.fb.group({
      procurement_request_id: [null, Validators.required],
      vendor_id: [null, Validators.required],
      amount: [0, [Validators.required, Validators.min(0)]],
      expected_delivery_date: ['', Validators.required]
    });

    // Automatically populate amount and vendor if request changes
    this.poForm.get('procurement_request_id')?.valueChanges.subscribe(reqId => {
      if (reqId) {
        const req = this.approvedRequests.find(r => r.id === reqId);
        if (req) {
          this.poForm.patchValue({
            amount: req.estimated_cost,
            vendor_id: req.vendor_id
          });
        }
      }
    });
  }

  loadOrders(): void {
    this.loading = true;
    this.procurementService.getPurchaseOrders().subscribe({
      next: (data) => {
        this.orders = data;
        this.applyFilters();
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading purchase orders', err);
        this.loading = false;
      }
    });
  }

  loadApprovedRequests(): void {
    if (this.authService.getRole() !== 'Vendor') {
      this.procurementService.getProcurementRequests('Approved').subscribe(data => this.approvedRequests = data);
    }
  }

  loadVendors(): void {
    if (this.authService.getRole() !== 'Vendor') {
      this.vendorService.getVendors('Active').subscribe(data => this.vendors = data);
    }
  }

  applyFilters(): void {
    this.filteredOrders = this.orders.filter(po => {
      const matchesSearch = !this.searchQuery || 
        po.po_number.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
        po.vendor.name.toLowerCase().includes(this.searchQuery.toLowerCase());
      
      const matchesStatus = !this.selectedStatus || po.status === this.selectedStatus;
      const matchesInvoice = !this.selectedInvoice || po.invoice_status === this.selectedInvoice;

      return matchesSearch && matchesStatus && matchesInvoice;
    });
  }

  openModal(): void {
    this.loadApprovedRequests();
    this.initForm();
    this.error = '';
    this.success = '';
    this.showCreateModal = true;
  }

  closeModal(): void {
    this.showCreateModal = false;
  }

  onSubmit(): void {
    if (this.poForm.invalid) return;
    this.submitting = true;
    this.error = '';
    this.success = '';

    this.procurementService.createPurchaseOrder(this.poForm.value).subscribe({
      next: () => {
        this.submitting = false;
        this.success = 'Purchase Order created and submitted!';
        this.loadOrders();
        setTimeout(() => this.closeModal(), 1500);
      },
      error: (err) => {
        this.submitting = false;
        this.error = err.error?.detail || 'Failed to submit Purchase Order.';
      }
    });
  }

  updateStatus(poId: number, status: string): void {
    if (!confirm(`Are you sure you want to transition this PO status to ${status}?`)) return;

    this.procurementService.updatePurchaseOrderStatus(poId, status).subscribe({
      next: () => {
        this.loadOrders();
      },
      error: (err) => {
        alert(err.error?.detail || 'Failed to update order status.');
      }
    });
  }

  updateInvoice(poId: number, invoice: string): void {
    this.procurementService.updatePurchaseOrder(poId, { invoice_status: invoice }).subscribe({
      next: () => {
        this.loadOrders();
      },
      error: (err) => {
        alert(err.error?.detail || 'Failed to update invoice status.');
      }
    });
  }
}
