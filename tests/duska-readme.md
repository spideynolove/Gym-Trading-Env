<h1>dukascopy-node</h1>

<p align="center"><img width="150" src="https://github.com/Leo4815162342/dukascopy-node/blob/master/dukascopy-node.png?raw=true" alt="dukascopy-node"></p>

<p align="center">
    <b>✨ Download free historical market price tick data ✨</b> <br>Stocks • Crypto • Commodities • Bonds • Currencies • CFDs • ETFs  <br> via Node.js and CLI
</p>

***

## 🚀 Installation

<table>
    <thead>
        <tr>
            <th><img width="16" src="https://www.dukascopy-node.app/npm.png" alt="dukascopy-node via npm"> npm</th>
            <th><img width="16" src="https://www.dukascopy-node.app/yarn.png" alt="dukascopy-node via yarn"> yarn</th>
            <th><img width="16" src="https://www.dukascopy-node.app/pnpm.png" alt="dukascopy-node via pnpm"> pnpm</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><pre><code>npm install dukascopy-node --save</code></pre></td>
            <td><pre><code>yarn add dukascopy-node</code></pre></td>
            <td><pre><code>pnpm add dukascopy-node</code></pre></td>
        </tr>
    </tbody>
</table>

## ✨ Usage via CLI

```bash
npx dukascopy-node -i btcusd -from 2019-01-13 -to 2019-01-14 -t tick -f csv
```

![dukascopy-node-1080p](https://user-images.githubusercontent.com/12486774/210557823-63ba12f1-ab77-42ae-ad27-6c199b0c1fdb.gif)


[🛠️ View full CLI specification](https://www.dukascopy-node.app/config/cli)

---

## ✨ Usage via Node.js ([try it live](https://runkit.com/embed/of4ho2xv8rvv))

```javascript
const { getHistoricalRates } = require('dukascopy-node');

(async () => {
  try {
    const data = await getHistoricalRates({
      instrument: 'btcusd',
      dates: {
        from: new Date('2019-01-13'),
        to: new Date('2019-01-14')
      },
      timeframe: 'tick',
      format: 'json'
    });

    console.log(data);
  } catch (error) {
    console.log('error', error);
  }
})();
```

[🛠️ View full Node.js specification](https://www.dukascopy-node.app/config/node)

---

## 📖 Quick start
* [Basic usage of `dukascopy-node`](https://www.dukascopy-node.app/output-formats)
* [Downloading tick data](https://www.dukascopy-node.app/downloading-tick-data)
* [Date formatting and converting timezones](https://www.dukascopy-node.app/custom-date-format-and-timezone-conversion)
* [Dealing with empty data and errors](https://www.dukascopy-node.app/errors-and-empty-data)
* [Downloading data with cache](https://www.dukascopy-node.app/using-cache)
* [Downloading data with custom batching](https://www.dukascopy-node.app/custom-batching)
* [Usage with typescript](https://www.dukascopy-node.app/with-typescript)
* [Debugging](https://www.dukascopy-node.app/debugging)

---

## 📂 Instruments

...
* [Forex major currencies 💶 (7)](#fx_majors)
...

<hr>

<h3 id="fx_majors">Forex major currencies 💶</h3>

|Instrument|id|Earliest data (UTC)|
|-|-|-|
|[Australian Dollar vs US Dollar](https://www.dukascopy-node.app/instrument/audusd)|`audusd`|Jan 4, 1993|
|[Euro vs US Dollar](https://www.dukascopy-node.app/instrument/eurusd)|`eurusd`|Mar 1, 1973|
|[Pound Sterling vs US Dollar](https://www.dukascopy-node.app/instrument/gbpusd)|`gbpusd`|Feb 10, 1986|
|[New Zealand Dollar vs US Dollar](https://www.dukascopy-node.app/instrument/nzdusd)|`nzdusd`|Jul 8, 1991|
|[US Dollar vs Canadian Dollar](https://www.dukascopy-node.app/instrument/usdcad)|`usdcad`|Feb 10, 1986|
|[US Dollar vs Swiss Franc](https://www.dukascopy-node.app/instrument/usdchf)|`usdchf`|Feb 10, 1986|
|[US Dollar vs Japanese Yen](https://www.dukascopy-node.app/instrument/usdjpy)|`usdjpy`|Feb 10, 1986|
<h3 id="fx_metals">Forex metals 🥇</h3>
...