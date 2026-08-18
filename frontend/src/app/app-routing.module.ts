import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

// Guards
import { AuthGuard } from './guards/auth.guard';

// Components
import { LoginComponent } from './components/login/login.component';
import { RegisterComponent } from './components/register/register.component';
import { ShellComponent } from './components/shell/shell.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { VendorsComponent } from './components/vendors/vendors.component';
import { VendorDetailComponent } from './components/vendor-detail/vendor-detail.component';
import { ProcurementComponent } from './components/procurement/procurement.component';
import { PurchaseOrdersComponent } from './components/purchase-orders/purchase-orders.component';
import { PerformanceComponent } from './components/performance/performance.component';
import { ReliabilityComponent } from './components/reliability/reliability.component';
import { ContractsComponent } from './components/contracts/contracts.component';
import { CommunicationComponent } from './components/communication/communication.component';
import { ReportsComponent } from './components/reports/reports.component';
import { NotificationsComponent } from './components/notifications/notifications.component';
import { UsersComponent } from './components/users/users.component';
import { AuditLogsComponent } from './components/audit-logs/audit-logs.component';
import { ProfileComponent } from './components/profile/profile.component';
import { ForgotPasswordComponent } from './components/forgot-password/forgot-password.component';
import { ResetPasswordComponent } from './components/reset-password/reset-password.component';

const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },
  { path: 'forgot-password', component: ForgotPasswordComponent },
  { path: 'reset-password', component: ResetPasswordComponent },
  {
    path: '',
    component: ShellComponent,
    canActivate: [AuthGuard],
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      { path: 'dashboard', component: DashboardComponent },
      { 
        path: 'vendors', 
        component: VendorsComponent,
        canActivate: [AuthGuard],
        data: { roles: ['Administrator', 'Procurement Manager', 'Supply Chain Manager', 'Auditor'] }
      },
      { path: 'vendors/:id', component: VendorDetailComponent },
      { 
        path: 'procurement', 
        component: ProcurementComponent,
        canActivate: [AuthGuard],
        data: { roles: ['Administrator', 'Procurement Manager', 'Supply Chain Manager', 'Finance Officer', 'Auditor'] }
      },
      { path: 'purchase-orders', component: PurchaseOrdersComponent },
      { 
        path: 'performance', 
        component: PerformanceComponent,
        canActivate: [AuthGuard],
        data: { roles: ['Administrator', 'Procurement Manager', 'Supply Chain Manager', 'Auditor'] }
      },
      { 
        path: 'reliability', 
        component: ReliabilityComponent,
        canActivate: [AuthGuard],
        data: { roles: ['Administrator', 'Procurement Manager', 'Supply Chain Manager', 'Auditor'] }
      },
      { path: 'contracts', component: ContractsComponent },
      { path: 'communication', component: CommunicationComponent },
      { 
        path: 'reports', 
        component: ReportsComponent,
        canActivate: [AuthGuard],
        data: { roles: ['Administrator', 'Procurement Manager', 'Supply Chain Manager', 'Finance Officer', 'Auditor'] }
      },
      { path: 'notifications', component: NotificationsComponent },
      { 
        path: 'users', 
        component: UsersComponent,
        canActivate: [AuthGuard],
        data: { roles: ['Administrator'] }
      },
      { 
        path: 'audit-logs', 
        component: AuditLogsComponent,
        canActivate: [AuthGuard],
        data: { roles: ['Administrator', 'Auditor'] }
      },
      { path: 'profile', component: ProfileComponent }
    ]
  },
  { path: '**', redirectTo: 'dashboard' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
