import type { FreshEvent, FreshSchema } from './api';

export const MAX_UPLOAD_ROWS = 30;
export const MAX_UPLOAD_BYTES = 61440;

const metadata = [
  'event_id', 'tool_life_id', 'asset_id', 'sequence_number', 'cut_completed_at', 'feature_schema_version',
  'sensor_profile_version', 'inspection_breaks', 'source_mode', 'clock_basis', 'data_origin',
];

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function csvRecords(input: string) {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = '';
  let quoted = false;
  let closingQuote = false;

  function endField() {
    row.push(field);
    field = '';
    closingQuote = false;
  }

  function endRecord() {
    endField();
    if (row.some((value) => value.trim())) rows.push(row);
    row = [];
  }

  for (let i = 0; i < input.length; i++) {
    const char = input[i];
    if (quoted) {
      if (char !== '"') field += char;
      else if (input[i + 1] === '"') { field += '"'; i++; }
      else { quoted = false; closingQuote = true; }
    } else if (char === ',') endField();
    else if (char === '\n' || char === '\r') {
      if (char === '\r' && input[i + 1] === '\n') i++;
      endRecord();
    } else if (char === '"' && !field && !closingQuote) quoted = true;
    else if (char === '"' || closingQuote) throw new Error('CSV contains an invalid quoted field.');
    else field += char;
  }
  if (quoted) throw new Error('CSV contains an unclosed quoted field.');
  if (row.length || field || closingQuote) endRecord();
  return rows;
}

function readCsv(input: string, schema: FreshSchema) {
  const [header = [], ...records] = csvRecords(input);
  const names = header.map((name) => name.trim());
  const columns = new Set(names);
  if (columns.size !== names.length) throw new Error('CSV column names must be unique.');
  if (!columns.has('event_id')) throw new Error('CSV requires an event_id column. Download template for exact field names.');
  const contextFields = new Set(schema.context_fields);
  const featureFields = new Set(schema.feature_fields);

  return records.map((row, index) => {
    if (row.length !== names.length) throw new Error(`CSV record ${index + 1} has ${row.length} values for ${names.length} columns.`);
    const context: FreshEvent = {};
    const features: FreshEvent = {};
    const event: FreshEvent = { source_mode: 'uploaded', context, features };
    names.forEach((name, column) => {
      const value = row[column].trim();
      if (!value) return;
      if (contextFields.has(name)) context[name] = Number.isFinite(Number(value)) ? Number(value) : value;
      else if (featureFields.has(name)) features[name] = Number.isFinite(Number(value)) ? Number(value) : value;
      else if (name === 'sequence_number') event[name] = Number.isFinite(Number(value)) ? Number(value) : value;
      else if (name === 'inspection_breaks') event[name] = value.split(';').map((slot) => slot.trim() && Number.isFinite(Number(slot)) ? Number(slot) : slot);
      else Object.defineProperty(event, name, { value, enumerable: true, configurable: true });
    });
    return event;
  });
}

export function importCuts(text: string, filename: string, schema: FreshSchema): FreshEvent[] {
  const input = text.replace(/^\uFEFF/, '');
  let events: unknown;
  if (filename.toLowerCase().endsWith('.csv')) events = readCsv(input, schema);
  else if (filename.toLowerCase().endsWith('.json')) {
    let json: unknown;
    try { json = JSON.parse(input); }
    catch { throw new Error('Invalid JSON. Provide a cut, an array of cuts, or an object with an events array.'); }
    events = Array.isArray(json) ? json : object(json) && 'events' in json ? json.events : [json];
  } else throw new Error('Choose a .csv or .json file.');
  if (!Array.isArray(events) || !events.length || !events.every(object)) throw new Error('File must contain at least one cut object.');
  if (events.length > MAX_UPLOAD_ROWS) throw new Error(`Upload at most ${MAX_UPLOAD_ROWS} cuts at a time.`);
  if (new TextEncoder().encode(JSON.stringify({ events })).length > MAX_UPLOAD_BYTES) throw new Error('Expanded upload is too large. Split it into smaller files.');
  return events;
}

export function cutTemplate(schema: FreshSchema, format: 'json' | 'csv') {
  if (format === 'json') {
    const values = (fields: string[]) => Object.fromEntries(fields.map((field) => [field, null]));
    return JSON.stringify({ events: [{
      event_id: '', asset_id: '', tool_life_id: '', sequence_number: null, cut_completed_at: '',
      feature_schema_version: schema.feature_schema_version, sensor_profile_version: schema.sensor_profile_version ?? '',
      source_mode: 'uploaded', clock_basis: 'observed', data_origin: 'user-measured', inspection_breaks: [],
      context: values(schema.context_fields), features: values(schema.feature_fields),
    }] }, null, 2) + '\n';
  }
  const columns = [...metadata, ...schema.context_fields, ...schema.feature_fields];
  return columns.map((name) => `"${name.replaceAll('"', '""')}"`).join(',') + '\n';
}

export function downloadEvidence(filename: string, content: string, type: string) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
