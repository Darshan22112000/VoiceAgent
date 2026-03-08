// src/app/auth.interceptor.ts
import { HttpInterceptorFn } from '@angular/common/http';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  console.log('🍪 withCredentials set for:', req.url);
  return next(req.clone({ withCredentials: true }));  // ✅ applies to all requests
};