#!/usr/bin/env node
/*
 * Build content-bundle.json from the markdown in faq/, metrics/, and docs/.
 *
 * The bundle is the only artifact the website consumes. Rendering happens
 * here, once, at build time: the site never ships a markdown parser. Every
 * file's frontmatter is validated against the schemas in schemas/; a
 * validation failure fails the build loudly rather than shipping a
 * half-formed bundle.
 *
 * Files with `publish: false` in frontmatter are excluded from the bundle
 * but still linted. This lets prose that depends on a future state (for
 * example, contribution instructions that reference this repository being
 * public) be written, reviewed, and merged ahead of the state it needs.
 *
 * Usage: node scripts/build-bundle.mjs [--out content-bundle.json]
 */

import { readFileSync, readdirSync, writeFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execSync } from 'node:child_process';
import matter from 'gray-matter';
import { marked } from 'marked';
import Ajv2020 from 'ajv/dist/2020.js';
const Ajv = Ajv2020.default ?? Ajv2020;

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const outArg = process.argv.indexOf('--out');
const outPath = outArg !== -1 ? process.argv[outArg + 1] : join(root, 'content-bundle.json');

const ajv = new Ajv({ useDefaults: true, allErrors: true });
const faqSchema = ajv.compile(JSON.parse(readFileSync(join(root, 'schemas/faq.json'), 'utf8')));
const docSchema = ajv.compile(JSON.parse(readFileSync(join(root, 'schemas/doc.json'), 'utf8')));
const metricSchema = ajv.compile(JSON.parse(readFileSync(join(root, 'schemas/metric.json'), 'utf8')));

/**
 * FAQ section order and display titles. The site renders sections in this
 * order. A category used in frontmatter but missing here fails the build,
 * so the order stays a conscious decision.
 */
const FAQ_SECTIONS = [
  ['about', 'About the portal'],
  ['site-tour', 'Finding your way around'],
  ['metrics', 'Metrics and definitions'],
  ['sources', 'Sources and reconciliation'],
  ['anchoring', 'Anchoring and verification'],
  ['methodology', 'Methodology and corrections'],
  ['governance', 'Governance and independence'],
  ['statutory', 'Statutory and regulatory frameworks'],
  ['recognition-ledger', 'The recognition ledger'],
  ['concepts', 'Concepts and terminology'],
  ['contributing', 'Contributing and disputing'],
  ['consumption', 'Using the data'],
];

marked.setOptions({ gfm: true });

function fail(msg) {
  console.error(`build-bundle: ${msg}`);
  process.exit(1);
}

function loadDir(dir, schema, kind) {
  const full = join(root, dir);
  if (!existsSync(full)) return [];
  const out = [];
  for (const name of readdirSync(full).filter((n) => n.endsWith('.md')).sort()) {
    const raw = readFileSync(join(full, name), 'utf8');
    const { data, content } = matter(raw);
    if (!schema(data)) {
      fail(`${dir}/${name} frontmatter invalid: ${ajv.errorsText(schema.errors)}`);
    }
    if (data.id !== name.replace(/\.md$/, '')) {
      fail(`${dir}/${name}: frontmatter id "${data.id}" must match the filename`);
    }
    out.push({ ...data, body: content.trim(), kind });
  }
  return out;
}

const faqs = loadDir('faq', faqSchema, 'faq');
const metrics = loadDir('metrics', metricSchema, 'metric');
const docs = loadDir('docs', docSchema, 'doc');

const sectionIds = new Set(FAQ_SECTIONS.map(([id]) => id));
for (const f of faqs) {
  if (!sectionIds.has(f.category)) fail(`faq/${f.id}.md: category "${f.category}" is not in FAQ_SECTIONS`);
}

const publishedFaqs = faqs.filter((f) => f.publish !== false);
const faqSections = FAQ_SECTIONS.map(([id, title]) => ({
  id,
  title,
  entries: publishedFaqs
    .filter((f) => f.category === id)
    .map((f) => ({
      id: f.id,
      question: f.question,
      html: marked.parse(f.body),
      audience: f.audience,
      last_reviewed: f.last_reviewed,
    })),
})).filter((s) => s.entries.length > 0);

const metricFramings = {};
for (const m of metrics.filter((m) => m.publish !== false)) {
  metricFramings[m.id] = m.question;
}

const publishedDocs = docs
  .filter((d) => d.publish !== false)
  .map((d) => ({
    id: d.id,
    title: d.title,
    category: d.category,
    audience: d.audience,
    html: marked.parse(d.body),
    last_reviewed: d.last_reviewed,
  }));

let contentVersion = 'unversioned';
try {
  contentVersion = execSync('git rev-parse --short HEAD', { cwd: root }).toString().trim();
} catch {
  /* fresh repo without a commit yet */
}

const bundle = {
  schema_version: 1,
  content_version: contentVersion,
  generated_at: new Date().toISOString(),
  faq_sections: faqSections,
  metric_framings: metricFramings,
  docs: publishedDocs,
};

writeFileSync(outPath, JSON.stringify(bundle, null, 1) + '\n');
const counts = `${publishedFaqs.length} FAQ entries (${faqs.length - publishedFaqs.length} held back), ${Object.keys(metricFramings).length} metric framings, ${publishedDocs.length} docs`;
console.log(`build-bundle: wrote ${outPath} (${counts}, content_version ${contentVersion})`);
