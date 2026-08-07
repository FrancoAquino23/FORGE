/* ==================================================================
   SETTINGS PANEL COMPONENT
   ================================================================== */

import {
  Component,
  DestroyRef,
  EventEmitter,
  HostListener,
  Input,
  OnChanges,
  Output,
  SimpleChanges,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { NgIconComponent, provideIcons } from '@ng-icons/core';
import {
  phosphorCheckBold,
  phosphorGearBold,
  phosphorLockKeyBold,
  phosphorPaletteBold,
  phosphorPlugsBold,
  phosphorSpinnerBold,
  phosphorTrashBold,
  phosphorUserBold,
  phosphorWarningBold,
  phosphorSwordBold,
  phosphorEyeBold,
  phosphorShieldBold,
  phosphorSketchLogoBold,
  phosphorDnaBold,
  phosphorLightningBold,
  phosphorSparkleBold,
  phosphorStarBold,
  phosphorFlaskBold,
  phosphorBrainBold,
  phosphorHeartBold,
  phosphorRocketBold,
  phosphorFireBold,
  phosphorCrownBold,
  phosphorGlobeBold,
  phosphorLeafBold,
  phosphorMoonBold,
  phosphorSunBold,
  phosphorAnchorBold,
  phosphorDiamondBold,
  phosphorHexagonBold,
  phosphorInfinityBold,
  phosphorSkullBold,
  phosphorCastleTurretBold,
  phosphorHorseBold,
  phosphorRadioactiveBold,
  phosphorRobotBold,
  phosphorPlanetBold,
  phosphorAlienBold,
  phosphorGhostBold,
  phosphorPizzaBold,
  phosphorCatBold,
  phosphorDogBold,
} from '@ng-icons/phosphor-icons/bold';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { PlayerStateService } from '../../core/player-state.service';
import { SoundService } from '../../core/sound.service';

// Available icons for avatar selection
export const AVATAR_ICONS: string[] = [
  'phosphorUserBold',
  'phosphorSwordBold',
  'phosphorDnaBold',
  'phosphorLightningBold',
  'phosphorSparkleBold',
  'phosphorFlaskBold',
  'phosphorHeartBold',
  'phosphorRocketBold',
  'phosphorCrownBold',
  'phosphorMoonBold',
  'phosphorAnchorBold',
  'phosphorInfinityBold',
  'phosphorSkullBold',
  'phosphorCastleTurretBold',
  'phosphorHorseBold',
  'phosphorRadioactiveBold',
  'phosphorRobotBold',
  'phosphorPlanetBold',
  'phosphorAlienBold',
  'phosphorGhostBold',
  'phosphorPizzaBold',
  'phosphorCatBold',
  'phosphorDogBold',
];

// Available colors for avatar background
export const AVATAR_COLORS: string[] = [
  '#f87171',
  '#fb923c',
  '#fbbf24',
  '#facc15',
  '#4ade80',
  '#34d399',
  '#22d3ee',
  '#60a5fa',
  '#818cf8',
  '#c084fc',
  '#f472b6',
  '#94a3b8',
  '#475569',
  '#1e293b',
  '#f8fafc',
];

@Component({
  selector: 'app-settings-panel',
  standalone: true,
  imports: [NgIconComponent, FormsModule],
  viewProviders: [
    provideIcons({
      phosphorCheckBold,
      phosphorGearBold,
      phosphorLockKeyBold,
      phosphorPaletteBold,
      phosphorPlugsBold,
      phosphorSpinnerBold,
      phosphorTrashBold,
      phosphorUserBold,
      phosphorWarningBold,
      phosphorSwordBold,
      phosphorEyeBold,
      phosphorShieldBold,
      phosphorSketchLogoBold,
      phosphorDnaBold,
      phosphorLightningBold,
      phosphorSparkleBold,
      phosphorStarBold,
      phosphorFlaskBold,
      phosphorBrainBold,
      phosphorHeartBold,
      phosphorRocketBold,
      phosphorFireBold,
      phosphorCrownBold,
      phosphorGlobeBold,
      phosphorLeafBold,
      phosphorMoonBold,
      phosphorSunBold,
      phosphorAnchorBold,
      phosphorDiamondBold,
      phosphorHexagonBold,
      phosphorInfinityBold,
      phosphorSkullBold,
      phosphorCastleTurretBold,
      phosphorHorseBold,
      phosphorRadioactiveBold,
      phosphorRobotBold,
      phosphorPlanetBold,
      phosphorAlienBold,
      phosphorGhostBold,
      phosphorPizzaBold,
      phosphorCatBold,
      phosphorDogBold,
    }),
  ],
  templateUrl: './settings-panel.component.html',
})
export class SettingsPanelComponent implements OnChanges {
  private api = inject(ApiService);
  private auth = inject(AuthService);
  private destroyRef = inject(DestroyRef);
  private playerState = inject(PlayerStateService);
  protected sound = inject(SoundService);

  @Input() open = false;
  @Output() closed = new EventEmitter<void>();
  @Output() profileChanged = new EventEmitter<void>();

  protected readonly profile = this.playerState.profile;

  readonly AVATAR_ICONS = AVATAR_ICONS;
  readonly AVATAR_COLORS = AVATAR_COLORS;

  // Account section
  newUsername = signal('');
  usernamePassword = signal('');
  usernameSaving = signal(false);
  usernameError = signal('');

  currentPassword = signal('');
  newPassword = signal('');
  passwordSaving = signal(false);
  passwordError = signal('');
  passwordSuccess = signal(false);

  // Avatar section
  selectedColor = signal<string | null>(null);
  selectedIcon = signal<string | null>(null);
  avatarSaving = signal(false);

  // Danger zone
  confirmingDelete = signal(false);
  deletePassword = signal('');
  deleteError = signal('');
  deleting = signal(false);

  // Sound section
  ngOnChanges(changes: SimpleChanges): void {
    if (changes['open']?.currentValue === true) {
      this.resetForms();
      const p = this.playerState.profile();
      if (p) {
        this.selectedColor.set(p.avatar_color);
        this.selectedIcon.set(p.avatar_icon);
      }
    }
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    if (this.open) this.close();
  }

  // Close panel
  close(): void {
    this.closed.emit();
  }

  // Username update
  saveUsername(): void {
    if (!this.newUsername().trim() || !this.usernamePassword() || this.usernameSaving()) return;
    this.usernameSaving.set(true);
    this.usernameError.set('');
    this.api
      .updateUsername(this.newUsername().trim(), this.usernamePassword())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.newUsername.set('');
          this.usernamePassword.set('');
          this.usernameSaving.set(false);
          this.playerState.loadProfile();
        },
        error: (err) => {
          this.usernameError.set(
            err.status === 409 ? 'Username already taken.' : 'Incorrect password.',
          );
          this.usernameSaving.set(false);
        },
      });
  }

  // Password update
  savePassword(): void {
    if (!this.currentPassword() || !this.newPassword() || this.passwordSaving()) return;
    this.passwordSaving.set(true);
    this.passwordError.set('');
    this.passwordSuccess.set(false);
    this.api
      .updatePassword(this.currentPassword(), this.newPassword())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.passwordSuccess.set(true);
          this.currentPassword.set('');
          this.newPassword.set('');
          this.passwordSaving.set(false);
        },
        error: () => {
          this.passwordError.set('Incorrect current password.');
          this.passwordSaving.set(false);
        },
      });
  }

  // Avatar update
  saveAvatar(): void {
    if (this.avatarSaving()) return;
    this.avatarSaving.set(true);
    this.api
      .updateAvatar(this.selectedColor(), this.selectedIcon())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.avatarSaving.set(false);
          this.playerState.loadProfile();
        },
        error: () => {
          this.avatarSaving.set(false);
        },
      });
  }

  // Delete account
  requestDelete(): void {
    this.confirmingDelete.set(true);
  }

  // Cancel delete account
  cancelDelete(): void {
    this.confirmingDelete.set(false);
    this.deletePassword.set('');
    this.deleteError.set('');
  }

  // Confirm delete account
  confirmDelete(): void {
    if (!this.deletePassword() || this.deleting()) return;
    this.deleting.set(true);
    this.deleteError.set('');
    this.api
      .deleteAccount(this.deletePassword())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.auth.logout();
        },
        error: () => {
          this.deleteError.set('Incorrect password. Please try again.');
          this.deleting.set(false);
        },
      });
  }

  private resetForms(): void {
    this.newUsername.set('');
    this.usernamePassword.set('');
    this.usernameError.set('');
    this.currentPassword.set('');
    this.newPassword.set('');
    this.passwordError.set('');
    this.confirmingDelete.set(false);
    this.deletePassword.set('');
    this.deleteError.set('');
  }
}
