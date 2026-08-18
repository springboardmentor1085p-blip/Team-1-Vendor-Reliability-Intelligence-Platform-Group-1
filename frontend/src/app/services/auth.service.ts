import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, tap, map, catchError, of } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = `${environment.apiUrl}/auth`;
  private currentUserSubject = new BehaviorSubject<any>(null);
  public currentUser$ = this.currentUserSubject.asObservable();

  constructor(private http: HttpClient) {
    this.loadCurrentUser();
  }

  private loadCurrentUser() {
    const token = this.getToken();
    if (token) {
      const payload = this.decodeToken(token);
      if (payload && payload.exp * 1000 > Date.now()) {
        // Fetch fresh details from /me to populate BehaviorSubject
        this.http.get<any>(`${this.apiUrl}/me`).pipe(
          catchError(() => {
            this.logout();
            return of(null);
          })
        ).subscribe(user => {
          if (user) {
            this.currentUserSubject.next(user);
          }
        });
      } else {
        this.logout();
      }
    }
  }

  public get currentUserValue() {
    return this.currentUserSubject.value;
  }

  public getToken(): string | null {
    return localStorage.getItem('vendoriq_token');
  }

  public register(user: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/register`, user);
  }

  public login(credentials: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/login`, credentials).pipe(
      tap(res => {
        localStorage.setItem('vendoriq_token', res.access_token);
        this.loadCurrentUser();
      })
    );
  }

  public logout() {
    localStorage.removeItem('vendoriq_token');
    this.currentUserSubject.next(null);
  }

  public forgotPassword(email: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/forgot-password`, { email });
  }

  public resetPassword(data: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/reset-password`, data);
  }

  public isAuthenticated(): boolean {
    const token = this.getToken();
    if (!token) return false;
    const payload = this.decodeToken(token);
    return payload ? payload.exp * 1000 > Date.now() : false;
  }

  public hasRole(roles: string[]): boolean {
    const user = this.currentUserValue;
    if (!user) return false;
    return roles.includes(user.role);
  }

  public getRole(): string | null {
    const user = this.currentUserValue;
    return user ? user.role : null;
  }

  private decodeToken(token: string): any {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) return null;
      const payload = parts[1];
      const decoded = window.atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
      return JSON.parse(decoded);
    } catch (e) {
      return null;
    }
  }

  public getAvatarUrl(avatarPath: string | null): string {
    const defaultAvatar = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iI2NiZDVlMSI+PHBhdGggZD0iTTEyIDEyYzIuMjEgMCA0LTEuNzkgNC00cy0xLjc5LTQtNC00LTQgMS43OS00IDQgMS43OSA0IDQgNHptMCAyYy0yLjY3IDAtOCAxLjM0LTggNHYyaDE2di0yYzAtMi42Ni01LjMzLTQtOC00eiIvPjwvc3ZnPg==';
    if (!avatarPath) return defaultAvatar;
    if (avatarPath.startsWith('http://') || avatarPath.startsWith('https://') || avatarPath.startsWith('data:')) {
      return avatarPath;
    }
    const base = environment.apiUrl.replace('/api', '');
    return `${base}${avatarPath}`;
  }

  public uploadMyAvatar(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<any>(`${this.apiUrl}/me/avatar`, formData).pipe(
      tap(user => {
        if (user) {
          this.currentUserSubject.next(user);
        }
      })
    );
  }

  public deleteMyAvatar(): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/me/avatar`).pipe(
      tap(user => {
        if (user) {
          this.currentUserSubject.next(user);
        }
      })
    );
  }
}
