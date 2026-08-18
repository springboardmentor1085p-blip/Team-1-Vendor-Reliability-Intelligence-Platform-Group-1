import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ProcurementService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getProcurementRequests(status?: string, priority?: string, vendorId?: number): Observable<any[]> {
    let params = new HttpParams();
    if (status) params = params.set('status', status);
    if (priority) params = params.set('priority', priority);
    if (vendorId) params = params.set('vendor_id', vendorId.toString());
    return this.http.get<any[]>(`${this.apiUrl}/procurement/`, { params });
  }

  getProcurementRequest(id: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/procurement/${id}`);
  }

  createProcurementRequest(req: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/procurement/`, req);
  }

  updateProcurementRequest(id: number, req: any): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/procurement/${id}`, req);
  }

  updateProcurementRequestStatus(id: number, status: string): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/procurement/${id}/status`, null, {
      params: new HttpParams().set('status_str', status)
    });
  }

  getPurchaseOrders(status?: string, vendorId?: number, invoiceStatus?: string): Observable<any[]> {
    let params = new HttpParams();
    if (status) params = params.set('status', status);
    if (vendorId) params = params.set('vendor_id', vendorId.toString());
    if (invoiceStatus) params = params.set('invoice_status', invoiceStatus);
    return this.http.get<any[]>(`${this.apiUrl}/purchase-orders/`, { params });
  }

  getPurchaseOrder(id: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/purchase-orders/${id}`);
  }

  createPurchaseOrder(po: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/purchase-orders/`, po);
  }

  updatePurchaseOrder(id: number, po: any): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/purchase-orders/${id}`, po);
  }

  updatePurchaseOrderStatus(id: number, status: string): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/purchase-orders/${id}/status`, null, {
      params: new HttpParams().set('status_str', status)
    });
  }
}
