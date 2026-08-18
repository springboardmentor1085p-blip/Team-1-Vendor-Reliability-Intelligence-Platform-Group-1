import { Component, OnInit, OnDestroy, HostListener } from '@angular/core';
import { Router } from '@angular/router';
import { Subscription, interval, startWith, switchMap } from 'rxjs';
import { AuthService } from '../../services/auth.service';
import { NotificationService } from '../../services/notification.service';

@Component({
  selector: 'app-shell',
  templateUrl: './shell.component.html',
  styleUrls: ['./shell.component.css']
})
export class ShellComponent implements OnInit, OnDestroy {
  currentUser: any = null;
  unreadNotificationsCount = 0;
  isDropdownOpen = false;
  isSearchOpen = false;
  isSidebarOpen = false;
  searchQuery = '';
  private notifSub!: Subscription;
  private userSub!: Subscription;

  constructor(
    public authService: AuthService,
    private notificationService: NotificationService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.userSub = this.authService.currentUser$.subscribe(user => {
      this.currentUser = user;
    });

    // Auto-close sidebar on router navigation changes
    this.router.events.subscribe(() => {
      this.isSidebarOpen = false;
    });

    // Poll for unread notification count every 30 seconds
    this.notifSub = interval(30000).pipe(
      startWith(0),
      switchMap(() => {
        if (this.authService.isAuthenticated()) {
          return this.notificationService.getUnreadCount();
        }
        return [];
      })
    ).subscribe({
      next: (res) => {
        this.unreadNotificationsCount = res.unread_count;
      },
      error: (err) => console.error('Notification error', err)
    });
  }

  ngOnDestroy(): void {
    if (this.notifSub) this.notifSub.unsubscribe();
    if (this.userSub) this.userSub.unsubscribe();
  }

  hasAccess(allowedRoles: string[]): boolean {
    return this.authService.hasRole(allowedRoles);
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  toggleDropdown(event: Event): void {
    event.stopPropagation();
    this.isDropdownOpen = !this.isDropdownOpen;
    this.isSearchOpen = false;
  }

  toggleSearch(event: Event): void {
    event.stopPropagation();
    this.isSearchOpen = !this.isSearchOpen;
    this.isDropdownOpen = false;
  }

  closeSearch(): void {
    this.isSearchOpen = false;
    this.searchQuery = '';
  }

  executeSearch(): void {
    if (this.searchQuery.trim()) {
      this.router.navigate(['/vendors'], { queryParams: { q: this.searchQuery } });
      this.isSearchOpen = false;
    }
  }

  toggleSidebar(event: Event): void {
    event.stopPropagation();
    this.isSidebarOpen = !this.isSidebarOpen;
  }

  closeSidebar(): void {
    this.isSidebarOpen = false;
  }

  @HostListener('document:click', [])
  onDocumentClick(): void {
    this.isDropdownOpen = false;
    this.isSearchOpen = false;
    this.isSidebarOpen = false;
  }

  @HostListener('window:keydown.escape', ['$event'])
  onEscapePressed(event: KeyboardEvent): void {
    this.isDropdownOpen = false;
    this.isSearchOpen = false;
    this.isSidebarOpen = false;
  }
}
