/* ==================================================================
   FORGE (APPLICATION COMPONENT)
   ================================================================== */

import { Component, inject, signal } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { NgIconComponent, provideIcons } from '@ng-icons/core';
import { phosphorRobot } from '@ng-icons/phosphor-icons/regular';
import { phosphorQuestionBold } from '@ng-icons/phosphor-icons/bold';
import { AuthService } from './core/auth.service';
import { PlayerStateService } from './core/player-state.service';
import { UiStateService } from './core/ui-state.service';
import { ToastComponent } from './shared/toast/toast.component';
import { ProfileModalComponent } from './shared/profile-modal/profile-modal.component';
import { SettingsPanelComponent } from './shared/settings-panel/settings-panel.component';
import { TutorialModalComponent } from './shared/tutorial-modal/tutorial-modal.component';

@Component({
  selector: 'app-root',
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    ToastComponent,
    ProfileModalComponent,
    SettingsPanelComponent,
    TutorialModalComponent,
    NgIconComponent,
  ],
  viewProviders: [provideIcons({ phosphorRobot, phosphorQuestionBold })],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  auth = inject(AuthService);
  playerState = inject(PlayerStateService);
  uiState = inject(UiStateService);
  tutorialOpen = signal(false);

  // Close all modals and panels
  closeAll(): void {
    this.uiState.profileOpen.set(false);
    this.uiState.settingsOpen.set(false);
  }
}
