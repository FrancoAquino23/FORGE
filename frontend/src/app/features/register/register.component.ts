/* ==================================================================
   REGISTER COMPONENT LOGIC
   ================================================================== */

import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth.service';

// Main register component that handles user registration
@Component({
  selector: 'app-register',
  imports: [FormsModule, RouterLink],
  templateUrl: './register.component.html',
  styleUrl: './register.component.scss',
})
export class RegisterComponent {
  private auth = inject(AuthService);
  private router = inject(Router);

  username = '';
  email = '';
  password = '';
  loading = signal(false);
  error = signal('');

  // Function to handle register form submission
  submit(): void {
    if (!this.username || !this.email || !this.password) return;
    this.loading.set(true);
    this.error.set('');

    this.auth.register(this.username, this.email, this.password).subscribe({
      next: () => this.router.navigate(['/dashboard']),
      error: (err) => {
        this.error.set(err.error?.detail ?? 'No se pudo crear la cuenta');
        this.loading.set(false);
      },
    });
  }
}
