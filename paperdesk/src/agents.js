export function scan(pool, config) {
  const f = config.filters;
  const reasons = [];
  if (pool.priceUsd == null || pool.priceUsd <= 0) reasons.push('missing_or_invalid_price');
  if (pool.liquidityUsd == null || pool.liquidityUsd < f.minLiquidityUsd) reasons.push('liquidity_below_min');
  if (pool.volumeH1Usd == null || pool.volumeH1Usd < f.minVolumeH1Usd) reasons.push('h1_volume_below_min');
  if (pool.ageMinutes == null) reasons.push('missing_pool_age');
  else {
    if (pool.ageMinutes < f.minPoolAgeMinutes) reasons.push('pool_too_new');
    if (pool.ageMinutes > f.maxPoolAgeHours * 60) reasons.push('pool_too_old');
  }
  if (pool.priceChangeM5Pct != null && Math.abs(pool.priceChangeM5Pct) > f.maxAbsPriceChangeM5Pct) {
    reasons.push('extreme_5m_price_change');
  }
  return { agent: 'SCAN', pass: reasons.length === 0, reasons, evidence: pool };
}

export function vet(pool) {
  const reasons = [];
  if (!pool.poolAddress) reasons.push('missing_pool_address');
  if (!pool.baseToken?.address) reasons.push('missing_base_token_address');
  if (pool.liquidityUsd == null) reasons.push('missing_liquidity');
  return {
    agent: 'VET',
    status: reasons.length ? 'WARN' : 'PASS',
    reasons,
    evidence: {
      poolAddress: pool.poolAddress,
      baseTokenAddress: pool.baseToken?.address ?? null,
      liquidityUsd: pool.liquidityUsd
    },
    note: 'v0.1 performs only deterministic data-completeness checks; on-chain authority/holder checks are not yet implemented.'
  };
}

export function social(pool) {
  return {
    agent: 'SOCIAL',
    status: 'UNKNOWN',
    reasons: ['social_provider_not_configured'],
    evidence: { token: pool.baseToken?.symbol ?? null }
  };
}

export function judge({ scanResult, vetResult }) {
  const hardFail = !scanResult.pass;
  const vetWarns = vetResult.reasons.length;
  const confidence = hardFail ? 0 : Math.max(0.5, 0.8 - vetWarns * 0.1);
  return {
    agent: 'JUDGE',
    action: hardFail ? 'SKIP' : 'BUY_CANDIDATE',
    confidence,
    reasons: [...scanResult.reasons, ...vetResult.reasons]
  };
}

export function pick(judgement) {
  return {
    agent: 'PICK',
    action: judgement.action === 'BUY_CANDIDATE' && judgement.confidence >= 0.7 ? 'BUY' : 'SKIP',
    confidence: judgement.confidence,
    reasons: judgement.reasons
  };
}

export function size(state, config, pool) {
  const capByPct = state.equityUsd * config.paper.positionPct;
  const requested = Math.min(capByPct, config.paper.maxPositionUsd, state.cashUsd);
  const liquidityCap = pool.liquidityUsd == null ? 0 : pool.liquidityUsd * 0.001;
  const usd = Math.max(0, Math.min(requested, liquidityCap));
  return { agent: 'SIZE', usd: Number(usd.toFixed(2)), reasons: usd <= 0 ? ['insufficient_size_or_liquidity'] : [] };
}
