import { Component, OnInit } from '@angular/core';
import { AdminService } from '../../services/admin.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-audit-logs',
  templateUrl: './audit-logs.component.html',
  styleUrls: ['./audit-logs.component.css']
})
export class AuditLogsComponent implements OnInit {
  logs: any[] = [];
  loading = false;

  // Filter bindings
  selectedModule = '';
  selectedAction = '';
  searchUsername = '';

  modules = ['Auth', 'Users', 'Vendors', 'Procurement', 'Purchase Orders', 'Performance', 'Reliability', 'Contracts', 'Communication'];
  actions = ['User Login', 'User Registered', 'Create User', 'Update User', 'Delete User', 'Create Vendor', 'Update Vendor', 'Update Vendor Status', 'Create Procurement Request', 'Update Procurement Request', 'Update Procurement Status', 'Create Purchase Order', 'Update Purchase Order', 'Update PO Status', 'Log Vendor Performance', 'Update Vendor Performance', 'Calculate Reliability Score', 'Create Contract', 'Update Contract', 'Send Message', 'Database Seeded'];

  constructor(
    private adminService: AdminService,
    public authService: AuthService
  ) {}

  ngOnInit(): void {
    this.loadLogs();
  }

  loadLogs(): void {
    this.loading = true;
    this.adminService.getAuditLogs(
      this.selectedModule || undefined,
      this.selectedAction || undefined,
      this.searchUsername || undefined
    ).subscribe({
      next: (data) => {
        this.logs = data;
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading audit logs', err);
        this.loading = false;
      }
    });
  }

  resetFilters(): void {
    this.selectedModule = '';
    this.selectedAction = '';
    this.searchUsername = '';
    this.loadLogs();
  }
}
