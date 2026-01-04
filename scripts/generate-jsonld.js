#!/usr/bin/env node
/**
 * Generate JSON-LD at build time for SEO crawlability
 * Run: npm run generate:jsonld
 */

const fs = require('fs');
const path = require('path');

// Paths
const DATA_PATH = path.join(__dirname, '../public/data/pricing-events.v1.json');
const OUTPUT_PATH = path.join(__dirname, '../public/data/pricing-events.jsonld.json');

// Colors for terminal output
const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  reset: '\x1b[0m'
};

function log(color, symbol, message) {
  console.log(`${colors[color]}${symbol}${colors.reset} ${message}`);
}

function generateJsonLd(data) {
  const events = data.events;
  const providers = [...new Set(events.map(e => e.provider))];
  const minDate = events.reduce((min, e) => e.date < min ? e.date : min, events[0].date);
  const maxDate = events.reduce((max, e) => e.date > max ? e.date : max, events[0].date);

  // Main Dataset schema
  const dataset = {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "LLM Pricing Events History",
    "description": `Comprehensive timeline of ${events.length} LLM API pricing changes from major providers including ${providers.slice(0, 4).join(', ')}${providers.length > 4 ? ' and more' : ''}. Covering ${minDate} to ${maxDate}.`,
    "url": "https://inferencepriceindex.com/intelligence.html",
    "identifier": "inference-price-index-events-v1",
    "dateModified": data.generatedAt,
    "temporalCoverage": `${minDate}/${maxDate}`,
    "license": "https://creativecommons.org/licenses/by/4.0/",
    "creator": {
      "@type": "Organization",
      "name": "Intent Solutions",
      "url": "https://intentsolutions.io"
    },
    "publisher": {
      "@type": "Organization",
      "name": "Inference Price Index",
      "url": "https://inferencepriceindex.com",
      "logo": {
        "@type": "ImageObject",
        "url": "https://inferencepriceindex.com/logo.png"
      }
    },
    "keywords": [
      "LLM pricing",
      "AI API costs",
      "GPT-4 pricing",
      "Claude pricing",
      "Gemini pricing",
      "inference costs",
      "token pricing",
      "AI model comparison"
    ],
    "distribution": [
      {
        "@type": "DataDownload",
        "encodingFormat": "application/json",
        "contentUrl": "https://inferencepriceindex.com/v1/events"
      }
    ],
    "measurementTechnique": "Manual curation from official provider pricing pages with verification",
    "variableMeasured": [
      {
        "@type": "PropertyValue",
        "name": "Input Token Price",
        "unitText": "USD per million tokens"
      },
      {
        "@type": "PropertyValue",
        "name": "Output Token Price",
        "unitText": "USD per million tokens"
      }
    ]
  };

  // Generate individual event items for FAQ/timeline rich results
  const eventItems = events
    .filter(e => e.severity === 'critical' || e.severity === 'high')
    .slice(0, 10)
    .map(event => ({
      "@type": "Event",
      "name": event.headline,
      "description": event.description,
      "startDate": event.date,
      "organizer": {
        "@type": "Organization",
        "name": event.provider
      },
      "about": {
        "@type": "Product",
        "name": event.model || `${event.provider} API`
      }
    }));

  // FAQ schema for common questions
  const faqSchema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {
        "@type": "Question",
        "name": "How much does GPT-4 API cost?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "GPT-4 API pricing has dropped significantly since launch. GPT-4o currently costs $2.50 per million input tokens and $10 per million output tokens, while GPT-4o Mini costs just $0.15 per million input tokens and $0.60 per million output tokens."
        }
      },
      {
        "@type": "Question",
        "name": "How much have LLM API prices dropped?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": `Since GPT-4's launch in March 2023, frontier model prices have dropped by over 90%. The Inference Price Index tracks ${events.length} pricing events across major providers.`
        }
      },
      {
        "@type": "Question",
        "name": "Which LLM API is cheapest?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "For frontier-class quality, DeepSeek V3 offers the lowest pricing at $0.14 per million input tokens. For efficient-tier models, GPT-4o Mini and Gemini 1.5 Flash offer sub-$0.20 pricing with strong capabilities."
        }
      }
    ]
  };

  // Breadcrumb schema
  const breadcrumb = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {
        "@type": "ListItem",
        "position": 1,
        "name": "Inference Price Index",
        "item": "https://inferencepriceindex.com"
      },
      {
        "@type": "ListItem",
        "position": 2,
        "name": "Pricing Intelligence",
        "item": "https://inferencepriceindex.com/intelligence.html"
      }
    ]
  };

  // WebPage schema
  const webPage = {
    "@context": "https://schema.org",
    "@type": "WebPage",
    "name": "LLM Pricing Intelligence Center",
    "description": `Track ${events.length} historical LLM pricing events, calculate savings, and compare API costs across providers.`,
    "url": "https://inferencepriceindex.com/intelligence.html",
    "dateModified": data.generatedAt,
    "isPartOf": {
      "@type": "WebSite",
      "name": "Inference Price Index",
      "url": "https://inferencepriceindex.com"
    },
    "mainEntity": dataset,
    "breadcrumb": breadcrumb
  };

  return {
    "@context": "https://schema.org",
    "@graph": [
      webPage,
      dataset,
      faqSchema,
      breadcrumb
    ]
  };
}

function main() {
  console.log('\n=== JSON-LD Generation ===\n');

  // Load data
  let data;
  try {
    data = JSON.parse(fs.readFileSync(DATA_PATH, 'utf8'));
    log('green', '+', `Loaded data: ${DATA_PATH}`);
  } catch (err) {
    log('red', 'X', `Failed to load data: ${err.message}`);
    process.exit(1);
  }

  // Generate JSON-LD
  const jsonld = generateJsonLd(data);

  // Write output
  try {
    fs.writeFileSync(OUTPUT_PATH, JSON.stringify(jsonld, null, 2));
    log('green', '+', `Generated JSON-LD: ${OUTPUT_PATH}`);
  } catch (err) {
    log('red', 'X', `Failed to write output: ${err.message}`);
    process.exit(1);
  }

  // Summary
  console.log('');
  log('green', '+', `Schemas generated: ${jsonld['@graph'].length}`);
  log('green', '+', 'JSON-LD generation complete');
  console.log('');
}

main();
