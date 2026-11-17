import { useState } from 'react';
import { ArrowUpRight, CircuitBoard, Gauge, Layers3, Radio, ScanLine, X } from 'lucide-react';
import type { Reading, Run, Tool } from './api';
import { decisionNames } from './api';

function recipeLabel(recipe: Tool['recipe']) {
  if (!recipe) return 'Recipe available in source metadata';
  return Object.entries(recipe).slice(0, 3).map(([key, value]) => key + ' ' + String(value)).join(' · ');
}

export function MachineStage({ run, latest, tool, remainingBudget }: {
  run: Run | null; latest: Reading | null; tool?: Tool; remainingBudget: number;
}) {
  const [open, setOpen] = useState(true);
  const risk = latest?.decision?.risk;
  const running = run?.state === 'running';

  return <section className="machine-stage" aria-label="Haas VF-1 digital representation">
    <div className="stage-grid" />
    <div className="stage-caption">
      <span className="eyebrow"><span className="small-dot" /> CNC TESTBED</span>
      <h2>Haas VF-1</h2>
      <p>42CrMo4 steel · End milling</p>
    </div>
    <div className="machine-illustration" aria-hidden="true">
      <svg viewBox="0 0 800 510" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="front" x1="0" y1="0" x2="1" y2="1"><stop stopColor="var(--machine-front-a)" /><stop offset="1" stopColor="var(--machine-front-b)" /></linearGradient>
          <linearGradient id="window" x1="0" y1="0" x2="1" y2="1"><stop stopColor="var(--machine-window-a)" /><stop offset="1" stopColor="var(--machine-window-b)" /></linearGradient>
          <linearGradient id="metal" x1="0" y1="0" x2="1" y2="0"><stop stopColor="#666a6a" /><stop offset=".5" stopColor="#b4b7b2" /><stop offset="1" stopColor="#5c6262" /></linearGradient>
          <filter id="shadow"><feGaussianBlur stdDeviation="11" /></filter>
          <pattern id="hatch" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="skewY(22)"><path d="M0 0V10" stroke="var(--machine-line)" strokeWidth="1" /></pattern>
        </defs>
        <ellipse cx="411" cy="434" rx="228" ry="37" fill="var(--machine-shadow)" filter="url(#shadow)" />
        <path d="M192 385 472 277 657 366 375 481Z" fill="var(--machine-platform)" stroke="var(--machine-line)" />
        <path d="M192 385 375 472 375 481 192 395Z" fill="var(--machine-side)" />
        <path d="M375 472 657 366 657 376 375 481Z" fill="var(--machine-front-b)" />
        <path d="M245 156 459 74 607 143 392 225Z" fill="var(--machine-top)" stroke="var(--machine-line)" />
        <path d="M459 74 607 143 607 361 459 291Z" fill="var(--machine-side)" stroke="var(--machine-line)" />
        <path d="M245 156 392 225 607 143 607 361 392 444 245 374Z" fill="url(#front)" stroke="var(--machine-line)" />
        <path d="M245 156 392 225 392 444 245 374Z" fill="var(--machine-left)" stroke="var(--machine-line)" />
        <path d="M267 188 369 236 369 387 267 338Z" fill="url(#window)" stroke="var(--machine-window-border)" strokeWidth="4" />
        <path d="M286 311 341 286 364 298 310 323Z" fill="var(--machine-bed)" />
        <path d="M286 311 310 323 310 341 286 330Z" fill="#757d79" />
        <path d="M310 323 364 298 364 317 310 341Z" fill="#89928b" />
        <path d="M318 218 337 228 337 281 318 272Z" fill="url(#metal)" />
        <path d="M322 274 333 279 333 294 328 299 322 289Z" fill="#ea7447" />
        <path d="M273 200 279 204 279 328 273 325Z" fill="var(--machine-glint)" />
        <path d="M403 242 574 177 574 351 403 417Z" fill="url(#window)" stroke="var(--machine-window-border)" strokeWidth="4" />
        <path d="M411 254 562 197 562 340 411 397Z" fill="url(#hatch)" opacity=".45" />
        <path d="M426 338 525 300 558 316 459 354Z" fill="var(--machine-bed)" />
        <path d="M459 354 558 316 558 331 459 370Z" fill="#7d8781" />
        <path d="M426 338 459 354 459 370 426 353Z" fill="#66726a" />
        <path d="M465 228 486 220 486 291 465 299Z" fill="url(#metal)" />
        <path d="M471 294 480 291 480 314 475 322 471 317Z" fill="#f08450" />
        <path d="M493 213 502 209 502 370 493 373Z" fill="var(--machine-glint)" opacity=".65" />
        <path d="M591 205 642 186 642 275 591 294Z" fill="var(--machine-control)" stroke="var(--machine-line)" strokeWidth="2" />
        <path d="M599 215 634 202 634 242 599 256Z" fill="#24362f" />
        <path d="M605 229 614 225M605 236 626 228M605 243 620 237" stroke="#91bca6" strokeWidth="2" />
        <path d="M602 267 606 265M613 263 617 261M624 259 628 257M602 276 606 274M613 272 617 270M624 268 628 266" stroke="var(--machine-window-border)" strokeWidth="3" />
        <circle cx="637" cy="277" r="4" fill="#df704f" />
        <path d="M282 353 357 390" stroke="var(--machine-line)" />
        <path d="M411 427 578 364" stroke="var(--machine-line)" />
        <path d="M270 180 370 227" stroke="#e07854" strokeWidth="3" />
        <path d="M410 230 575 167" stroke="#e07854" strokeWidth="3" />
        <path d="M464 86 592 146" stroke="var(--machine-glint)" opacity=".8" />
        <path d="M261 162 456 87" stroke="var(--machine-glint)" />
        <text x="289" y="173" fill="var(--machine-wordmark)" fontSize="16" fontFamily="Inter, sans-serif" fontWeight="700" transform="rotate(25 289 173)">HAAS</text>
        <path d="M296 414 278 405 278 418 296 427ZM548 393 567 386 567 400 548 408Z" fill="var(--machine-foot)" />
      </svg>
    </div>
    <button className={'machine-hotspot' + (running ? ' active' : '')} onClick={() => setOpen(!open)} aria-label={open ? 'Hide cutter details' : 'Show cutter details'} aria-expanded={open}><ScanLine size={17} /></button>
    {open && <div className="machine-hud">
      <div className="hud-top"><span><span className={'small-dot ' + (running ? 'green' : '')} /> {run ? 'Cutter ' + run.tool_id : 'Cutter detail'}</span><button className="tiny-icon" onClick={() => setOpen(false)} aria-label="Close cutter details"><X size={13} /></button></div>
      <div className="hud-number"><span>{latest ? String(latest.cycle).padStart(3, '0') : '—'}</span><small>completed cut</small></div>
      <div className="hud-divider" />
      <dl><div><dt><Gauge size={13} /> Benchmark risk</dt><dd>{typeof risk === 'number' ? Math.round(risk * 100) + '%' : 'Awaiting data'}</dd></div><div><dt><Layers3 size={13} /> Vibration allowance</dt><dd>{remainingBudget} available</dd></div></dl>
      <p>{recipeLabel(tool?.recipe)}</p>
    </div>}
    <div className="stage-bottom">
      <span><CircuitBoard size={14} /> {latest?.decision?.status ? decisionNames[latest.decision.status] : 'Ready for recorded telemetry'}</span>
      <span className="stage-provenance"><Radio size={12} /> 500 Hz current <ArrowUpRight size={12} /> 25 kHz vibration</span>
    </div>
  </section>;
}
