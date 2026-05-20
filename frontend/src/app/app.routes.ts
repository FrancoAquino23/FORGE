/* ==================================================================
   FORGE (APPLICATION CONFIGURATION)
   ================================================================== */

import { inject } from '@angular/core';
import { Router, Routes } from '@angular/router';
import { AuthService } from './core/auth.service';

// Route guard to protect authenticated routes
const authGuard = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  return auth.isLoggedIn() ? true : router.parseUrl('/login');
};

// Application routes
export const routes: Routes = [
  // Default route redirects to dashboard
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  {
    // Login route (public)
    path: 'login',
    loadComponent: () => import('./features/login/login.component').then((m) => m.LoginComponent),
  },
  {
    // Register route (public)
    path: 'register',
    loadComponent: () =>
      import('./features/register/register.component').then((m) => m.RegisterComponent),
  },
  {
    // Dashboard route (protected)
    path: 'dashboard',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
  },
  {
    // Missions route (protected)
    path: 'missions',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/missions/missions.component').then((m) => m.MissionsComponent),
  },
  {
    // Prestige route (protected)
    path: 'prestige',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/prestige/prestige.component').then((m) => m.PrestigeComponent),
  },
  {
    // Forge route (protected)
    path: 'forge',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/forge/forge.component').then((m) => m.ForgeComponent),
  },
  {
    // Skill Tree route (protected)
    path: 'skill-tree',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/skill-tree/skill-tree.component').then((m) => m.SkillTreeComponent),
  },
  // Fallback route for undefined paths
  { path: '**', redirectTo: 'dashboard' },
];
