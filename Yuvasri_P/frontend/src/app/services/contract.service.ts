import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ContractService {
  private apiUrl = `${environment.apiUrl}/contracts`;

  constructor(private http: HttpClient) {}

  getContracts(status?: string, vendorId?: number, complianceStatus?: string): Observable<any[]> {
    let params = new HttpParams();
    if (status) params = params.set('status', status);
    if (vendorId) params = params.set('vendor_id', vendorId.toString());
    if (complianceStatus) params = params.set('compliance_status', complianceStatus);
    return this.http.get<any[]>(`${this.apiUrl}/`, { params });
  }

  getContract(id: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/${id}`);
  }

  createContract(contract: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/`, contract);
  }

  updateContract(id: number, contract: any): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/${id}`, contract);
  }
}
