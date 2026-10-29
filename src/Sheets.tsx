import type { ReactNode } from 'react';
import { FONT_SIZE_RANGE, useSettings, type Theme } from './settings';

export function Sheet({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  return (
    <div className="sheet-backdrop" onClick={onClose}>
      <section className="sheet" role="dialog" aria-label={title} onClick={(event) => event.stopPropagation()}>
        <header className="sheet-header">
          <h2>{title}</h2>
          <button className="button subtle" onClick={onClose}>Done</button>
        </header>
        <div className="sheet-body">{children}</div>
      </section>
    </div>
  );
}

function Stepper({ value, min, max, step = 1, onChange, format }: {
  value: number;
  min: number;
  max: number;
  step?: number;
  onChange: (value: number) => void;
  format?: (value: number) => string;
}) {
  return (
    <div className="stepper">
      <button className="button step" disabled={value <= min} onClick={() => onChange(Math.max(min, value - step))} aria-label="Decrease">−</button>
      <span className="stepper-value">{format ? format(value) : value}</span>
      <button className="button step" disabled={value >= max} onClick={() => onChange(Math.min(max, value + step))} aria-label="Increase">+</button>
    </div>
  );
}

function Toggle({ checked, onChange }: { checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <button className={`toggle${checked ? ' on' : ''}`} role="switch" aria-checked={checked} onClick={() => onChange(!checked)}>
      <span className="toggle-knob" />
    </button>
  );
}

export function Segmented<T extends string>({ options, value, onChange }: {
  options: Array<[T, string]>;
  value: T;
  onChange: (value: T) => void;
}) {
  return (
    <div className="segmented">
      {options.map(([option, label]) => (
        <button key={option} className={value === option ? 'selected' : ''} onClick={() => onChange(option)}>
          {label}
        </button>
      ))}
    </div>
  );
}

const THEMES: Array<[Theme, string]> = [['system', 'System'], ['light', 'Light'], ['dark', 'Dark']];

export function SettingsSheet({ onClose }: { onClose: () => void }) {
  const [settings, update] = useSettings();
  return (
    <Sheet title="Settings" onClose={onClose}>
      <div className="setting">
        <span>Code size</span>
        <Stepper
          value={settings.fontSize}
          min={FONT_SIZE_RANGE.min}
          max={FONT_SIZE_RANGE.max}
          onChange={(fontSize) => update({ fontSize })}
          format={(size) => `${size}px`}
        />
      </div>
      <div className="setting">
        <span>Theme</span>
        <Segmented options={THEMES} value={settings.theme} onChange={(theme) => update({ theme })} />
      </div>
      <h3 className="setting-group">Drill</h3>
      <div className="setting">
        <span>Show signatures</span>
        <Toggle checked={settings.showSignature} onChange={(showSignature) => update({ showSignature })} />
      </div>
      <p className="setting-note">
        Gives a function's or class's header line before you recall the rest. Off: the cue only.
      </p>
      <div className="setting">
        <span>Reveal on the left</span>
        <Toggle checked={settings.swapZones} onChange={(swapZones) => update({ swapZones })} />
      </div>
    </Sheet>
  );
}
