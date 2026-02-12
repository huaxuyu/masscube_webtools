<script setup>
import { onBeforeUnmount, ref } from 'vue';
import Plotly from 'plotly.js-dist-min';

const apiBaseUrl = ref(import.meta.env.VITE_EIC_API_URL || 'http://127.0.0.1:8000');

const mzmlFile = ref(null);
const fileName = ref('No file selected.');

const targetMzsText = ref('138.0521');
const targetRtText = ref('1.774');
const mzTolText = ref('0.005');
const rtTolText = ref('0.3');
const rtRangeStartText = ref('');
const rtRangeEndText = ref('');
const ylimMinText = ref('');
const ylimMaxText = ref('');
const showTargetRt = ref(true);

const statusText = ref('');
const errorText = ref('');
const isLoading = ref(false);

const chartEl = ref(null);

const palette = ['#0071e3', '#dc2626', '#0f9d6a', '#d97706', '#7c3aed', '#0891b2'];

function parseOptionalNumber(value, fieldLabel) {
  const text = String(value || '').trim();
  if (!text) {
    return null;
  }

  const parsed = Number(text);
  if (!Number.isFinite(parsed)) {
    throw new Error(`${fieldLabel} must be a valid number.`);
  }

  return parsed;
}

function parseMzValues(text) {
  const parts = String(text)
    .split(/[,\s]+/)
    .map((part) => part.trim())
    .filter(Boolean);

  if (!parts.length) {
    throw new Error('Target m/z values are required.');
  }

  const values = parts.map((part) => Number(part));
  if (values.some((value) => !Number.isFinite(value))) {
    throw new Error('Target m/z values must be comma-separated numbers.');
  }

  return values;
}

function parseInputs() {
  const targetMzs = parseMzValues(targetMzsText.value);

  const targetRt = parseOptionalNumber(targetRtText.value, 'Target RT');
  const mzTol = parseOptionalNumber(mzTolText.value, 'm/z tolerance');
  const rtTol = parseOptionalNumber(rtTolText.value, 'RT tolerance');

  if (mzTol === null || mzTol <= 0) {
    throw new Error('m/z tolerance must be a positive number.');
  }

  if (rtTol === null || rtTol <= 0) {
    throw new Error('RT tolerance must be a positive number.');
  }

  const rtRangeStart = parseOptionalNumber(rtRangeStartText.value, 'RT range start');
  const rtRangeEnd = parseOptionalNumber(rtRangeEndText.value, 'RT range end');

  let rtRange = null;
  if (rtRangeStart !== null || rtRangeEnd !== null) {
    if (rtRangeStart === null || rtRangeEnd === null) {
      throw new Error('Provide both RT range start and end values.');
    }

    if (rtRangeStart >= rtRangeEnd) {
      throw new Error('RT range start must be smaller than RT range end.');
    }

    rtRange = [rtRangeStart, rtRangeEnd];
  }

  const ylimMin = parseOptionalNumber(ylimMinText.value, 'Y-axis min');
  const ylimMax = parseOptionalNumber(ylimMaxText.value, 'Y-axis max');

  let ylim = null;
  if (ylimMin !== null || ylimMax !== null) {
    if (ylimMin === null || ylimMax === null) {
      throw new Error('Provide both y-axis min and max values.');
    }

    if (ylimMin >= ylimMax) {
      throw new Error('Y-axis min must be smaller than y-axis max.');
    }

    ylim = [ylimMin, ylimMax];
  }

  return {
    targetMzs,
    targetRt,
    mzTol,
    rtTol,
    rtRange,
    ylim,
    showTargetRt: showTargetRt.value,
  };
}

function toFormValue(value) {
  return value === null || value === undefined ? '' : String(value);
}

function renderEicPlot(traces, targetRtValue, shouldShowTargetRt) {
  if (!chartEl.value) {
    return;
  }

  if (!Array.isArray(traces) || traces.length === 0) {
    Plotly.purge(chartEl.value);
    return;
  }

  const series = traces.map((trace, idx) => ({
    x: trace.time,
    y: trace.intensity,
    type: 'scatter',
    mode: 'lines',
    name: trace.label || `Trace ${idx + 1}`,
    line: {
      width: 2,
      color: palette[idx % palette.length],
    },
  }));

  const layout = {
    margin: { l: 72, r: 22, t: 20, b: 62 },
    paper_bgcolor: '#ffffff',
    plot_bgcolor: '#ffffff',
    legend: {
      orientation: 'h',
      y: 1.12,
      x: 0,
      font: { family: 'Arial, Helvetica, sans-serif', size: 12 },
    },
    xaxis: {
      title: {
        text: 'Retention time (min)',
        standoff: 16,
        font: { family: 'Arial, Helvetica, sans-serif', size: 16 },
      },
      tickfont: { family: 'Arial, Helvetica, sans-serif', size: 13 },
      showline: true,
      linecolor: '#0f172a',
      linewidth: 1.7,
      ticks: 'outside',
      ticklen: 6,
      tickwidth: 1,
      tickcolor: '#0f172a',
      zeroline: false,
    },
    yaxis: {
      title: {
        text: 'Intensity',
        standoff: 10,
        font: { family: 'Arial, Helvetica, sans-serif', size: 16 },
      },
      tickfont: { family: 'Arial, Helvetica, sans-serif', size: 13 },
      showline: true,
      linecolor: '#0f172a',
      linewidth: 1.7,
      ticks: 'outside',
      ticklen: 6,
      tickwidth: 1,
      tickcolor: '#0f172a',
      rangemode: 'tozero',
      separatethousands: true,
      automargin: true,
      zeroline: false,
    },
    shapes:
      shouldShowTargetRt && Number.isFinite(targetRtValue)
        ? [
            {
              type: 'line',
              x0: targetRtValue,
              x1: targetRtValue,
              y0: 0,
              y1: 1,
              yref: 'paper',
              line: {
                color: '#1d4ed8',
                width: 1.8,
                dash: 'dash',
              },
            },
          ]
        : [],
  };

  Plotly.newPlot(chartEl.value, series, layout, {
    responsive: true,
    displaylogo: false,
  });
}

function handleFileChange(event) {
  const selected = event.target.files?.[0] || null;
  mzmlFile.value = selected;
  fileName.value = selected ? selected.name : 'No file selected.';
}

async function extractEics() {
  errorText.value = '';
  statusText.value = '';

  if (!mzmlFile.value) {
    errorText.value = 'Select an mzML file first.';
    return;
  }

  let parsed;
  try {
    parsed = parseInputs();
  } catch (error) {
    errorText.value = error instanceof Error ? error.message : 'Invalid parameters.';
    return;
  }

  const formData = new FormData();
  formData.append('file', mzmlFile.value);
  formData.append('target_mz_arr', parsed.targetMzs.join(','));
  formData.append('target_rt', toFormValue(parsed.targetRt));
  formData.append('mz_tol', String(parsed.mzTol));
  formData.append('rt_tol', String(parsed.rtTol));
  formData.append('rt_range_start', toFormValue(parsed.rtRange?.[0]));
  formData.append('rt_range_end', toFormValue(parsed.rtRange?.[1]));
  formData.append('ylim_min', toFormValue(parsed.ylim?.[0]));
  formData.append('ylim_max', toFormValue(parsed.ylim?.[1]));
  formData.append('show_target_rt', String(parsed.showTargetRt));

  const endpoint = `${apiBaseUrl.value.replace(/\/$/, '')}/api/eic`;

  isLoading.value = true;
  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      body: formData,
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(data.detail || `Backend request failed with status ${response.status}.`);
    }

    if (!data.traces || !Array.isArray(data.traces) || data.traces.length === 0) {
      throw new Error('No EIC traces were returned from the backend.');
    }

    renderEicPlot(data.traces, parsed.targetRt, parsed.showTargetRt);
    statusText.value = `Loaded ${data.traces.length} EIC trace(s) with ${data.total_points || 0} total points.`;
  } catch (error) {
    errorText.value = error instanceof Error ? error.message : 'Unable to extract EIC data.';
    if (chartEl.value) {
      Plotly.purge(chartEl.value);
    }
  } finally {
    isLoading.value = false;
  }
}

onBeforeUnmount(() => {
  if (chartEl.value) {
    Plotly.purge(chartEl.value);
  }
});
</script>

<template>
  <section class="view-shell eic-view">
    <div class="hero-row">
      <div>
        <p class="kicker">Raw Data Inspection</p>
        <h1 class="page-title slim">mzML EIC Viewer</h1>
        <p class="page-subtitle narrow">
          Upload an mzML file and extract EIC traces through a MassCube Python backend service.
        </p>
      </div>
    </div>

    <div class="layout-grid">
      <section class="panel">
        <header class="panel-header">
          <h2 class="panel-title">Parameters</h2>
          <span class="pill">MassCube backend required</span>
        </header>

        <div class="panel-body form-stack">
          <div class="field-block">
            <label for="backend-url">Backend URL</label>
            <input
              id="backend-url"
              v-model="apiBaseUrl"
              type="text"
              placeholder="http://127.0.0.1:8000"
            />
          </div>

          <div class="field-block">
            <label for="mzml-file">mzML file</label>
            <input id="mzml-file" type="file" accept=".mzML,.mzml" @change="handleFileChange" />
            <p class="field-note">{{ fileName }}</p>
          </div>

          <div class="form-grid">
            <div class="field-block full-width">
              <label for="target-mz">Target m/z values</label>
              <input id="target-mz" v-model="targetMzsText" type="text" placeholder="138.0521, 150.1234" />
              <p class="field-note">Use comma-separated values for overlapping EICs.</p>
            </div>

            <div class="field-block">
              <label for="target-rt">Target RT (min)</label>
              <input id="target-rt" v-model="targetRtText" type="text" placeholder="1.774" />
            </div>

            <div class="field-block">
              <label for="mz-tol">m/z tolerance (Da)</label>
              <input id="mz-tol" v-model="mzTolText" type="text" placeholder="0.005" />
            </div>

            <div class="field-block">
              <label for="rt-tol">RT tolerance (min)</label>
              <input id="rt-tol" v-model="rtTolText" type="text" placeholder="0.3" />
            </div>

            <div class="field-block">
              <label for="rt-start">RT range start (min)</label>
              <input id="rt-start" v-model="rtRangeStartText" type="text" placeholder="optional" />
            </div>

            <div class="field-block">
              <label for="rt-end">RT range end (min)</label>
              <input id="rt-end" v-model="rtRangeEndText" type="text" placeholder="optional" />
            </div>

            <div class="field-block">
              <label for="ylim-min">Y-axis min</label>
              <input id="ylim-min" v-model="ylimMinText" type="text" placeholder="optional" />
            </div>

            <div class="field-block">
              <label for="ylim-max">Y-axis max</label>
              <input id="ylim-max" v-model="ylimMaxText" type="text" placeholder="optional" />
            </div>
          </div>

          <label class="checkbox-row">
            <input v-model="showTargetRt" type="checkbox" />
            <span>Show dashed line at target RT</span>
          </label>

          <div class="action-row">
            <button class="btn btn-primary" type="button" :disabled="isLoading" @click="extractEics">
              {{ isLoading ? 'Extracting...' : 'Extract and Plot EICs' }}
            </button>
          </div>

          <p v-if="statusText" class="status-ok">{{ statusText }}</p>
          <p v-if="errorText" class="status-error">{{ errorText }}</p>
        </div>
      </section>

      <section class="panel">
        <header class="panel-header">
          <h2 class="panel-title">EIC plot</h2>
        </header>
        <div class="panel-body">
          <div ref="chartEl" class="plot"></div>
          <p class="empty-note">If the panel stays blank, check that the backend is running and parameters are valid.</p>
        </div>
      </section>
    </div>
  </section>
</template>

<style scoped>
.eic-view {
  display: grid;
  gap: 16px;
}

.slim {
  font-size: clamp(1.8rem, 3.5vw, 2.6rem);
}

.narrow {
  max-width: 72ch;
}

.layout-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: minmax(320px, 520px) minmax(0, 1fr);
  align-items: start;
}

.form-stack {
  display: grid;
  gap: 14px;
}

.form-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.field-block {
  display: grid;
  gap: 6px;
}

.field-block.full-width {
  grid-column: 1 / -1;
}

label {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-secondary);
}

.field-note {
  margin: 0;
  font-size: 0.78rem;
  color: var(--text-muted);
}

.checkbox-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-row input {
  width: 16px;
  height: 16px;
}

.action-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.status-ok {
  margin: 0;
  color: var(--success);
  font-size: 0.86rem;
  font-weight: 600;
}

.status-error {
  margin: 0;
  color: var(--danger);
  font-size: 0.86rem;
  font-weight: 600;
}

.plot {
  width: 100%;
  min-height: 560px;
}

@media (max-width: 1100px) {
  .layout-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 700px) {
  .form-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .plot {
    min-height: 420px;
  }
}
</style>
