from re import A
from typing import Optional, Tuple
import ccxt, json
import pprint
from asyncio import gather, run


async def fetch_price(exchange, symbol) -> Optional[Tuple[str, int]]:
   print('checking', symbol, 'on', exchange)
   try:
       ticker = exchange.fetch_ticker(symbol)
       return exchange.name, ticker['last']
   except Exception as e:
       print(type(e).__name__, str(e))
       return None

async def compare_symbol(exchanges, symbol) -> Tuple[Tuple[str, int], Tuple[str, int]]:
   print('comparing', symbol)
   coroutines = [fetch_price(exchange, symbol) for exchange in exchanges]
   results = await gather(*coroutines);
   results = [result for result in results if result is not None and result[1] is not None]
   if not results:
       raise ValueError('no valid results in compare_symbol')
   return min(results, key=lambda x: x[1]), max(results, key=lambda x: x[1])

def collect_symbols():
    print("started collecting symbols")

    ex = []

    symbols = {}

    symbol = "SOL/USDC:USDC"
    for exchange in ccxt.exchanges:
        try:
            x = getattr(ccxt, exchange)()
            x.loadMarkets()
            ex.append(x)
        except Exception as e:
            print(f"Error processing exchange {exchange}: {e}")
    for x in ex:
        try:
            if not hasattr(x, 'symbols') or not isinstance(x.symbols, list):
                continue
            for sym in x.symbols:
                if sym not in symbols:
                    symbols[sym] = []
                symbols[sym].append(x.id)
        except Exception as e:
            print(f"Error processing exchange {x.name}: {e}")

    with open('symbols.json', 'w') as f:
        json.dump(symbols, f, indent=1)
    print(symbols)

def get_symbols():
    with open('symbols.json', 'r') as f:
        return json.load(f)

async def scan():
    print('started')
    ex = {}
    prices = {}
    symbols = get_symbols()
    symbols_to_scan = ['SOL/USDT', 'ADA/USDT', 'ETH/USDT', 'NEAR/USDT', 'BTC/USDT', 'XRP/USDT', 'DOGE/USDT']
    symbols = {k: v for k, v in symbols.items() if len(v) > 1 and k in symbols_to_scan}
    # symbols = {k: v for k, v in symbols.items() if len(v) > 1 and any(sub in k for sub in symbols_to_scan)}
    for symbol in symbols.keys():
        for exchange in symbols[symbol]:
            if not exchange in ex:
                x = getattr(ccxt, exchange)()
                try:
                    print('loading', x.id)
                    x.load_markets()
                    ex[x.id] = x
                    print('loaded', x.id)
                except Exception as e:
                    print('exception with', exchange, ':', e)

    # print(ex)
    prices = {}
    for symbol in symbols.keys():
        print('starting', symbol)
        exchanges = [ex[x] for x in symbols[symbol] if x in ex]
        minmax = await compare_symbol(exchanges, symbol)
        prices[symbol] = {"min": minmax[0], "max": minmax[1]}
    pprint.pprint(prices)
run(scan())
