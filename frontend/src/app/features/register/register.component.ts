/* ==================================================================
   REGISTER COMPONENT LOGIC
   ================================================================== */

import { Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { NgIconComponent, provideIcons } from '@ng-icons/core';
import { phosphorRobot } from '@ng-icons/phosphor-icons/regular';
import { AuthService } from '../../core/auth.service';

// Main register component that handles user registration
@Component({
  selector: 'app-register',
  imports: [FormsModule, RouterLink, NgIconComponent],
  viewProviders: [provideIcons({ phosphorRobot })],
  templateUrl: './register.component.html',
  styleUrl: './register.component.scss',
})
export class RegisterComponent {
  private auth = inject(AuthService);
  private router = inject(Router);
  private destroyRef = inject(DestroyRef);

  username = signal('');
  email = signal('');
  password = signal('');
  loading = signal(false);
  error = signal('');

  // Function to handle register form submission
  submit(): void {
    const username = this.username().trim();
    const email = this.email().trim();
    const password = this.password().trim();
    if (!username || !email || !password) return;
    if (username.length < 3) { this.error.set('Username must be at least 3 characters'); return; }
    if (password.length < 8) { this.error.set('Password must be at least 8 characters'); return; }
    this.loading.set(true);
    this.error.set('');

    this.auth
      .register(username, email, password)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => this.router.navigate(['/dashboard']),
        error: (err) => {
          this.error.set(err.error?.detail ?? 'Could not create account');
          this.loading.set(false);
        },
      });
  }
}
