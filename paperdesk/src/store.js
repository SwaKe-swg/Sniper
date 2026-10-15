import fs from 'node:fs/promises';
import path from 'node:path';

const DATA_DIR = path.resolve('data');
const STATE_FILE = path.join(DATA_DIR, 'state.json');

export async function loadState(startingBalanceUsd = 1000) {
  await fs.mkdir(DATA_DIR, { recursive: true });
  try {
    const raw = await fs.readFile(STATE_FILE, 'utf8');
    return JSON.parse(raw);
  } catch {
    return {
      cashUsd: startingBalanceUsd,
      equityUsd: startingBalanceUsd,
      realizedPnlUsd: 0,
      maxEquityUsd: startingBalanceUsd,
      maxDrawdownPct: 0,
      positions: [],
      trades: [],
      decisions: []
    };
  }
}

export async function saveState(state) {
  await fs.mkdir(DATA_DIR, { recursive: true });
  await fs.writeFile(STATE_FILE, JSON.stringify(state, null, 2));
}

export function recomputeEquity(state) {
  const unrealized = state.positions.reduce((sum, p) => sum + (p.unrealizedPnlUsd ?? 0), 0);
  state.equityUsd = state.cashUsd + state.positions.reduce((sum, p) => sum + p.costUsd, 0) + unrealized;
  state.maxEquityUsd = Math.max(state.maxEquityUsd ?? state.equityUsd, state.equityUsd);
  if (state.maxEquityUsd > 0) {
    const dd = (state.maxEquityUsd - state.equityUsd) / state.maxEquityUsd;
    state.maxDrawdownPct = Math.max(state.maxDrawdownPct ?? 0, dd);
  }
  return state;
}
