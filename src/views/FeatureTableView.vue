<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue';
import Plotly from 'plotly.js-dist-min';
import { parseRtIntensityPairs } from '../utils/peak';
import { normalizeMirrorPeaks, parseSpectrum } from '../utils/spectra';

const allFeatures = ref([]);
const statusText = ref('No file loaded.');
const filterField = ref('all');
const filterQuery = ref('');
const selectedFeature = ref(null);
const peakNote = ref('');
const ms2Note = ref('');

const peakPlotEl = ref(null);
const ms2PlotEl = ref(null);

const sortState = ref({
  key: null,
  asc: true,
  colIndex: null,
});

const columns = [
  { label: '#', key: '_rowIndex', type: 'number' },
  { label: 'group_ID', key: 'group_ID', type: 'string' },
  { label: 'feature_ID', key: 'feature_ID', type: 'string' },
  { label: 'm/z', key: 'm/z', type: 'number' },
  { label: 'RT', key: 'RT', type: 'number' },
  { label: 'annotation', key: 'annotation', type: 'string' },
  { label: 'formula', key: 'formula', type: 'string' },
  { label: 'similarity', key: 'similarity', type: 'number' },
];

const filterOptions = [
  { label: 'All fields', value: 'all' },
  { label: 'm/z', value: 'm/z' },
  { label: 'RT', value: 'RT' },
  { label: 'annotation', value: 'annotation' },
  { label: 'formula', value: 'formula' },
  { label: 'group_ID', value: 'group_ID' },
  { label: 'feature_ID', value: 'feature_ID' },
  { label: 'similarity', value: 'similarity' },
];

function parseFloatSafe(value) {
  const parsed = parseFloat(value);
  return Number.isNaN(parsed) ? NaN : parsed;
}

function getAnnotation(feature) {
  return feature.annotation || feature['annotation '] || '';
}

function fieldValue(feature, key) {
  if (key === 'annotation') {
    return getAnnotation(feature);
  }
  return feature[key];
}

function compareFeatures(a, b, column) {
  const va = fieldValue(a, column.key);
  const vb = fieldValue(b, column.key);

  if (column.type === 'number') {
    const na = parseFloat(va);
    const nb = parseFloat(vb);
    const av = Number.isNaN(na) ? Number.POSITIVE_INFINITY : na;
    const bv = Number.isNaN(nb) ? Number.POSITIVE_INFINITY : nb;

    if (av < bv) {
      return sortState.value.asc ? -1 : 1;
    }

    if (av > bv) {
      return sortState.value.asc ? 1 : -1;
    }

    return 0;
  }

  const sa = String(va || '').toLowerCase();
  const sb = String(vb || '').toLowerCase();

  if (sa < sb) {
    return sortState.value.asc ? -1 : 1;
  }

  if (sa > sb) {
    return sortState.value.asc ? 1 : -1;
  }

  return 0;
}

function matchesFilter(feature) {
  const query = filterQuery.value.toLowerCase().trim();

  if (!query) {
    return true;
  }

  const annotation = getAnnotation(feature);

  if (filterField.value === 'all') {
    const values = [
      feature['m/z'],
      feature.RT,
      annotation,
      feature.formula,
      feature.group_ID,
      feature.feature_ID,
      feature.similarity,
    ];

    return values.some((value) => value && String(value).toLowerCase().includes(query));
  }

  const selectedValue = filterField.value === 'annotation' ? annotation : feature[filterField.value];
  return selectedValue && String(selectedValue).toLowerCase().includes(query);
}

const filteredFeatures = computed(() => {
  let rows = allFeatures.value.filter((feature) => matchesFilter(feature));

  if (sortState.value.key) {
    const selectedColumn = columns[sortState.value.colIndex];
    if (selectedColumn) {
      rows = [...rows].sort((a, b) => compareFeatures(a, b, selectedColumn));
    }
  }

  return rows;
});

watch(filteredFeatures, (rows) => {
  if (selectedFeature.value && !rows.includes(selectedFeature.value)) {
    selectedFeature.value = null;
  }
});

const hasFeatures = computed(() => filteredFeatures.value.length > 0);

function headerLabel(column, idx) {
  if (sortState.value.colIndex !== idx) {
    return column.label;
  }

  return `${column.label}${sortState.value.asc ? ' ▲' : ' ▼'}`;
}

function toggleSort(column, idx) {
  if (sortState.value.key === column.key && sortState.value.colIndex === idx) {
    sortState.value.asc = !sortState.value.asc;
  } else {
    sortState.value = {
      key: column.key,
      asc: true,
      colIndex: idx,
    };
  }
}

function formatCell(feature, key) {
  if (key === '_rowIndex') {
    return feature._rowIndex + 1;
  }

  if (key === 'annotation') {
    return getAnnotation(feature);
  }

  if (key === 'm/z') {
    const value = parseFloatSafe(feature['m/z']);
    return Number.isFinite(value) ? value.toFixed(4) : '';
  }

  if (key === 'RT') {
    const value = parseFloatSafe(feature.RT);
    return Number.isFinite(value) ? value.toFixed(3) : '';
  }

  if (key === 'similarity') {
    const value = Number(feature.similarity);
    return Number.isFinite(value) ? value.toFixed(4) : '';
  }

  return feature[key] || '';
}

function selectFeature(feature) {
  selectedFeature.value = feature;
}

async function handleFileSelect(event) {
  const file = event.target.files?.[0];
  if (!file) {
    return;
  }

  const text = await file.text();
  parseFeatureTable(text, file.name);
}

function parseFeatureTable(text, filename = '') {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trimEnd())
    .filter((line) => line.length > 0);

  if (lines.length < 2) {
    statusText.value = 'File seems empty or malformed.';
    allFeatures.value = [];
    selectedFeature.value = null;
    return;
  }

  const delimiter = lines[0].includes('\t') ? '\t' : ',';
  const headers = lines[0].split(delimiter);
  const rows = [];

  for (let i = 1; i < lines.length; i += 1) {
    const cells = lines[i].split(delimiter);
    if (cells.length === 1 && cells[0] === '') {
      continue;
    }

    const feature = { _rowIndex: rows.length };
    for (let j = 0; j < headers.length; j += 1) {
      feature[headers[j]] = cells[j] !== undefined ? cells[j] : '';
    }

    rows.push(feature);
  }

  allFeatures.value = rows;
  selectedFeature.value = null;
  sortState.value = { key: null, asc: true, colIndex: null };
  statusText.value = `Loaded ${rows.length} features${filename ? ` from ${filename}` : ''}.`;
}

const similarityLabel = computed(() => {
  const similarity = selectedFeature.value?.similarity;
  const numeric = Number(similarity);

  if (!Number.isFinite(numeric)) {
    return '';
  }

  return `unweighted entropy similarity = ${numeric.toFixed(4)}`;
});

const featureDetails = computed(() => {
  if (!selectedFeature.value) {
    return [];
  }

  const feature = selectedFeature.value;
  const mz = parseFloatSafe(feature['m/z']);
  const rt = parseFloatSafe(feature.RT);

  const rows = [
    ['group_ID', feature.group_ID],
    ['feature_ID', feature.feature_ID],
    ['m/z', Number.isFinite(mz) ? mz.toFixed(4) : feature['m/z']],
    ['RT (min)', Number.isFinite(rt) ? rt.toFixed(3) : feature.RT],
    ['detection rate', feature.detection_rate_gap_filled],
    ['search mode', feature.search_mode],
    ['annotation', getAnnotation(feature)],
    ['unweighted entropy similarity', feature.similarity],
    ['matched peaks', feature.matched_peak_number],
    ['charge', feature.charge],
    ['adduct', feature.adduct],
    ['formula', feature.formula],
    ['Gaussian similarity', feature.Gaussian_similarity],
    ['noise score', feature.noise_score],
    ['asymmetry factor', feature.asymmetry_factor],
    ['alignment reference file', feature.alignment_reference_file],
    ['MS/MS source file', feature.MS2_reference_file],
    ['SMILES', feature.SMILES],
    ['InChIKey', feature.InChIKey],
  ];

  return rows
    .filter(([, value]) => value !== undefined && value !== null && value !== '')
    .map(([label, value]) => ({
      label,
      value,
      isLong:
        label === 'alignment reference file' ||
        label === 'MS/MS source file' ||
        label === 'SMILES' ||
        label === 'InChIKey',
    }));
});

function renderPeakPlot(peakString) {
  if (!peakPlotEl.value) {
    return;
  }

  const rows = parseRtIntensityPairs(peakString);

  if (!rows.length) {
    Plotly.purge(peakPlotEl.value);
    peakNote.value = 'No peak_shape data for this feature.';
    return;
  }

  peakNote.value = '';

  const trace = {
    x: rows.map((row) => row.rt),
    y: rows.map((row) => row.intensity),
    type: 'scatter',
    mode: 'lines',
    line: { color: '#0071e3', width: 2.2 },
    fill: 'tozeroy',
    fillcolor: 'rgba(0, 113, 227, 0.18)',
    name: 'Intensity',
  };

  Plotly.newPlot(
    peakPlotEl.value,
    [trace],
    {
      margin: { l: 70, r: 18, t: 12, b: 58 },
      paper_bgcolor: '#ffffff',
      plot_bgcolor: '#ffffff',
      xaxis: {
        title: {
          text: 'Retention time (min)',
          standoff: 18,
          font: { family: 'Arial, Helvetica, sans-serif', size: 15 },
        },
        tickfont: { family: 'Arial, Helvetica, sans-serif', size: 12 },
        showline: true,
        linecolor: '#0f172a',
        linewidth: 1.6,
        zeroline: false,
        ticks: 'outside',
        ticklen: 5,
      },
      yaxis: {
        title: {
          text: 'Intensity',
          standoff: 10,
          font: { family: 'Arial, Helvetica, sans-serif', size: 15 },
        },
        tickfont: { family: 'Arial, Helvetica, sans-serif', size: 12 },
        showline: true,
        linecolor: '#0f172a',
        linewidth: 1.6,
        ticks: 'outside',
        ticklen: 5,
        rangemode: 'tozero',
        separatethousands: true,
        zeroline: false,
        automargin: true,
      },
    },
    {
      responsive: true,
      displaylogo: false,
    },
  );
}

function renderMs2Plot(ms2AString, ms2BString) {
  if (!ms2PlotEl.value) {
    return;
  }

  const a = parseSpectrum(ms2AString);
  const b = parseSpectrum(ms2BString);

  if (!a.length && !b.length) {
    Plotly.purge(ms2PlotEl.value);
    ms2Note.value = 'No MS/MS data for this feature.';
    return;
  }

  ms2Note.value = '';

  const { top, bottom, maxMz } = normalizeMirrorPeaks(a, b);

  Plotly.newPlot(
    ms2PlotEl.value,
    [
      {
        x: top.x,
        y: top.y,
        mode: 'lines',
        name: 'Experimental MS/MS',
        line: { color: '#0071e3', width: 2 },
      },
      {
        x: bottom.x,
        y: bottom.y,
        mode: 'lines',
        name: 'Matched database MS/MS',
        line: { color: '#dc2626', width: 2 },
      },
    ],
    {
      margin: { l: 70, r: 18, t: 12, b: 58 },
      paper_bgcolor: '#ffffff',
      plot_bgcolor: '#ffffff',
      legend: {
        font: { family: 'Arial, Helvetica, sans-serif', size: 12 },
      },
      xaxis: {
        title: {
          text: 'm/z',
          standoff: 18,
          font: { family: 'Arial, Helvetica, sans-serif', size: 15 },
        },
        tickfont: { family: 'Arial, Helvetica, sans-serif', size: 12 },
        showline: true,
        linecolor: '#0f172a',
        linewidth: 1.6,
        range: [0, maxMz + 10],
      },
      yaxis: {
        title: {
          text: 'Relative intensity',
          standoff: 10,
          font: { family: 'Arial, Helvetica, sans-serif', size: 15 },
        },
        tickfont: { family: 'Arial, Helvetica, sans-serif', size: 12 },
        showline: true,
        linecolor: '#0f172a',
        linewidth: 1.6,
        ticks: 'outside',
        ticklen: 5,
        zeroline: true,
        zerolinecolor: '#94a3b8',
      },
    },
    {
      responsive: true,
      displaylogo: false,
    },
  );
}

watch(
  selectedFeature,
  (feature) => {
    if (!feature) {
      if (peakPlotEl.value) {
        Plotly.purge(peakPlotEl.value);
      }

      if (ms2PlotEl.value) {
        Plotly.purge(ms2PlotEl.value);
      }

      peakNote.value = '';
      ms2Note.value = '';
      return;
    }

    renderPeakPlot(feature.peak_shape);
    renderMs2Plot(feature.MS2, feature.matched_MS2);
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  if (peakPlotEl.value) {
    Plotly.purge(peakPlotEl.value);
  }

  if (ms2PlotEl.value) {
    Plotly.purge(ms2PlotEl.value);
  }
});
</script>

<template>
  <section class="view-shell feature-view">
    <div class="hero-row">
      <div>
        <p class="kicker">Aligned Inspection</p>
        <h1 class="page-title slim">Aligned Feature Table Viewer</h1>
        <p class="page-subtitle narrow">
          Load <code>aligned_feature_table.txt</code>, search and sort instantly, and inspect peak shape plus MS/MS
          evidence for each feature.
        </p>
      </div>
    </div>

    <div class="toolbar panel">
      <div class="panel-body toolbar-body">
        <label class="file-picker" for="feature-file">
          <span class="file-label">Choose aligned table</span>
          <input
            id="feature-file"
            type="file"
            accept=".txt,.tsv,.csv"
            @change="handleFileSelect"
          />
        </label>

        <p class="status-text">{{ statusText }}</p>
      </div>
    </div>

    <div class="workspace-grid">
      <section class="panel table-panel">
        <header class="panel-header">
          <h2 class="panel-title">Features</h2>
          <span class="pill">{{ filteredFeatures.length }} rows</span>
        </header>
        <div class="panel-body table-controls">
          <select v-model="filterField" aria-label="Filter field">
            <option
              v-for="option in filterOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
          <input
            v-model="filterQuery"
            type="text"
            placeholder="Type to search..."
            aria-label="Feature search"
          />
        </div>

        <div class="table-wrap">
          <table aria-label="Aligned feature table">
            <thead>
              <tr>
                <th
                  v-for="(column, idx) in columns"
                  :key="column.key"
                  @click="toggleSort(column, idx)"
                >
                  {{ headerLabel(column, idx) }}
                </th>
              </tr>
            </thead>

            <tbody>
              <tr
                v-for="feature in filteredFeatures"
                :key="feature._rowIndex"
                :class="{ selected: feature === selectedFeature }"
                @click="selectFeature(feature)"
              >
                <td v-for="column in columns" :key="column.key">
                  {{ formatCell(feature, column.key) }}
                </td>
              </tr>

              <tr v-if="!hasFeatures">
                <td colspan="8" class="empty-note">No features to display.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <div class="details-stack">
        <section class="panel">
          <header class="panel-header">
            <h2 class="panel-title">Feature details</h2>
            <span v-if="selectedFeature" class="pill">Feature {{ selectedFeature.feature_ID || '' }}</span>
          </header>

          <div class="panel-body">
            <div v-if="!selectedFeature" class="empty-note">
              Load a table, then click a feature row to inspect metadata and spectra.
            </div>

            <div v-else class="info-grid">
              <div
                v-for="item in featureDetails"
                :key="item.label"
                class="info-item"
                :class="{ long: item.isLong }"
              >
                <p class="info-label">{{ item.label }}</p>
                <p class="info-value">{{ item.value }}</p>
              </div>
            </div>
          </div>
        </section>

        <section class="panel">
          <header class="panel-header">
            <h2 class="panel-title">Peak shape</h2>
          </header>
          <div class="panel-body">
            <div ref="peakPlotEl" class="plot"></div>
            <p v-if="peakNote" class="empty-note">{{ peakNote }}</p>
          </div>
        </section>

        <section class="panel">
          <header class="panel-header">
            <h2 class="panel-title">MS/MS mirror plot</h2>
            <span v-if="similarityLabel" class="sim-label">{{ similarityLabel }}</span>
          </header>
          <div class="panel-body">
            <div ref="ms2PlotEl" class="plot"></div>
            <p v-if="ms2Note" class="empty-note">{{ ms2Note }}</p>
          </div>
        </section>
      </div>
    </div>
  </section>
</template>

<style scoped>
.feature-view {
  display: grid;
  gap: 16px;
}

.slim {
  font-size: clamp(1.8rem, 3.5vw, 2.6rem);
}

.narrow {
  max-width: 78ch;
}

.toolbar-body {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.file-picker {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid var(--line-soft);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.84);
}

.file-label {
  font-size: 0.84rem;
  font-weight: 700;
}

.file-picker input {
  width: auto;
  border: 0;
  padding: 0;
  font-size: 0.8rem;
  background: transparent;
}

.workspace-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: minmax(410px, 560px) minmax(0, 1fr);
  align-items: start;
}

.table-panel {
  min-height: calc(100vh - 170px);
  display: flex;
  flex-direction: column;
}

.table-controls {
  display: flex;
  gap: 8px;
  border-bottom: 1px solid var(--line-soft);
}

.table-controls select {
  max-width: 170px;
  border-radius: 999px;
  padding-block: 8px;
}

.table-controls input {
  border-radius: 999px;
  padding-block: 8px;
}

.table-wrap {
  overflow: auto;
  min-height: 0;
  flex: 1;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
}

thead {
  position: sticky;
  top: 0;
  z-index: 1;
  background: rgba(248, 250, 252, 0.94);
  backdrop-filter: blur(6px);
}

th,
td {
  text-align: left;
  padding: 8px 9px;
  white-space: nowrap;
  border-bottom: 1px solid var(--line-soft);
}

th {
  font-weight: 700;
  color: var(--text-secondary);
  font-size: 0.74rem;
  cursor: pointer;
  user-select: none;
}

tbody tr {
  cursor: pointer;
  transition: background var(--ease);
}

tbody tr:hover {
  background: color-mix(in srgb, var(--accent) 9%, white);
}

tbody tr.selected {
  background: color-mix(in srgb, var(--accent) 16%, white);
}

.details-stack {
  display: grid;
  gap: 12px;
}

.info-grid {
  display: grid;
  gap: 10px 14px;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
}

.info-item {
  display: grid;
  gap: 4px;
}

.info-item.long {
  grid-column: 1 / -1;
}

.info-label {
  margin: 0;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  font-weight: 700;
}

.info-value {
  margin: 0;
  color: var(--text-primary);
  font-size: 0.83rem;
  font-weight: 600;
  line-height: 1.5;
  word-break: break-word;
}

.plot {
  width: 100%;
  min-height: 330px;
}

.sim-label {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--accent-strong);
}

@media (max-width: 1120px) {
  .workspace-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .table-panel {
    min-height: auto;
  }

  .table-wrap {
    max-height: 480px;
  }
}

@media (max-width: 680px) {
  .toolbar-body {
    align-items: stretch;
  }

  .file-picker {
    justify-content: space-between;
    width: 100%;
  }

  .table-controls {
    flex-direction: column;
  }

  .table-controls select {
    max-width: none;
  }
}
</style>
