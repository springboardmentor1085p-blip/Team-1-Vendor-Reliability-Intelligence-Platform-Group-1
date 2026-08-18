import { Component, OnInit } from '@angular/core';
import { ReportService } from '../../services/report.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-reports',
  templateUrl: './reports.component.html',
  styleUrls: ['./reports.component.css']
})
export class ReportsComponent implements OnInit {
  activeTab = 'vendors';
  loading = false;
  summaryData: any = null;

  constructor(
    private reportService: ReportService,
    public authService: AuthService
  ) {}

  ngOnInit(): void {
    this.loadSummary();
  }

  changeTab(tabName: string): void {
    this.activeTab = tabName;
    this.loadSummary();
  }

  loadSummary(): void {
    this.loading = true;
    this.summaryData = null;
    
    if (this.activeTab === 'vendors') {
      this.reportService.getVendorsSummary().subscribe(data => {
        this.summaryData = data;
        this.loading = false;
      });
    } else if (this.activeTab === 'procurement') {
      this.reportService.getProcurementSummary().subscribe(data => {
        const mapped = { ...data };
        mapped.status_list = Object.keys(data.status_distribution || {}).map(k => ({
          key: k,
          value: data.status_distribution[k]
        }));
        this.summaryData = mapped;
        this.loading = false;
      });
    } else if (this.activeTab === 'purchase-orders') {
      this.reportService.getPOSummary().subscribe(data => {
        const mapped = { ...data };
        mapped.status_list = Object.keys(data.status_distribution || {}).map(k => ({
          key: k,
          value: data.status_distribution[k]
        }));
        this.summaryData = mapped;
        this.loading = false;
      });
    } else if (this.activeTab === 'contracts') {
      this.reportService.getContractsSummary().subscribe(data => {
        const mapped = { ...data };
        mapped.compliance_list = Object.keys(data.compliance_distribution || {}).map(k => ({
          key: k,
          value: data.compliance_distribution[k]
        }));
        this.summaryData = mapped;
        this.loading = false;
      });
    }
  }

  downloadReport(format: 'csv' | 'excel' | 'pdf'): void {
    const reportType = this.activeTab as 'vendors' | 'procurement' | 'purchase-orders' | 'contracts';
    this.reportService.downloadReport(reportType, format);
  }
}
