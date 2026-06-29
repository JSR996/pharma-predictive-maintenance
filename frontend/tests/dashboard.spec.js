import { test, expect } from '@playwright/test'

/**
 * E2E coverage for the PharmaGuard live dashboard.
 * Backend streams real CMAPSS predictions over WebSocket (~1.5s tick), so the
 * dashboard hydrates a beat after load — assertions use web-first auto-waiting.
 */

const API = 'http://localhost:8000'

test.describe('PharmaGuard dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('header renders and connects to the live stream', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'PharmaGuard', level: 1 })).toBeVisible()
    await expect(page.getByText('Live', { exact: true })).toBeVisible()
  })

  test('fleet status and equipment list render once data streams', async ({ page }) => {
    await expect(page.getByText('Fleet Status')).toBeVisible()
    await expect(page.getByRole('heading', { name: /Equipment \(\d+\)/ })).toBeVisible()

    const cards = page.getByRole('button').filter({ hasText: /COMP-\d+/ })
    await expect(cards.first()).toBeVisible()
    expect(await cards.count()).toBeGreaterThan(0)
  })

  test('selecting each equipment card updates the detail panel', async ({ page, request }) => {
    await expect(page.getByText('Fleet Status')).toBeVisible()

    const res = await request.get(`${API}/equipment/`)
    expect(res.ok()).toBeTruthy()
    const { equipment: units } = await res.json()
    expect(Array.isArray(units)).toBeTruthy()
    expect(units.length).toBeGreaterThan(0)

    for (const unit of units) {
      const card = page.getByRole('button').filter({ hasText: unit.id })
      await card.first().click()
      // The detail panel is the only place the unit name appears as a heading.
      await expect(page.getByRole('heading', { name: unit.name })).toBeVisible()
      await expect(page.getByText('Anomaly Score')).toBeVisible()
    }
  })

  test('sensor charts and alert feed render', async ({ page }) => {
    await expect(page.getByText('Fleet Status')).toBeVisible()

    // Full-word labels are unique to the chart panels (cards use Temp/Vib/Press).
    for (const label of ['Temperature', 'Vibration', 'Pressure']) {
      await expect(page.getByText(label, { exact: true })).toBeVisible()
    }
    await expect(page.getByText('RPM').first()).toBeVisible()

    await expect(page.getByRole('heading', { name: 'Alert Feed' })).toBeVisible()
    await expect(page.getByText('Equipment Health')).toBeVisible()
  })

  test('equipment health % agrees with the model RUL', async ({ request }) => {
    // Guards flaw #3: degradation_pct must be derived from RUL (rul/125), not
    // from replay-file position. "% remaining" therefore equals rul/cap.
    const RUL_CAP = 125
    const res = await request.get(`${API}/equipment/`)
    expect(res.ok()).toBeTruthy()
    const { equipment: units } = await res.json()
    for (const u of units) {
      const expectedRemaining = (100 * u.rul) / RUL_CAP
      const actualRemaining = 100 - u.degradation_pct
      expect(Math.abs(expectedRemaining - actualRemaining)).toBeLessThanOrEqual(0.1)
    }
  })

  test('perform maintenance resets a unit to healthy', async ({ page }) => {
    await expect(page.getByText('Fleet Status')).toBeVisible()

    const card = page.getByRole('button').filter({ hasText: 'COMP-01' }).first()
    await expect(card).toBeVisible()

    // On a healthy unit the action stays quiet until the card is hovered/focused.
    await card.hover()
    const maintain = card.getByRole('button', { name: /Perform Maintenance|Servicing/ })
    await expect(maintain).toBeVisible()

    const [res] = await Promise.all([
      page.waitForResponse(
        (r) => r.url().includes('/equipment/COMP-01/replace') &&
               r.request().method() === 'POST'
      ),
      maintain.click(),
    ])

    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.status).toBe('replaced')
    expect(body.reading.failed).toBe(false)
  })

  for (const vp of [
    { name: 'tablet', width: 768, height: 1024 },
    { name: 'desktop', width: 1440, height: 900 },
  ]) {
    test(`no horizontal overflow at ${vp.name} (${vp.width}px)`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height })
      await expect(page.getByText('Fleet Status')).toBeVisible()

      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth
      )
      expect(overflow).toBeLessThanOrEqual(1)
    })
  }
})
