import { fileURLToPath } from 'node:url';
import { expect, test } from '@playwright/test';

const appNames = ['AllAboard', 'AllHail', 'OverBoard', 'OverHeard'];
const custom404 = fileURLToPath(new URL('../../404.html', import.meta.url));

test.beforeEach(async ({ context, baseURL }) => {
  await context.route('**/*', route =>
    new URL(route.request().url()).origin === baseURL ? route.continue() : route.abort()
  );
});

test('the homepage displays the app cards and remembers the theme', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  await expect(page.locator('link[rel="stylesheet"][href$="style.css"]')).toHaveCount(1);
  for (const name of appNames) {
    await expect(page.getByRole('heading', { name, exact: true })).toBeVisible();
  }

  await page.getByRole('button', { name: 'Switch to dark mode' }).click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await page.reload();
  await expect(page.getByRole('button', { name: 'Switch to light mode' })).toBeVisible();
  expect(errors).toEqual([]);
});

test('the homepage fits a phone viewport', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto('/');
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  const overflows = await page.locator('body').evaluate(body =>
    body.scrollWidth > document.documentElement.clientWidth
  );
  expect(overflows).toBe(false);
});

test('hub pages and their local links and assets resolve', async ({ page }) => {
  const links = new Set();
  for (const path of ['/', '/privacy.html', '/terms.html', '/404.html']) {
    const response = await page.goto(path);
    expect(response.status(), path).toBe(200);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    const pageLinks = await page.locator('a[href], link[href], script[src], img[src]').evaluateAll(elements =>
      elements.map(element => {
        const url = new URL(element.getAttribute('href') ?? element.getAttribute('src'), document.baseURI);
        url.hash = '';
        return url.origin === window.location.origin ? url.href : null;
      }).filter(Boolean)
    );
    for (const url of pageLinks) links.add(url);
  }

  for (const url of links) {
    const response = await page.request.head(url);
    await expect(response, url).toBeOK();
  }
});

const roomOrigin = 'https://over-heard-606573080592.us-east1.run.app';
const shortcuts = [
  ['/chefbot/', '/ChefBot/'],
  ['/cHeFbOt', '/ChefBot/'],
  ['/AlLaBoArD/', 'https://allaboard-606573080592.us-east1.run.app/'],
  ['/OvErBoArD/', 'https://bpmdata.github.io/OverBoard/app/'],
  ['/OvErHeArD/', roomOrigin + '/'],
  ['/Physics-42/', roomOrigin + '/physics-42'],
];

for (const [shortcut, target] of shortcuts) {
  test(`the 404 page routes ${shortcut}`, async ({ page, baseURL }) => {
    const destination = new URL(target, baseURL);
    // GitHub Pages serves this file at the missing URL. Stub the destination so
    // a linked app's availability cannot affect the test.
    await page.route(url => url.pathname === shortcut, route =>
      route.fulfill({ status: 404, path: custom404 })
    );
    await page.route(url => url.origin === destination.origin && url.pathname === destination.pathname, route =>
      route.fulfill({ contentType: 'text/html', body: '<title>Destination</title>' })
    );
    await page.goto(shortcut + '?source=test#section');
    await expect(page).toHaveURL(destination.href + '?source=test#section');
  });
}
