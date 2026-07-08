/* ==================================================================
   TUTORIAL COMPONENT LOGIC
   ================================================================== */

import { Component, EventEmitter, HostListener, Input, Output, inject } from '@angular/core';
import { NgIconComponent, provideIcons } from '@ng-icons/core';
import {
  phosphorQuestionBold,
  phosphorXCircleBold,
  phosphorChartBarBold,
  phosphorClipboardTextBold,
  phosphorFireBold,
  phosphorCrownSimpleBold,
  phosphorTreeStructureBold,
  phosphorNavigationArrowBold,
} from '@ng-icons/phosphor-icons/bold';
import { TutorialId, TutorialService } from '../../core/tutorial.service';
import { PlayerStateService } from '../../core/player-state.service';

// Tutorial card (data structure)
interface TutorialCard {
  id: TutorialId;
  title: string;
  description: string;
  icon: string;
}

// Constants for tutorial cards
const TUTORIALS: TutorialCard[] = [
  {
    id: 'general',
    title: 'General Overview',
    description: 'Attributes, missions, rewards & prestige.',
    icon: 'phosphorNavigationArrowBold',
  },
  {
    id: 'dashboard',
    title: 'Dashboard',
    description: 'S.P.E.C.I.A.L. report & activities panels.',
    icon: 'phosphorChartBarBold',
  },
  {
    id: 'missions',
    title: 'Missions',
    description: 'Deploy, manage, track & claim missions.',
    icon: 'phosphorClipboardTextBold',
  },
  {
    id: 'forge',
    title: 'Forge',
    description: 'Forge materials into stardust to upgrade relics.',
    icon: 'phosphorFireBold',
  },
  {
    id: 'prestige',
    title: 'Prestige',
    description: 'Ascend, reset & repeat.',
    icon: 'phosphorCrownSimpleBold',
  },
  {
    id: 'skill-tree',
    title: 'Perks',
    description: 'Spend prestige points on permanent buffs.',
    icon: 'phosphorTreeStructureBold',
  },
];

@Component({
  selector: 'app-tutorial-modal',
  standalone: true,
  imports: [NgIconComponent],
  viewProviders: [
    provideIcons({
      phosphorQuestionBold,
      phosphorXCircleBold,
      phosphorNavigationArrowBold,
      phosphorChartBarBold,
      phosphorClipboardTextBold,
      phosphorFireBold,
      phosphorCrownSimpleBold,
      phosphorTreeStructureBold,
    }),
  ],
  templateUrl: './tutorial-modal.component.html',
})
export class TutorialModalComponent {
  @Input() open = false;
  @Output() closed = new EventEmitter<void>();

  readonly tutorials = TUTORIALS;
  private tutorialService = inject(TutorialService);
  private playerState = inject(PlayerStateService);
  readonly prestigeCount = this.playerState.prestigeCount;

  // Close modal on escape key
  @HostListener('document:keydown.escape')
  onEscape(): void {
    if (this.open) this.close();
  }

  // Close modal on click outside
  close(): void {
    this.closed.emit();
  }

  // Launch tutorial and close modal
  launch(id: TutorialId): void {
    this.close();
    setTimeout(() => this.tutorialService.start(id), 150);
  }
}
