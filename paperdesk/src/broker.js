const round = (n, d = 8) => Number(n.toFixed(d));

export function simulateBuy(state, pool, sizeUsd, config, now = new Date()) {
  if (sizeUsd <= 0) throw new Error('sizeUsd must be > 0');
  if (!pool.priceUsd || pool.priceUsd <= 0) throw new Error('valid pool price required');
  if (state.positions.length >= config.paper.maxOpenPositions) throw new Error('max open positions reached');
  if (sizeUsd > state.cashUsd) throw new Error('insufficient paper cash');

  const feeUsd = sizeUsd * config.paper.feeBps / 10000;
  const liquidityImpactBps = pool.liquidityUsd > 0 ? Math.min(400, (sizeUsd / pool.liquidityUsd) * 10000) : config.paper.maxSlippageBps;
  const slippageBps = Math.min(config.paper.maxSlippageBps, config.paper.baseSlippageBps + liquidityImpactBps);
  const fillPriceUsd = pool.priceUsd * (1 + slippageBps / 10000);
  const netCostUsd = sizeUsd - feeUsd;
  const quantity = netCostUsd / fillPriceUsd;

  const position = {
    id: crypto.randomUUID(),
    poolAddress: pool.poolAddress,
    tokenAddress: pool.baseToken?.address ?? null,
    symbol: pool.baseToken?.symbol ?? pool.name ?? 'UNKNOWN',
    openedAt: now.toISOString(),
    decisionPriceUsd: pool.priceUsd,
    entryPriceUsd: round(fillPriceUsd, 12),
    quantity: round(quantity, 12),
    costUsd: round(sizeUsd, 8),
    entryFeeUsd: round(feeUsd, 8),
    entrySlippageBps: round(slippageBps, 4),
    markPriceUsd: pool.priceUsd,
    unrealizedPnlUsd: -feeUsd
  };

  state.cashUsd = round(state.cashUsd - sizeUsd, 8);
  state.positions.push(position);
  state.trades.push({ type: 'BUY', ...position });
  return position;
}

export function markPosition(position, marketPriceUsd) {
  if (!marketPriceUsd || marketPriceUsd <= 0) return position;
  position.markPriceUsd = marketPriceUsd;
  const markValue = position.quantity * marketPriceUsd;
  position.unrealizedPnlUsd = round(markValue - position.costUsd, 8);
  return position;
}

export function riskDecision(position, marketPriceUsd, config, now = new Date()) {
  if (!marketPriceUsd || marketPriceUsd <= 0) return { action: 'HOLD', reason: 'missing_price' };
  const returnPct = (marketPriceUsd - position.entryPriceUsd) / position.entryPriceUsd;
  const ageMinutes = (now.getTime() - Date.parse(position.openedAt)) / 60000;
  if (returnPct <= -config.paper.stopLossPct) return { action: 'EXIT', reason: 'stop_loss', returnPct };
  if (returnPct >= config.paper.takeProfitPct) return { action: 'EXIT', reason: 'take_profit', returnPct };
  if (ageMinutes >= config.paper.maxHoldMinutes) return { action: 'EXIT', reason: 'max_hold', returnPct };
  return { action: 'HOLD', reason: 'within_limits', returnPct };
}

export function simulateSell(state, positionId, marketPriceUsd, config, reason = 'manual', now = new Date()) {
  const index = state.positions.findIndex((p) => p.id === positionId);
  if (index < 0) throw new Error('position not found');
  const position = state.positions[index];
  const slippageBps = Math.min(config.paper.maxSlippageBps, config.paper.baseSlippageBps);
  const fillPriceUsd = marketPriceUsd * (1 - slippageBps / 10000);
  const grossUsd = position.quantity * fillPriceUsd;
  const feeUsd = grossUsd * config.paper.feeBps / 10000;
  const proceedsUsd = grossUsd - feeUsd;
  const pnlUsd = proceedsUsd - position.costUsd;

  state.positions.splice(index, 1);
  state.cashUsd = round(state.cashUsd + proceedsUsd, 8);
  state.realizedPnlUsd = round((state.realizedPnlUsd ?? 0) + pnlUsd, 8);
  const trade = {
    type: 'SELL',
    positionId,
    symbol: position.symbol,
    poolAddress: position.poolAddress,
    closedAt: now.toISOString(),
    exitPriceUsd: round(fillPriceUsd, 12),
    exitFeeUsd: round(feeUsd, 8),
    pnlUsd: round(pnlUsd, 8),
    reason
  };
  state.trades.push(trade);
  return trade;
}
