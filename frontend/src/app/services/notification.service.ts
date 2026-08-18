import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private apiUrl = `${environment.apiUrl}/notifications`;

  constructor(private http: HttpClient) {}

  getNotifications(isRead?: boolean): Observable<any[]> {
    let params = new HttpParams();
    if (isRead !== undefined) params = params.set('is_read', isRead.toString());
    return this.http.get<any[]>(`${this.apiUrl}/`, { params });
  }

  getUnreadCount(): Observable<{ unread_count: number }> {
    return this.http.get<{ unread_count: number }>(`${this.apiUrl}/unread-count`);
  }

  markAsRead(id: number): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/${id}/read`, null);
  }

  markAllRead(): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/mark-all-read`, null);
  }
}
