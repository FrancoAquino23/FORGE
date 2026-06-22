/* ==================================================================
   FORGE (APPLICATION COMPONENT)
   ================================================================== */

import { Component, inject, signal } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from './core/auth.service';
import { PlayerStateService } from './core/player-state.service';
import { ToastComponent } from './shared/toast/toast.component';
import { ProfileModalComponent } from './shared/profile-modal/profile-modal.component';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, ToastComponent, ProfileModalComponent],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  auth = inject(AuthService);
  playerState = inject(PlayerStateService);
  profileOpen = signal(false);
}
