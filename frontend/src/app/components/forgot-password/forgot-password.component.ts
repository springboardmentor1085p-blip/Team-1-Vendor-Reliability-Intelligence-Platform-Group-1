import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-forgot-password',
  templateUrl: './forgot-password.component.html',
  styleUrls: ['./forgot-password.component.css']
})
export class ForgotPasswordComponent implements OnInit {
  forgotForm!: FormGroup;
  loading = false;
  message = '';
  error = '';

  constructor(
    private formBuilder: FormBuilder,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.forgotForm = this.formBuilder.group({
      email: ['', [Validators.required, Validators.email]]
    });
  }

  onSubmit(): void {
    if (this.forgotForm.invalid) {
      return;
    }

    this.loading = true;
    this.message = '';
    this.error = '';

    this.authService.forgotPassword(this.forgotForm.value.email).subscribe({
      next: res => {
        this.loading = false;
        this.message = res.message || 'If this email is registered, a password reset link has been generated.';
      },
      error: err => {
        this.loading = false;
        this.error = err.error?.detail || 'An error occurred. Please try again.';
      }
    });
  }
}
