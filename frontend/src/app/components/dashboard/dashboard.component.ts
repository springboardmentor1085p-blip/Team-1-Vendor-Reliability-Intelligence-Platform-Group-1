import { Component, OnInit, AfterViewInit, OnDestroy, ElementRef, ViewChild } from '@angular/core';
import { Chart } from 'chart.js/auto';
import { DashboardService } from '../../services/dashboard.service';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit, OnDestroy {
  kpis: any = {
    total_vendors: 0,
    active_vendors: 0,
    pending_approvals: 0,
    active_pos: 0,
    procurement_value: 0.0,
    average_reliability: 100.0,
    high_risk_vendors: 0,
    expiring_contracts: 0
  };

  chartsData: any = null;
  loadingKPIs = true;
  loadingCharts = true;
  recentActivities: any[] = [];
  riskActions: any[] = [];

  // Chart references for destruction
  private spendingChart: Chart | null = null;
  private reliabilityChart: Chart | null = null;

  @ViewChild('spendingCanvas') spendingCanvas!: ElementRef<HTMLCanvasElement>;
  @ViewChild('reliabilityCanvas') reliabilityCanvas!: ElementRef<HTMLCanvasElement>;

  constructor(private dashboardService: DashboardService) {}

  ngOnInit(): void {
    this.loadKPIs();
    this.loadCharts();
  }

  ngOnDestroy(): void {
    // Clean up charts to avoid canvas recycling errors
    if (this.spendingChart) this.spendingChart.destroy();
    if (this.reliabilityChart) this.reliabilityChart.destroy();
  }

  loadKPIs(): void {
    this.dashboardService.getKPIs().subscribe({
      next: (data) => {
        this.kpis = data;
        this.loadingKPIs = false;
      },
      error: (err) => {
        console.error('Error fetching KPIs', err);
        this.loadingKPIs = false;
      }
    });
  }

  loadCharts(): void {
    this.dashboardService.getCharts().subscribe({
      next: (data) => {
        this.chartsData = data;
        this.recentActivities = data.recent_activities || [];
        this.riskActions = data.risk_actions || [];
        this.loadingCharts = false;
        // Schedule chart rendering in macro-task queue to ensure canvas elements exist in view
        setTimeout(() => this.renderCharts(), 0);
      },
      error: (err) => {
        console.error('Error fetching charts', err);
        this.loadingCharts = false;
      }
    });
  }

  renderCharts(): void {
    if (!this.chartsData) return;

    // 1. Procurement Spend Trend (Line Chart with Shading)
    const months = this.chartsData.spending_by_month.map((x: any) => x.month);
    const spending = this.chartsData.spending_by_month.map((x: any) => x.amount);
    
    this.spendingChart = new Chart(this.spendingCanvas.nativeElement, {
      type: 'line',
      data: {
        labels: months,
        datasets: [{
          label: 'Spending ($)',
          data: spending,
          borderColor: '#0ea5e9',
          backgroundColor: 'rgba(14, 165, 233, 0.08)',
          fill: true,
          tension: 0.3,
          borderWidth: 2,
          pointBackgroundColor: '#0ea5e9',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 1.5,
          pointRadius: 4,
          pointHoverRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { 
          legend: { display: false }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: '#64748b', font: { size: 11 } }
          },
          y: {
            grid: { color: '#f1f5f9' },
            ticks: { 
              color: '#64748b', 
              font: { size: 11 },
              callback: (value) => '$' + Number(value).toLocaleString()
            }
          }
        }
      }
    });

    // 2. Vendor Reliability & Risk Overview (Doughnut Chart)
    const riskLabels = this.chartsData.risk_distribution.map((x: any) => x.risk_level);
    const riskCounts = this.chartsData.risk_distribution.map((x: any) => x.count);

    // Map risk levels to professional enterprise colors
    const colorMap: { [key: string]: string } = {
      'LOW': '#10b981',       // Healthy green
      'MEDIUM': '#f59e0b',    // Warning orange
      'HIGH': '#ef4444',      // Action red
      'CRITICAL': '#7f1d1d'   // Critical dark red
    };
    const colors = riskLabels.map((label: string) => colorMap[label] || '#94a3b8');
    
    this.reliabilityChart = new Chart(this.reliabilityCanvas.nativeElement, {
      type: 'doughnut',
      data: {
        labels: riskLabels,
        datasets: [{
          data: riskCounts,
          backgroundColor: colors,
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              boxWidth: 8,
              padding: 12,
              font: { size: 11, family: 'Inter' },
              color: '#64748b'
            }
          }
        },
        cutout: '65%'
      }
    });
  }

  getRiskRoute(item: any): any[] {
    if (item.type === 'high_risk_vendor') {
      return ['/vendors', item.id];
    } else if (item.type === 'pending_approval') {
      return ['/procurement'];
    } else if (item.type === 'expiring_contract') {
      return ['/contracts'];
    }
    return ['/dashboard'];
  }
}
