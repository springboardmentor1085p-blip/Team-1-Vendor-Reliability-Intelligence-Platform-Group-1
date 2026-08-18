import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ReportService {
  private apiUrl = `${environment.apiUrl}/reports`;

  constructor(private http: HttpClient) {}

  getVendorsSummary(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/summary/vendors`);
  }

  getProcurementSummary(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/summary/procurement`);
  }

  getPOSummary(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/summary/purchase-orders`);
  }

  getContractsSummary(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/summary/contracts`);
  }

  downloadReport(type: 'vendors' | 'procurement' | 'purchase-orders' | 'contracts', format: 'csv' | 'excel' | 'pdf' = 'csv') {
    return this.http.get(`${this.apiUrl}/export/${type}?format=${format}`, { responseType: 'blob' }).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const ext = format === 'excel' ? 'xlsx' : (format === 'pdf' ? 'pdf' : 'csv');
        a.download = `${type}_report_${new Date().toISOString().split('T')[0]}.${ext}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      },
      error: (err) => {
        console.error('Error exporting report', err);
      }
    });
  }
}
