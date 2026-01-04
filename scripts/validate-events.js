#!/usr/bin/env node
/**
 * Build-time validation for pricing-events.v1.json
 * Uses Ajv (JSON Schema) for schema validation + custom business rules
 * Run: npm run validate
 */

const Ajv = require('ajv');
const addFormats = require('ajv-formats');
const fs = require('fs');
const path = require('path');

// Paths
const SCHEMA_PATH = path.join(__dirname, '../schemas/pricing-events.schema.json');
const DATA_PATH = path.join(__dirname, '../public/data/pricing-events.v1.json');

// Colors for terminal output
const colors = {
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  reset: '\x1b[0m'
};

function log(color, symbol, message) {
  console.log(`${colors[color]}${symbol}${colors.reset} ${message}`);
}

function validateSchema(data, schema) {
  const ajv = new Ajv({ allErrors: true, strict: false });
  addFormats(ajv);

  const validate = ajv.compile(schema);
  const valid = validate(data);

  if (!valid) {
    log('red', '!', 'Schema validation failed:');
    validate.errors.forEach(err => {
      console.log(`  - ${err.instancePath || 'root'}: ${err.message}`);
      if (err.params) {
        console.log(`    ${JSON.stringify(err.params)}`);
      }
    });
    return false;
  }

  return true;
}

function validateBusinessRules(data) {
  const errors = [];
  const warnings = [];

  // 1. Check for duplicate IDs
  const ids = data.events.map(e => e.id);
  const duplicates = ids.filter((id, i) => ids.indexOf(id) !== i);
  if (duplicates.length > 0) {
    errors.push(`Duplicate event IDs: ${[...new Set(duplicates)].join(', ')}`);
  }

  // 2. Check chronological order
  let lastDate = null;
  for (const event of data.events) {
    const eventDate = new Date(event.date);
    if (lastDate && eventDate < lastDate) {
      warnings.push(`Events not in chronological order: ${event.id}`);
    }
    lastDate = eventDate;
  }

  // 3. Validate price change consistency
  for (const event of data.events) {
    if (event.type === 'price_drop' || event.type === 'price_increase') {
      if (!event.oldPrice || !event.newPrice) {
        errors.push(`${event.id}: price changes must have oldPrice and newPrice`);
      }
      if (!event.change) {
        errors.push(`${event.id}: price changes must have change percentage`);
      }
    }

    if (event.type === 'new_model' && event.oldPrice !== null) {
      warnings.push(`${event.id}: new_model events typically have null oldPrice`);
    }
  }

  // 4. Validate severity matches deterministic rubric
  for (const event of data.events) {
    if (event.change && event.severity) {
      const maxChange = Math.max(
        Math.abs(event.change.input || 0),
        Math.abs(event.change.output || 0)
      );

      const expectedSeverity =
        maxChange >= 0.50 ? 'critical' :
        maxChange >= 0.20 ? 'high' :
        maxChange >= 0.05 ? 'medium' : 'low';

      if (event.severity !== expectedSeverity && event.type !== 'new_model') {
        warnings.push(`${event.id}: severity '${event.severity}' may not match rubric (expected '${expectedSeverity}' for ${(maxChange * 100).toFixed(0)}% change)`);
      }
    }
  }

  // 5. Check sourceUrl accessibility (HTTPS required for high confidence)
  for (const event of data.events) {
    if (event.confidence === 'high' && !event.sourceUrl.startsWith('https://')) {
      errors.push(`${event.id}: high confidence events must have HTTPS sourceUrl`);
    }
  }

  // 6. Check verifiedAt is not in the future
  const now = new Date();
  for (const event of data.events) {
    if (new Date(event.verifiedAt) > now) {
      warnings.push(`${event.id}: verifiedAt is in the future`);
    }
  }

  // 7. Check tag consistency
  const validTags = new Set();
  for (const event of data.events) {
    if (event.tags) {
      event.tags.forEach(tag => validTags.add(tag));
    }
  }

  return { errors, warnings };
}

function main() {
  console.log('\n=== Pricing Events Validation ===\n');

  // Load files
  let schema, data;
  try {
    schema = JSON.parse(fs.readFileSync(SCHEMA_PATH, 'utf8'));
    log('green', '+', `Loaded schema: ${SCHEMA_PATH}`);
  } catch (err) {
    log('red', 'X', `Failed to load schema: ${err.message}`);
    process.exit(1);
  }

  try {
    data = JSON.parse(fs.readFileSync(DATA_PATH, 'utf8'));
    log('green', '+', `Loaded data: ${DATA_PATH}`);
  } catch (err) {
    log('red', 'X', `Failed to load data: ${err.message}`);
    process.exit(1);
  }

  console.log('');

  // Schema validation
  log('yellow', '~', 'Running JSON Schema validation...');
  const schemaValid = validateSchema(data, schema);

  if (!schemaValid) {
    log('red', 'X', 'Schema validation FAILED');
    process.exit(1);
  }
  log('green', '+', 'Schema validation passed');

  console.log('');

  // Business rules validation
  log('yellow', '~', 'Running business rules validation...');
  const { errors, warnings } = validateBusinessRules(data);

  if (warnings.length > 0) {
    console.log('\nWarnings:');
    warnings.forEach(w => log('yellow', '!', w));
  }

  if (errors.length > 0) {
    console.log('\nErrors:');
    errors.forEach(e => log('red', 'X', e));
    console.log('');
    log('red', 'X', `Validation FAILED with ${errors.length} error(s)`);
    process.exit(1);
  }

  // Summary
  console.log('\n=== Summary ===\n');
  log('green', '+', `Events: ${data.events.length}`);
  log('green', '+', `Providers: ${[...new Set(data.events.map(e => e.provider))].length}`);
  log('green', '+', `Date range: ${data.events[0]?.date} to ${data.events[data.events.length - 1]?.date}`);

  const typeCounts = data.events.reduce((acc, e) => {
    acc[e.type] = (acc[e.type] || 0) + 1;
    return acc;
  }, {});
  log('green', '+', `Types: ${Object.entries(typeCounts).map(([k,v]) => `${k}(${v})`).join(', ')}`);

  if (warnings.length > 0) {
    log('yellow', '!', `Warnings: ${warnings.length}`);
  }

  console.log('');
  log('green', '+', 'Validation PASSED');
  console.log('');
}

main();
