import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';

// Routing
import { AppRoutingModule } from './app-routing.module';

// Interceptors
import { JwtInterceptor } from './interceptors/jwt.interceptor';

// Components
import { AppComponent } from './app.component';
import { LoginComponent } from './components/login/login.component';
import { RegisterComponent } from './components/register/register.component';
import { ForgotPasswordComponent } from './components/forgot-password/forgot-password.component';
import { ResetPasswordComponent } from './components/reset-password/reset-password.component';
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

@NgModule({
  declarations: [
    AppComponent,
    LoginComponent,
    RegisterComponent,
    ForgotPasswordComponent,
    ResetPasswordComponent,
    ShellComponent,
    DashboardComponent,
    VendorsComponent,
    VendorDetailComponent,
    ProcurementComponent,
    PurchaseOrdersComponent,
    PerformanceComponent,
    ReliabilityComponent,
    ContractsComponent,
    CommunicationComponent,
    ReportsComponent,
    NotificationsComponent,
    UsersComponent,
    AuditLogsComponent,
    ProfileComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule,
    FormsModule,
    ReactiveFormsModule,
    BrowserAnimationsModule
  ],
  providers: [
    { provide: HTTP_INTERCEPTORS, useClass: JwtInterceptor, multi: true }
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
