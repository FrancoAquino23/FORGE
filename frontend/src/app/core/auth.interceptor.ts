/* ==================================================================
   FORGE - (AUTH INTERCEPTOR)
   ================================================================== */

import { HttpInterceptorFn } from '@angular/common/http';

// Interceptor (Authentication - Add Bearer Token to Requests)
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = localStorage.getItem('forge_token');
  if (token) {
    req = req.clone({ setHeaders: { Authorization: `Bearer ${token}` } });
  }
  return next(req);
};
