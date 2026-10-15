import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';

const config = JSON.parse(await fs.readFile(new URL('../config.json', import.meta.url), 'utf8'));
const statePath = path.resolve('data/state.json');

async function readState() {
  try { return JSON.parse(await fs.readFile(statePath, 'utf8')); }
  catch { return { cashUsd: config.paper.startingBalanceUsd, equityUsd: config.paper.startingBalanceUsd, realizedPnlUsd: 0, positions: [], trades: [], decisions: [] }; }
}

const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function page(state) {
  const exits = state.trades.filter((t) => t.type === 'SELL');
  const wins = exits.filter((t) => t.pnlUsd > 0).length;
  const winRate = exits.length ? (wins / exits.length * 100).toFixed(1) : '0.0';
  const positions = state.positions.map((p) => `<tr><td>${esc(p.symbol)}</td><td>${p.costUsd.toFixed(2)}</td><td>${p.entryPriceUsd}</td><td>${p.markPriceUsd}</td><td>${(p.unrealizedPnlUsd ?? 0).toFixed(2)}</td></tr>`).join('');
  const recent = state.trades.slice(-15).reverse().map((t) => `<tr><td>${esc(t.type)}</td><td>${esc(t.symbol)}</td><td>${esc(t.reason ?? '')}</td><td>${Number(t.pnlUsd ?? 0).toFixed(2)}</td></tr>`).join('');
  const decisions = state.decisions.slice(-20).reverse().map((d) => `<tr><td>${esc(d.agent ?? d.pick?.agent ?? '')}</td><td>${esc(d.action ?? d.pick?.action ?? '')}</td><td>${esc(d.reason ?? (d.pick?.reasons ?? []).join(', '))}</td></tr>`).join('');
  return `<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="refresh" content="10"><title>PaperDesk</title><style>body{font-family:system-ui;background:#0d1117;color:#e6edf3;margin:24px}.badge{display:inline-block;background:#1f6feb;padding:6px 10px;border-radius:8px;font-weight:700}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:18px 0}.card{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:14px}table{width:100%;border-collapse:collapse;margin:12px 0 28px}th,td{text-align:left;border-bottom:1px solid #30363d;padding:8px;font-size:14px}h2{margin-top:28px}</style></head><body><span class="badge">PAPER MODE</span><h1>PaperDesk</h1><div class="grid"><div class="card">Cash<br><b>$${Number(state.cashUsd ?? 0).toFixed(2)}</b></div><div class="card">Equity<br><b>$${Number(state.equityUsd ?? 0).toFixed(2)}</b></div><div class="card">Realized PnL<br><b>$${Number(state.realizedPnlUsd ?? 0).toFixed(2)}</b></div><div class="card">Open positions<br><b>${state.positions.length}</b></div><div class="card">Win rate<br><b>${winRate}%</b></div></div><h2>Open positions</h2><table><tr><th>Token</th><th>Cost</th><th>Entry</th><th>Mark</th><th>uPnL</th></tr>${positions}</table><h2>Recent trades</h2><table><tr><th>Type</th><th>Token</th><th>Reason</th><th>PnL</th></tr>${recent}</table><h2>Agent activity</h2><table><tr><th>Agent</th><th>Action</th><th>Reason</th></tr>${decisions}</table></body></html>`;
}

http.createServer(async (_req, res) => {
  const state = await readState();
  res.writeHead(200, { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' });
  res.end(page(state));
}).listen(config.dashboard.port, '127.0.0.1', () => {
  console.log(`PaperDesk dashboard: http://127.0.0.1:${config.dashboard.port}`);
});
