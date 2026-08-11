/* ==================================================================
   FORGE - (SOUND SERVICE)
   ================================================================== */

import { Injectable, signal } from '@angular/core';

const GD = 440;
const STORAGE_KEY = 'forge-sound';

@Injectable({ providedIn: 'root' })
export class SoundService {
  private ctx: AudioContext | null = null;

  readonly soundEnabled = signal<boolean>(localStorage.getItem(STORAGE_KEY) !== 'off');

  private queue: Array<() => Promise<void>> = [];
  private processing = false;

  // Toggle sound on/off
  toggleSound(): void {
    const next = !this.soundEnabled();
    this.soundEnabled.set(next);
    localStorage.setItem(STORAGE_KEY, next ? 'on' : 'off');
  }

  private async getCtx(): Promise<AudioContext> {
    if (!this.ctx) this.ctx = new AudioContext();
    if (this.ctx.state !== 'running') await this.ctx.resume();
    return this.ctx;
  }

  private enqueue(fn: () => Promise<void>): void {
    this.queue.push(fn);
    if (!this.processing) this.processQueue();
  }

  private async processQueue(): Promise<void> {
    this.processing = true;
    while (this.queue.length > 0) {
      const fn = this.queue.shift()!;
      await fn();
    }
    this.processing = false;
  }

  private wait(ms: number): Promise<void> {
    return new Promise(r => setTimeout(r, ms));
  }

  private note(
    a: AudioContext,
    freq: number,
    t: number,
    dur: number,
    vol: number,
    freqEnd?: number | null,
    wave: OscillatorType = 'square',
  ): void {
    const osc = a.createOscillator();
    const g = a.createGain();
    osc.type = wave;
    osc.frequency.setValueAtTime(freq, t);
    if (freqEnd != null) osc.frequency.linearRampToValueAtTime(freqEnd, t + dur);
    g.gain.setValueAtTime(0, t);
    g.gain.linearRampToValueAtTime(vol, t + 0.003);
    g.gain.exponentialRampToValueAtTime(0.001, t + dur);
    osc.connect(g);
    g.connect(a.destination);
    osc.start(t);
    osc.stop(t + dur + 0.05);
  }

  private noteV(
    a: AudioContext,
    freq: number,
    t: number,
    dur: number,
    vol: number,
    vibRate: number,
    vibDepth: number,
    freqEnd?: number | null,
    wave: OscillatorType = 'square',
  ): void {
    const osc = a.createOscillator();
    const g = a.createGain();
    const lfo = a.createOscillator();
    const lfoG = a.createGain();
    osc.type = wave;
    osc.frequency.setValueAtTime(freq, t);
    if (freqEnd != null) osc.frequency.linearRampToValueAtTime(freqEnd, t + dur);
    lfo.type = 'sine';
    lfo.frequency.setValueAtTime(vibRate, t);
    lfoG.gain.setValueAtTime(vibDepth, t);
    lfo.connect(lfoG);
    lfoG.connect(osc.frequency);
    g.gain.setValueAtTime(0, t);
    g.gain.linearRampToValueAtTime(vol, t + 0.003);
    g.gain.exponentialRampToValueAtTime(0.001, t + dur);
    osc.connect(g);
    g.connect(a.destination);
    lfo.start(t);
    lfo.stop(t + dur + 0.05);
    osc.start(t);
    osc.stop(t + dur + 0.05);
  }

  // Sound 1 — Mission action: deploy, activate, edit, delete, claim
  playMission(): void {
    if (!this.soundEnabled()) return;
    this.enqueue(async () => {
      const a = await this.getCtx();
      const t = a.currentTime;
      this.note(a, GD, t, 0.055, 0.27);
      this.note(a, GD * 2, t + 0.07, 0.12, 0.31);
      await this.wait(350);
    });
  }

  // Sound 2 — Streak unlocked: favorite toggle ON
  playStreak(): void {
    if (!this.soundEnabled()) return;
    this.enqueue(async () => {
      const a = await this.getCtx();
      const t = a.currentTime;
      this.note(a, GD * 1.0, t, 0.09, 0.24);
      this.note(a, GD * 1.75, t + 0.1, 0.09, 0.25);
      this.note(a, GD * 1.0, t + 0.2, 0.09, 0.24);
      this.note(a, GD * 1.75, t + 0.3, 0.13, 0.26);
      await this.wait(600);
    });
  }

  // Sound 3 — Path chosen: first node of a skill path unlocked
  playPath(): void {
    if (!this.soundEnabled()) return;
    this.enqueue(async () => {
      const a = await this.getCtx();
      const t = a.currentTime;
      this.note(a, GD, t, 0.14, 0.42, GD * 2);
      await this.wait(300);
    });
  }

  // Sound 4 — Perk reset: skill tree full reset
  playPerkReset(): void {
    if (!this.soundEnabled()) return;
    this.enqueue(async () => {
      const a = await this.getCtx();
      const t = a.currentTime;
      this.note(a, GD * 2, t, 0.22, 0.3, GD * 0.5);
      this.note(a, GD * 2.5, t + 0.02, 0.2, 0.18, GD * 0.6, 'triangle');
      this.note(a, GD * 1.75, t + 0.01, 0.18, 0.14, GD * 0.45, 'triangle');
      await this.wait(380);
    });
  }

  // Sound 5 — Upgrade: perk node, relic upgrade, level up
  playUpgrade(): void {
    if (!this.soundEnabled()) return;
    this.enqueue(async () => {
      const a = await this.getCtx();
      const t = a.currentTime;
      this.note(a, GD, t, 0.045, 0.27);
      this.note(a, GD * 1.25, t + 0.055, 0.045, 0.29);
      this.note(a, GD * 1.5, t + 0.11, 0.14, 0.33);
      await this.wait(400);
    });
  }

  // Sound 6 — Stardust: successful transmutation in the Forge
  playStardust(): void {
    if (!this.soundEnabled()) return;
    this.enqueue(async () => {
      const a = await this.getCtx();
      const t = a.currentTime;
      this.note(a, GD * 2.0, t, 0.05, 0.44, null, 'triangle');
      this.note(a, GD * 2.5, t + 0.05, 0.05, 0.44, null, 'triangle');
      this.note(a, GD * 3.0, t + 0.1, 0.05, 0.38, null, 'triangle');
      this.note(a, GD * 3.5, t + 0.15, 0.18, 0.22, null, 'triangle');
      this.note(a, GD * 5.0, t + 0.15, 0.14, 0.14, null, 'sine');
      await this.wait(500);
    });
  }

  // Sound 7 — Achievement: achievement unlocked
  playAchievement(): void {
    if (!this.soundEnabled()) return;
    this.enqueue(async () => {
      const a = await this.getCtx();
      const t = a.currentTime;
      this.note(a, GD * 0.75, t, 0.055, 0.24);
      this.note(a, GD, t + 0.065, 0.055, 0.26);
      this.note(a, GD * 1.25, t + 0.13, 0.055, 0.28);
      this.note(a, GD * 1.5, t + 0.185, 0.055, 0.3);
      this.noteV(a, GD * 2, t + 0.24, 0.7, 0.4, 13, 10, null, 'triangle');
      this.noteV(a, GD * 2 + 7, t + 0.24, 0.6, 0.2, 13, 10, null, 'triangle');
      this.note(a, GD * 3, t + 0.24, 0.45, 0.14, null, 'sine');
      await this.wait(1100);
    });
  }

  // Sound 8 — Prestige: prestige upgrade completed
  playPrestige(): void {
    if (!this.soundEnabled()) return;
    this.enqueue(async () => {
      const a = await this.getCtx();
      const t = a.currentTime;
      this.note(a, GD * 0.75, t, 0.05, 0.24);
      this.note(a, GD * 1.0, t + 0.06, 0.05, 0.26);
      this.note(a, GD * 1.25, t + 0.12, 0.05, 0.28);
      this.note(a, GD * 1.5, t + 0.18, 0.05, 0.3);
      this.note(a, GD * 2.0, t + 0.26, 0.09, 0.3);
      this.note(a, GD * 1.5, t + 0.36, 0.09, 0.28);
      this.note(a, GD * 2.0, t + 0.46, 0.09, 0.31);
      this.noteV(a, GD * 2.5, t + 0.58, 0.88, 0.26, 12, 9, null, 'triangle');
      this.noteV(a, GD * 2.5 + 5, t + 0.58, 0.78, 0.12, 12, 9, null, 'triangle');
      this.note(a, GD * 3.75, t + 0.58, 0.65, 0.09, null, 'sine');
      await this.wait(1650);
    });
  }

  // Sound 9 — Error: any failed action
  playError(): void {
    if (!this.soundEnabled()) return;
    this.enqueue(async () => {
      const a = await this.getCtx();
      const t = a.currentTime;
      this.note(a, 130, t, 0.16, 0.3, 130 * 0.88);
      this.note(a, 130 * 1.08, t, 0.16 * 0.7, 0.15, null, 'triangle');
      await this.wait(300);
    });
  }
}
