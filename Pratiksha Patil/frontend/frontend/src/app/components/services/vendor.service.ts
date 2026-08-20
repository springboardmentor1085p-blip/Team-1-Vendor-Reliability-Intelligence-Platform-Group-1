import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class VendorService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}
  getVendors(status?: string, category?: string, search?: string): Observable<any[]> {
    let params = new HttpParams();
    if (status) params = params.set('status', status);
    if (category) params = params.set('category', category);
    if (search) params = params.set('search', search);
    return this.http.get<any[]>(`${this.apiUrl}/vendors/`, { params });
  }

  getVendor(id: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/vendors/${id}`);
  }

  createVendor(vendor: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/vendors/`, vendor);
  }

  updateVendor(id: number, vendor: any): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/vendors/${id}`, vendor);
  }

  updateVendorStatus(id: number, status: string): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/vendors/${id}/status`, null, {
      params: new HttpParams().set('status_str', status)
    });
  }

  getPerformanceLogs(vendorId?: number): Observable<any[]> {
    let params = new HttpParams();
    if (vendorId) params = params.set('vendor_id', vendorId.toString());
    return this.http.get<any[]>(`${this.apiUrl}/performance/`, { params });
  }

  logPerformance(perf: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/performance/`, perf);
  }

  updatePerformance(id: number, perf: any): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/performance/${id}`, perf);
  }

  getReliabilityHistory(vendorId: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/reliability/vendor/${vendorId}`);
  }

  calculateReliability(vendorId: number): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/reliability/vendor/${vendorId}/calculate`, null);
  }

  getVendorRanking(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/reliability/ranking`);
  }
}
