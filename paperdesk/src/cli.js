import fs from 'node:fs/promises';
import { discoverSolanaPools, fetchPool } from './market.js';
import { scan, vet, social, judge, pick, size } from './agents.js';
import { simulateBuy, markPosition, riskDecision, simulateSell } from './broker.js';
import { loadState, saveState, recomputeEquity } from './store.js';

const config = JSON.parse(await fs.readFile(new URL('../config.json', import.meta.url), 'utf8'));
const command = process.argv[2] ?? 'status';

async function evaluateCandidate(pool, state) {
  const scanResult = scan(pool, config);
  const vetResult = vet(pool);
  const socialResult = social(pool);
  const judgement = judge({ scanResult, vetResult, socialResult });
  const selection = pick(judgement);
  const sizing = size(state, config, pool);
  return { pool, scan: scanResult, vet: vetResult, social: socialResult, judge: judgement, pick: selection, size: sizing };
}

async function discoveryCycle(state, { allowEntries }) {
  const pools = await discoverSolanaPools(config.discovery);
  const seen = new Set();
  const evaluations = [];

  for (const pool of pools) {
    if (!pool.poolAddress || seen.has(pool.poolAddress)) continue;
    seen.add(pool.poolAddress);
    const result = await evaluateCandidate(pool, state);
    evaluations.push(result);
    state.decisions.push({ at: new Date().toISOString(), ...result });
    if (state.decisions.length > 1000) state.decisions.splice(0, state.decisions.length - 1000);

    const alreadyOpen = state.positions.some((p) => p.poolAddress === pool.poolAddress);
    if (allowEntries && config.paper.autoEnter && result.pick.action === 'BUY' && !alreadyOpen && result.size.usd > 0) {
      if (state.positions.length >= config.paper.maxOpenPositions) break;
      simulateBuy(state, pool, result.size.usd, config);
    }
  }
  return evaluations;
}

async function riskCycle(state) {
  for (const position of [...state.positions]) {
    try {
      const pool = await fetchPool(config.network, position.poolAddress, config.discovery.requestTimeoutMs);
      const price = pool.priceUsd;
      markPosition(position, price);
      const decision = riskDecision(position, price, config);
      state.decisions.push({ at: new Date().toISOString(), agent: 'RISK', positionId: position.id, symbol: position.symbol, ...decision });
      if (decision.action === 'EXIT') simulateSell(state, position.id, price, config, decision.reason);
    } catch (error) {
      state.decisions.push({ at: new Date().toISOString(), agent: 'RISK', positionId: position.id, action: 'HOLD', reason: `market_error:${error.message}` });
    }
  }
}

function stats(state) {
  const exits = state.trades.filter((t) => t.type === 'SELL');
  const wins = exits.filter((t) => t.pnlUsd > 0);
  const losses = exits.filter((t) => t.pnlUsd < 0);
  const grossProfit = wins.reduce((s, t) => s + t.pnlUsd, 0);
  const grossLoss = Math.abs(losses.reduce((s, t) => s + t.pnlUsd, 0));
  return {
    mode: config.mode.toUpperCase(),
    cashUsd: state.cashUsd,
    equityUsd: state.equityUsd,
    realizedPnlUsd: state.realizedPnlUsd,
    openPositions: state.positions.length,
    completedTrades: exits.length,
    wins: wins.length,
    losses: losses.length,
    winRatePct: exits.length ? (wins.length / exits.length) * 100 : 0,
    averageWinUsd: wins.length ? grossProfit / wins.length : 0,
    averageLossUsd: losses.length ? -grossLoss / losses.length : 0,
    profitFactor: grossLoss > 0 ? grossProfit / grossLoss : null,
    maxDrawdownPct: (state.maxDrawdownPct ?? 0) * 100
  };
}

async function runDry() {
  const state = recomputeEquity(await loadState(config.paper.startingBalanceUsd));
  const evaluations = await discoveryCycle(state, { allowEntries: false });
  console.log(JSON.stringify({ mode: 'PAPER_DRY_RUN', candidates: evaluations.length, evaluations }, null, 2));
}

async function runPaper() {
  console.log(`PaperDesk PAPER MODE started. Cycle: ${config.cycleSeconds}s. Ctrl+C to stop.`);
  const state = await loadState(config.paper.startingBalanceUsd);
  const cycle = async () => {
    try {
      await riskCycle(state);
      recomputeEquity(state);
      await discoveryCycle(state, { allowEntries: true });
      recomputeEquity(state);
      await saveState(state);
      console.log(new Date().toISOString(), stats(state));
    } catch (error) {
      console.error(new Date().toISOString(), 'cycle_error', error.message);
    }
  };
  await cycle();
  setInterval(cycle, config.cycleSeconds * 1000);
}

async function runStatus() {
  const state = recomputeEquity(await loadState(config.paper.startingBalanceUsd));
  console.log(JSON.stringify({ ...stats(state), positions: state.positions.slice(-20) }, null, 2));
}

if (command === 'dry') await runDry();
else if (command === 'paper') await runPaper();
else if (command === 'status') await runStatus();
else throw new Error(`Unknown command: ${command}`);
