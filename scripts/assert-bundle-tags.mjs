#!/usr/bin/env node
/*
 * Post-build assertion: no bundle fragment contains a tag outside the
 * allowlist declared alongside the build in scripts/build-bundle.mjs.
 *
 * The build step already rejects raw HTML at parse time and runs DOMPurify
 * over the rendered output, so a violation here would mean the sanitizer
 * missed something or the allowlist and the sanitizer's ALLOWED_TAGS have
 * drifted. Either way this is the last line of defence before the bundle
 * is uploaded, and it makes the invariant a testable property.
 *
 * Usage:
 *   node scripts/assert-bundle-tags.mjs [--bundle path/to/content-bundle.json]
 */

import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

import { ALLOWED_HTML_TAGS } from './build-bundle.mjs';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const bundleArg = process.argv.indexOf('--bundle');
const bundlePath =
  bundleArg !== -1 ? process.argv[bundleArg + 1] : join(root, 'content-bundle.json');

const bundle = JSON.parse(readFileSync(bundlePath, 'utf8'));
const allowed = new Set(ALLOWED_HTML_TAGS.map((t) => t.toLowerCase()));

const violations = [];

function scan(html, label) {
  // Match every opening or self-closing tag name, ignoring closing tags
  // (redundant with openings) and comments (already stripped by DOMPurify).
  // Attribute contents can never contain a `>`, so the greedy stop at the
  // next `>` is safe for the allowlist we ship.
  const re = /<([a-zA-Z][a-zA-Z0-9-]*)\b[^>]*>/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    const tag = m[1].toLowerCase();
    if (!allowed.has(tag)) {
      violations.push({ label, tag, snippet: html.slice(m.index, m.index + 120) });
    }
  }
}

for (const section of bundle.faq_sections ?? []) {
  for (const entry of section.entries ?? []) {
    scan(entry.html ?? '', `faq/${entry.id}`);
  }
}
for (const doc of bundle.docs ?? []) {
  scan(doc.html ?? '', `docs/${doc.id}`);
}

if (violations.length > 0) {
  console.error('assert-bundle-tags: disallowed tags in the bundle:');
  for (const v of violations) {
    console.error(`  ${v.label}: <${v.tag}> - ${v.snippet}`);
  }
  process.exit(1);
}

console.log('assert-bundle-tags: OK, every rendered fragment uses only allowlisted tags.');
