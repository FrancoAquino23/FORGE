/* ==================================================================
   FORGE - (AUTH SERVICE)
   ================================================================== */

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { tap } from 'rxjs';

// Interface for the token response from the backend
interface TokenResponse {
  access_token: string;
  token_type: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly BASE = 'http://localhost:8000';
  private http = inject(HttpClient);
  private router = inject(Router);

  // Method (Login - Get Token from API and Store in Local Storage)
  login(email: string, password: string) {
    const body = new URLSearchParams({ username: email, password });
    return this.http
      .post<TokenResponse>(`${this.BASE}/auth/login`, body.toString(), {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      .pipe(tap((res) => localStorage.setItem('forge_token', res.access_token)));
  }

  // Method (Register - Get Token from API and Store in Local Storage)
  register(username: string, email: string, password: string) {
    return this.http
      .post<TokenResponse>(`${this.BASE}/auth/register`, { username, email, password })
      .pipe(tap((res) => localStorage.setItem('forge_token', res.access_token)));
  }

  // Method (Logout - Remove Token from Local Storage and Redirect to Login)
  logout(): void {
    localStorage.removeItem('forge_token');
    this.router.navigate(['/login']);
  }

  // Method (Check if User is Authenticated - Check for Token in Local Storage)
  isLoggedIn(): boolean {
    return !!localStorage.getItem('forge_token');
  }
}
