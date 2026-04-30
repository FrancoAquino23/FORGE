/* ==================================================================
   FORGE (APPLICATION CONFIGURATION)
   ================================================================== */

import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { LUCIDE_ICONS, LucideIconProvider, Hammer, Eye, Shield, Gem, Cpu, Zap, Sparkles } from 'lucide-angular';
import { routes } from './app.routes';
import { authInterceptor } from './core/auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor])),
    {
      provide: LUCIDE_ICONS,
      useValue: new LucideIconProvider({ Hammer, Eye, Shield, Gem, Cpu, Zap, Sparkles }),
      multi: true,
    },
  ],
};
