import { Component, OnInit } from '@angular/core';
import { VendorService } from '../../services/vendor.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-performance',
  templateUrl: './performance.component.html',
  styleUrls: ['./performance.component.css']
})
export class PerformanceComponent implements OnInit {
  logs: any[] = [];
  loading = false;

  constructor(
    private vendorService: VendorService,
    public authService: AuthService
  ) {}

  ngOnInit(): void {
    this.loadLogs();
  }

  loadLogs(): void {
    this.loading = true;
    this.vendorService.getPerformanceLogs().subscribe({
      next: (data) => {
        this.logs = data;
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading performance logs', err);
        this.loading = false;
      }
    });
  }
}
