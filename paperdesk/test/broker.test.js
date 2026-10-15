import test from 'node:test';
import assert from 'node:assert/strict';
import { simulateBuy, riskDecision, simulateSell } from '../src/broker.js';

const config = {
  paper: {
    maxOpenPositions: 5,
    feeBps: 30,
    baseSlippageBps: 25,
    maxSlippageBps: 500,
    stopLossPct: 0.15,
    takeProfitPct: 0.30,
    maxHoldMinutes: 180
  }
};

const pool = {
  poolAddress: 'pool1',
  baseToken: { address: 'token1', symbol: 'TEST' },
  priceUsd: 1,
  liquidityUsd: 100000
};

test('paper buy never exceeds cash and creates a position', () => {
  const state = { cashUsd: 1000, positions: [], trades: [], realizedPnlUsd: 0 };
  const p = simulateBuy(state, pool, 20, config, new Date('2026-01-01T00:00:00Z'));
  assert.equal(state.positions.length, 1);
  assert.equal(state.cashUsd, 980);
  assert.equal(p.costUsd, 20);
  assert.ok(p.entryPriceUsd > 1);
});

test('risk exits at stop loss', () => {
  const position = { entryPriceUsd: 1, openedAt: '2026-01-01T00:00:00Z' };
  const d = riskDecision(position, 0.84, config, new Date('2026-01-01T00:05:00Z'));
  assert.equal(d.action, 'EXIT');
  assert.equal(d.reason, 'stop_loss');
});

test('risk exits at take profit', () => {
  const position = { entryPriceUsd: 1, openedAt: '2026-01-01T00:00:00Z' };
  const d = riskDecision(position, 1.31, config, new Date('2026-01-01T00:05:00Z'));
  assert.equal(d.action, 'EXIT');
  assert.equal(d.reason, 'take_profit');
});

test('paper sell realizes pnl', () => {
  const state = { cashUsd: 1000, positions: [], trades: [], realizedPnlUsd: 0 };
  const p = simulateBuy(state, pool, 20, config, new Date('2026-01-01T00:00:00Z'));
  const trade = simulateSell(state, p.id, 1.5, config, 'test', new Date('2026-01-01T00:10:00Z'));
  assert.equal(state.positions.length, 0);
  assert.ok(trade.pnlUsd > 0);
  assert.ok(state.realizedPnlUsd > 0);
});
