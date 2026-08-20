import { Injectable } from '@angular/core';
import { CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {
  constructor(private authService: AuthService, private router: Router) {}

  canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): boolean {
    if (this.authService.isAuthenticated()) {
      const requiredRoles = route.data['roles'] as Array<string>;
      
      if (requiredRoles) {
        const hasRole = this.authService.hasRole(requiredRoles);
        if (!hasRole) {
          // Redirect to dashboard if they don't have the required role
          this.router.navigate(['/dashboard']);
          return false;
        }
      }
      return true;
    }

    // Not logged in, redirect to login page with returnUrl
    this.router.navigate(['/login'], { queryParams: { returnUrl: state.url } });
    return false;
  }
}
