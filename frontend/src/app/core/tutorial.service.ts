/* ==================================================================
   FORGE - (TUTORIAL SERVICE)
   ================================================================== */

import { Injectable, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { driver, DriveStep } from 'driver.js';

export type TutorialId = 'general' | 'dashboard' | 'missions' | 'forge' | 'prestige' | 'skill-tree';

const STEPS: Record<TutorialId, DriveStep[]> = {
  /* ===== GENERAL OVERVIEW ===== */
  general: [
    {
      popover: {
        title: 'Welcome to THE FORGE',
        description:
          "This is your personal productivity engine. Everything here runs on a single loop. Let's walk through it.",
        align: 'center',
      },
    },
    {
      element: 'nav a.forge-nav-link[routerlink="/dashboard"]',
      popover: {
        title: 'Dashboard',
        description: 'Your command center. Tracks your attributes level & missions performance.',
      },
    },
    {
      element: 'nav a.forge-nav-link[routerlink="/missions"]',
      popover: {
        title: 'Missions',
        description: 'Your mission board. Deploy tasks, track progress & collect rewards.',
      },
    },
    {
      element: 'nav a.forge-nav-link[routerlink="/forge"]',
      popover: {
        title: 'Forge',
        description:
          'Your experimental lab. Transform raw materials into Stardust to upgrade Relics.',
      },
    },
    {
      element: 'nav a.forge-nav-link[routerlink="/prestige"]',
      popover: {
        title: 'Prestige',
        description:
          'Your ascension panel. Reset attributes for Prestige Points & permanent power.',
      },
    },
    {
      element: 'nav a.forge-nav-link[routerlink="/skill-tree"]',
      popover: {
        title: 'Perks',
        description:
          'Your skill tree. Spend Prestige Points on permanent buffs across exclusive paths.',
      },
    },
    {
      element: 'nav button.forge-nav-link',
      popover: {
        title: 'Profile',
        description: 'Your identity card. Username, prestige count, lifetime stats & achievements.',
        side: 'bottom',
      },
    },
    {
      element: '.dashboard-special-grid',
      popover: {
        title: 'S.P.E.C.I.A.L.',
        description:
          'Level up your attributes by completing missions aligned with each area of your life.',
        side: 'bottom',
      },
    },
    {
      popover: {
        title: 'The Loop',
        description:
          'Mission <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" fill="currentColor" style="width:10px;height:10px;display:inline-block;vertical-align:middle"><path d="M144.49,136.49l-80,80a12,12,0,0,1-17-17L119,128,47.51,56.49a12,12,0,0,1,17-17l80,80A12,12,0,0,1,144.49,136.49Zm80-17-80-80a12,12,0,1,0-17,17L199,128l-71.52,71.51a12,12,0,0,0,17,17l80-80A12,12,0,0,0,224.49,119.51Z"></path></svg> Rewards <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" fill="currentColor" style="width:10px;height:10px;display:inline-block;vertical-align:middle"><path d="M144.49,136.49l-80,80a12,12,0,0,1-17-17L119,128,47.51,56.49a12,12,0,0,1,17-17l80,80A12,12,0,0,1,144.49,136.49Zm80-17-80-80a12,12,0,1,0-17,17L199,128l-71.52,71.51a12,12,0,0,0,17,17l80-80A12,12,0,0,0,224.49,119.51Z"></path></svg> Level Up Attributes <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" fill="currentColor" style="width:10px;height:10px;display:inline-block;vertical-align:middle"><path d="M144.49,136.49l-80,80a12,12,0,0,1-17-17L119,128,47.51,56.49a12,12,0,0,1,17-17l80,80A12,12,0,0,1,144.49,136.49Zm80-17-80-80a12,12,0,1,0-17,17L199,128l-71.52,71.51a12,12,0,0,0,17,17l80-80A12,12,0,0,0,224.49,119.51Z"></path></svg> Upgrade Relics <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" fill="currentColor" style="width:10px;height:10px;display:inline-block;vertical-align:middle"><path d="M144.49,136.49l-80,80a12,12,0,0,1-17-17L119,128,47.51,56.49a12,12,0,0,1,17-17l80,80A12,12,0,0,1,144.49,136.49Zm80-17-80-80a12,12,0,1,0-17,17L199,128l-71.52,71.51a12,12,0,0,0,17,17l80-80A12,12,0,0,0,224.49,119.51Z"></path></svg> Prestige <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" fill="currentColor" style="width:10px;height:10px;display:inline-block;vertical-align:middle"><path d="M144.49,136.49l-80,80a12,12,0,0,1-17-17L119,128,47.51,56.49a12,12,0,0,1,17-17l80,80A12,12,0,0,1,144.49,136.49Zm80-17-80-80a12,12,0,1,0-17,17L199,128l-71.52,71.51a12,12,0,0,0,17,17l80-80A12,12,0,0,0,224.49,119.51Z"></path></svg> Repeat. That\'s it. Now go deploy your first mission.',
        align: 'center',
      },
    },
  ],

  /* ===== DASHBOARD TUTORIAL ===== */
  dashboard: [
    {
      popover: {
        title: 'Dashboard',
        description:
          'Your weekly performance report. Everything shown here reflects missions completed within the current week window.',
        align: 'center',
      },
    },
    {
      element: '.dashboard-week-nav',
      popover: {
        title: 'Week Navigation',
        description:
          'Browse previous weeks to review your historical performance. The label shows the exact date range being displayed.',
        side: 'bottom',
      },
    },
    {
      element: '.dashboard-category-breakdown',
      popover: {
        title: 'Mission Breakdown',
        description:
          'Total missions completed this week, split by category: Main Quest, Side Quest & Dailies.',
        side: 'top',
      },
    },
    {
      element: '.dashboard-threat-breakdown',
      popover: {
        title: 'Threat Distribution',
        description:
          "Shows the difficulty mix of your completed missions. A healthy spread means you're not just grinding easy tasks.",
        side: 'top',
      },
    },
    {
      element: '.dashboard-attribute-breakdown',
      popover: {
        title: 'Attribute Focus',
        description:
          "Which S.P.E.C.I.A.L. attributes you've been developing this week, ranked by mission count.",
        side: 'top',
      },
    },
    {
      element: '.dashboard-resolution-time',
      popover: {
        title: 'Average Resolution Time',
        description:
          'How long it takes to close missions on average, by category. Measured from deployment to claim.',
        side: 'top',
      },
    },
    {
      element: '.dashboard-active-missions',
      popover: {
        title: 'Active Missions',
        description:
          'Your most urgent open missions. Sorted by due date & threat level so the critical ones are always at the top.',
        side: 'left',
      },
    },
  ],

  /* ===== MISSIONS TUTORIAL ===== */
  missions: [
    {
      popover: {
        title: 'Missions',
        description:
          'Your active mission board. Three categories: Main Quest (big goals), Side Quest (secondary tasks) & Daily Grind (recurring habits). You can also stage missions as Drafts before starting the timer.',
        align: 'center',
      },
    },
    {
      element: '.missions-tab-bar',
      popover: {
        title: 'Tab Navigation',
        description:
          'Switch between your active missions by category, deploy new ones, review staged drafts or browse completed work.',
        side: 'bottom',
      },
    },
    {
      element: '[data-tab="NEW_MISSION"]',
      popover: {
        title: 'Deploy a Mission',
        description:
          'Create a new mission here. Pick an attribute, category, threat level & due date. Optionally add a description or checkpoints.',
        side: 'bottom',
      },
    },
    {
      element: '.missions-form-threat',
      popover: {
        title: 'Threat Level',
        description:
          '<strong>Minor</strong> = routine.<br><strong>Major</strong> = challenging.<br><strong>Critical</strong> = high-stakes.<br>Higher threat = more XP & materials on completion.',
        side: 'bottom',
      },
    },
    {
      element: '[data-tab="DRAFTS"]',
      popover: {
        title: 'Drafts',
        description:
          'Stage a Main Quest or Side Quest as a Draft to plan it without starting the timer. The resolution clock only starts when you activate it.',
        side: 'bottom',
      },
    },
    {
      popover: {
        title: 'Reading a Mission Card',
        description: "Let's walk through what each field on a mission card means.",
        align: 'center',
      },
    },
    {
      element: '.tutorial-mission-header',
      popover: {
        title: 'Objective & Identity',
        description:
          'The mission title at the top is what you committed to doing. Below it: the attribute it develops, the category it belongs to, and the threat level (difficulty).',
        side: 'bottom',
      },
    },
    {
      element: '.tutorial-mission-progress',
      popover: {
        title: 'Progress',
        description:
          'Tracks how close you are to completion. For manual missions it fills when all checkpoints are done. A full bar means the mission is ready to claim.',
        side: 'bottom',
      },
    },
    {
      element: '.tutorial-mission-rewards',
      popover: {
        title: 'Rewards',
        description:
          'XP for the linked attribute and raw material units earned on completion. Relics and skill nodes can increase both values.',
        side: 'top',
      },
    },
    {
      element: '.tutorial-mission-action',
      popover: {
        title: 'Due Date & Action',
        description:
          'The deadline keeps you accountable. The action button activates when all conditions are met click it to claim your rewards.',
        side: 'top',
      },
    },
    {
      popover: {
        title: 'Recurring Dailies',
        description:
          'Mark a mission as Favorite (<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" fill="currentColor" style="width:11px;height:11px;display:inline-block;vertical-align:middle"><path d="M234.29,114.85l-45,38.83L203,211.75a16.4,16.4,0,0,1-24.5,17.82L128,198.49,77.47,229.57A16.4,16.4,0,0,1,53,211.75l13.76-58.07-45-38.83A16.46,16.46,0,0,1,31.08,86l59-4.76,22.76-55.08a16.36,16.36,0,0,1,30.27,0l22.75,55.08,59,4.76a16.46,16.46,0,0,1,9.37,28.86Z"></path></svg>) to begin a streak. Missing a day breaks the streak. Consistency is rewarded.',
        align: 'center',
      },
    },
    {
      element: '[data-tab="HISTORY"]',
      popover: {
        title: 'Mission History',
        description:
          'A full log of every completed mission with date, attribute, category, threat level & rewards earned.',
        side: 'bottom',
      },
    },
  ],

  /* ===== FORGE TUTORIAL ===== */
  forge: [
    {
      popover: {
        title: 'The Forge',
        description:
          'Raw materials earned from missions have two uses: upgrade your relics or transmute them into Stardust. Manage them wisely.',
        align: 'center',
      },
    },
    {
      element: '.forge-material-grid',
      popover: {
        title: 'Material Balances',
        description:
          'Each S.P.E.C.I.A.L. attribute produces its own raw material when you complete missions. Green means you have enough to transform while red means you need more.',
        side: 'right',
      },
    },
    {
      element: '.forge-stardust-balance',
      popover: {
        title: 'Stardust Balance',
        description: 'Your current Stardust reserve. A key resource tied to your progression.',
        side: 'left',
      },
    },
    {
      element: '.forge-transmute-panel',
      popover: {
        title: 'Transmutation',
        description:
          'Select a batch size & convert your materials. Larger batches yield more. Once transformed, materials are consumed permanently.',
        side: 'left',
      },
    },
    {
      element: 'app-relic-workshop',
      popover: {
        title: 'Relic Workshop',
        description:
          'Relics are permanent artifacts tied to each S.P.E.C.I.A.L. attribute. Upgrading them amplifies the XP & materials rewarded.',
        side: 'top',
      },
    },
    {
      element: '.relic-card',
      popover: {
        title: 'Relic Card',
        description:
          "Shows the relic's current level, active bonus & upgrade cost in materials. Each level increases the bonus multiplier. Max level is 10.",
        side: 'bottom',
      },
    },
  ],

  /* ===== PRESTIGE TUTORIAL ===== */
  prestige: [
    {
      popover: {
        title: 'Prestige',
        description:
          'Once all 7 S.P.E.C.I.A.L. attributes reach the threshold, you can Prestige Up & obtain Prestige Points.',
        align: 'center',
      },
    },
    {
      element: '.prestige-honeycomb',
      popover: {
        title: 'Attribute Honeycomb',
        description:
          'Each hexagon represents one S.P.E.C.I.A.L. attribute. It lights up when that attribute reaches the required level. All 7 must be ready before you can ascend.',
        side: 'right',
      },
    },
    {
      element: '.prestige-material-reserves',
      popover: {
        title: 'Material Reserves',
        description:
          'Ascending also costs a fixed amount of each material. Make sure your reserves are stocked. Cost increases with each cycle.',
        side: 'left',
      },
    },
    {
      element: '.prestige-ascend-btn',
      popover: {
        title: 'Ascend',
        description:
          'When all attributes are ready & materials are sufficient, the Ascend button activates. <strong> Resetting all your progress</strong>.',
        side: 'top',
      },
    },
  ],

  /* ===== PERKS TUTORIAL ===== */
  'skill-tree': [
    {
      popover: {
        title: 'Perk Tree',
        description:
          'Each prestige earns you Prestige Points to spend here. All paths lock out alternatives. Choose carefully.',
        align: 'center',
      },
    },
    {
      element: '.skill-tree-pp-display',
      popover: {
        title: 'Prestige Points',
        description:
          'Your available Prestige Points. Earned each prestige cycle.Points are fully refunded on your next ascension.',
        side: 'left',
      },
    },
    {
      element: '.skill-tree-path-tabs',
      popover: {
        title: 'Paths',
        description:
          'Perks are organized into paths. Each path has exclusive options. Once chosen, the alternative is locked until you reset the tree.',
        side: 'top',
      },
    },
    {
      element: '.node-detail-panel',
      popover: {
        title: 'Perk Nodes',
        description:
          'Each node has a current level, max level & cost to upgrade. Hover a node to see its description & bonuses.',
        side: 'left',
      },
    },
    {
      element: '.skill-tree-reset-btn',
      popover: {
        title: 'Reset Tree',
        description:
          'Refunds all spent Prestige Points & clears your perk selections. Use this to reallocate your build.',
        side: 'bottom',
      },
    },
  ],
};

@Injectable({ providedIn: 'root' })
export class TutorialService {
  private router = inject(Router);

  readonly showDemoMission = signal(false);

  private _driver = driver({
    animate: true,
    smoothScroll: true,
    overlayColor: 'rgba(0,0,0,0.72)',
    stagePadding: 8,
    stageRadius: 6,
    popoverClass: 'forge-driver-popover',
    nextBtnText:
      'Next <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" fill="currentColor" style="width:14px;height:14px;display:inline-block;vertical-align:middle;margin-left:4px"><path d="M128,20A108,108,0,1,0,236,128,108.12,108.12,0,0,0,128,20Zm0,192a84,84,0,1,1,84-84A84.09,84.09,0,0,1,128,212Zm32.49-92.49a12,12,0,0,1,0,17l-40,40a12,12,0,0,1-17-17L135,128,103.51,96.49a12,12,0,0,1,17-17Z"></path></svg>',
    prevBtnText:
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" fill="currentColor" style="width:14px;height:14px;display:inline-block;vertical-align:middle;margin-right:4px"><path d="M128,20A108,108,0,1,0,236,128,108.12,108.12,0,0,0,128,20Zm0,192a84,84,0,1,1,84-84A84.09,84.09,0,0,1,128,212ZM152.49,96.49,121,128l31.52,31.51a12,12,0,0,1-17,17l-40-40a12,12,0,0,1,0-17l40-40a12,12,0,0,1,17,17Z"></path></svg> Prev',
    doneBtnText:
      'Done <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" fill="currentColor" style="width:14px;height:14px;display:inline-block;vertical-align:middle;margin-left:4px"><path d="M128,20A108,108,0,1,0,236,128,108.12,108.12,0,0,0,128,20Zm0,192a84,84,0,1,1,84-84A84.09,84.09,0,0,1,128,212Zm32.49-92.49a12,12,0,0,1,0,17l-40,40a12,12,0,0,1-17-17L135,128,103.51,96.49a12,12,0,0,1,17-17Z"></path></svg>',
    progressText: '{{current}} / {{total}}',
    showProgress: true,
  });

  // Start a tutorial
  start(id: TutorialId): void {
    let steps = STEPS[id];
    if (!steps?.length) return;

    // Navigate to a specific route for each tutorial
    if (id === 'general') {
      steps = steps.map((step, i) => ({
        ...step,
        onHighlightStarted: () => {
          if (i === 7) this.router.navigate(['/dashboard']);
        },
      }));
    }

    if (id === 'dashboard') {
      this.router.navigate(['/dashboard']);
    }

    if (id === 'missions') {
      this.router.navigate(['/missions']);
      steps = steps.map((step, i) => ({
        ...step,
        onHighlightStarted: () => {
          if (i === 4) {
            const tab = document.querySelector<HTMLElement>('[data-tab="DRAFTS"]');
            tab?.click();
          }
          if (i === 5) {
            const tab = document.querySelector<HTMLElement>('[data-tab="MAIN_QUEST"]');
            tab?.click();
            setTimeout(() => this.showDemoMission.set(true), 50);
          }
          if (i === 10) {
            this.showDemoMission.set(false);
            const tab = document.querySelector<HTMLElement>('[data-tab="DAILY_GRIND"]');
            tab?.click();
          }
          if (i === 11) {
            const tab = document.querySelector<HTMLElement>('[data-tab="HISTORY"]');
            tab?.click();
          }
        },
        onDeselected: i === 11 ? () => this.showDemoMission.set(false) : undefined,
      }));
    }

    if (id === 'forge') {
      this.router.navigate(['/forge']);
    }

    if (id === 'prestige') {
      this.router.navigate(['/prestige']);
    }

    if (id === 'skill-tree') {
      this.router.navigate(['/skill-tree']);
    }

    this._driver.setSteps(steps);
    this._driver.drive(0);
  }

  // Destroy instance
  destroy(): void {
    this._driver.destroy();
  }
}
