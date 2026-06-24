import { chromium } from 'playwright'

const browser = await chromium.launch({ channel: 'msedge' })
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } })

const portfolio = {
  portfolio: {
    portfolio_id: 'pf-001',
    saa: { weights: { stock: 0.5, bond: 0.5 } },
    bindings: [
      { strategy_id: 'trend_ema_cross', strategy_name: 'EMA趋势跟踪', strategy_family: 'trend', symbol: '000001', symbol_name: '平安银行', weight: 0.25, sector: '股票' },
      { strategy_id: 'momentum_rsi', strategy_name: 'RSI动量反转', strategy_family: 'momentum', symbol: '000002', symbol_name: '万科A', weight: 0.25, sector: '股票' },
    ],
    risk_config: { stop_loss: 0.05, max_position: 0.3, max_drawdown: 0.15, rebalance_threshold: 0.05 }
  }
}

await page.goto('http://localhost:3000/backtests')
await page.evaluate(p => sessionStorage.setItem('latest_portfolio', JSON.stringify(p)), portfolio)
await page.reload({ waitUntil: 'networkidle' })
await page.waitForTimeout(2000)
await page.screenshot({ path: 'C:/Users/ALIENW~1/AppData/Local/Temp/backtest_config_ready.png', fullPage: false })

// Fill dates explicitly
const inputs = await page.locator('input[type=date]').all()
if (inputs.length >= 2) {
  const today = new Date()
  const lastYear = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate())
  await inputs[0].fill(lastYear.toISOString().split('T')[0])
  await inputs[1].fill(today.toISOString().split('T')[0])
}

await page.click('button:has-text("一键运行回测")')
await page.waitForTimeout(10000)
await page.screenshot({ path: 'C:/Users/ALIENW~1/AppData/Local/Temp/backtest_after_run.png', fullPage: false })
await browser.close()
console.log('Done')
