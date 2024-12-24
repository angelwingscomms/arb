from re import A
from typing import Optional, Tuple
import ccxt, json
from asyncio import gather, run


async def fetch_price(exchange, symbol) -> Optional[Tuple[str, int]]:
   print('checking', symbol, 'on', exchange)
   try:
       ticker = await exchange.fetch_ticker(symbol)
       return exchange.id, ticker['last']
   except Exception as e:
       print(type(e).__name__, str(e))
       return None

async def compare_symbol(exchanges, symbol) -> Tuple[Tuple[str, int], Tuple[str, int]]:
   coroutines = [fetch_price(exchange, symbol) for exchange in exchanges]
   results = await gather(*coroutines);
   results = [result for result in results if result is not None]
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

def scan():
    ex = {}
    prices = {}
    symbols = get_symbols()
    symbols_to_scan = ['SOL', 'BTC', 'XRP', 'DOGE']
    symbols = {k: v for k, v in symbols.items() if len(v) > 1 and any(sub in k for sub in symbols_to_scan)}
    for symbol in symbols.keys():
        for exchange in symbols[symbol]:
            x = getattr(ccxt, exchange)()
            try:
                print('loading', x.id)
                x.load_markets()
            except:
                ''
            if not x.id in ex:
                ex[x.id] = x

    prices = []
    for symbol in symbols.keys():
        exchanges = [ex[x] for x in symbols[symbol]]
        prices.append(compare_symbol(exchanges, symbol))
    print(prices)
scan()