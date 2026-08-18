import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class CommunicationService {
  private apiUrl = `${environment.apiUrl}/communications`;

  constructor(private http: HttpClient) {}

  getCommunications(vendorId?: number): Observable<any[]> {
    let params = new HttpParams();
    if (vendorId) params = params.set('vendor_id', vendorId.toString());
    return this.http.get<any[]>(`${this.apiUrl}/`, { params });
  }

  sendCommunication(msg: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/`, msg);
  }

  markAsRead(id: number): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/${id}/read`, null);
  }

  uploadFile(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<any>(`${this.apiUrl}/upload-file`, formData);
  }

  downloadAttachment(id: number): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/${id}/download`, { responseType: 'blob' });
  }
}
