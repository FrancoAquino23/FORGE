/* ==================================================================
   LOGIN COMPONENT LOGIC
   ================================================================== */

import { Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { NgIconComponent, provideIcons } from '@ng-icons/core';
import { phosphorRobot } from '@ng-icons/phosphor-icons/regular';
import { AuthService } from '../../core/auth.service';

// Main login component that handles user authentication
@Component({
  selector: 'app-login',
  imports: [FormsModule, RouterLink, NgIconComponent],
  viewProviders: [provideIcons({ phosphorRobot })],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
})
export class LoginComponent {
  private auth = inject(AuthService);
  private router = inject(Router);
  private destroyRef = inject(DestroyRef);

  email = signal('');
  password = signal('');
  loading = signal(false);
  error = signal('');

  // Function to handle login form submission
  submit(): void {
    if (!this.email() || !this.password()) return;
    this.loading.set(true);
    this.error.set('');

    this.auth
      .login(this.email(), this.password())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => this.router.navigate(['/dashboard']),
        error: (err) => {
          this.error.set(err.error?.detail ?? 'Invalid credentials');
          this.loading.set(false);
        },
      });
  }
}
