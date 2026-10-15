const ROOT = 'https://api.geckoterminal.com/api/v2';

const num = (value) => {
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
};

export async function discoverSolanaPools({ maxCandidates = 20, requestTimeoutMs = 12000 } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), requestTimeoutMs);
  const url = `${ROOT}/networks/solana/new_pools?include=base_token,quote_token&page=1`;
  try {
    const response = await fetch(url, {
      headers: { accept: 'application/json', 'user-agent': 'PaperDesk/0.1' },
      signal: controller.signal
    });
    if (!response.ok) throw new Error(`GeckoTerminal HTTP ${response.status}`);
    const payload = await response.json();
    const included = new Map((payload.included ?? []).map((x) => [x.id, x]));
    return (payload.data ?? []).slice(0, maxCandidates).map((pool) => normalizePool(pool, included));
  } finally {
    clearTimeout(timer);
  }
}

function normalizePool(pool, included) {
  const a = pool.attributes ?? {};
  const baseRel = pool.relationships?.base_token?.data?.id;
  const quoteRel = pool.relationships?.quote_token?.data?.id;
  const base = included.get(baseRel)?.attributes ?? {};
  const quote = included.get(quoteRel)?.attributes ?? {};
  const createdAt = a.pool_created_at ? Date.parse(a.pool_created_at) : NaN;
  const ageMinutes = Number.isFinite(createdAt) ? Math.max(0, (Date.now() - createdAt) / 60000) : null;

  return {
    source: 'geckoterminal',
    poolId: pool.id,
    poolAddress: a.address ?? null,
    name: a.name ?? null,
    baseToken: { address: base.address ?? null, name: base.name ?? null, symbol: base.symbol ?? null },
    quoteToken: { address: quote.address ?? null, name: quote.name ?? null, symbol: quote.symbol ?? null },
    priceUsd: num(a.base_token_price_usd),
    liquidityUsd: num(a.reserve_in_usd),
    marketCapUsd: num(a.market_cap_usd),
    fdvUsd: num(a.fdv_usd),
    volumeH1Usd: num(a.volume_usd?.h1),
    volumeH24Usd: num(a.volume_usd?.h24),
    buysH1: num(a.transactions?.h1?.buys),
    sellsH1: num(a.transactions?.h1?.sells),
    priceChangeM5Pct: num(a.price_change_percentage?.m5),
    priceChangeH1Pct: num(a.price_change_percentage?.h1),
    poolCreatedAt: a.pool_created_at ?? null,
    ageMinutes
  };
}

export async function fetchPool(network, poolAddress, requestTimeoutMs = 12000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), requestTimeoutMs);
  try {
    const response = await fetch(`${ROOT}/networks/${encodeURIComponent(network)}/pools/${encodeURIComponent(poolAddress)}`,
      { headers: { accept: 'application/json', 'user-agent': 'PaperDesk/0.1' }, signal: controller.signal });
    if (!response.ok) throw new Error(`GeckoTerminal HTTP ${response.status}`);
    const payload = await response.json();
    return normalizePool(payload.data, new Map());
  } finally {
    clearTimeout(timer);
  }
}
