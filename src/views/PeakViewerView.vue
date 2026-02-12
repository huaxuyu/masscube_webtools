<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue';
import Plotly from 'plotly.js-dist-min';
import { parseRtIntensityPairs, toPeakCsv } from '../utils/peak';

const inputText = ref(`1.476;1616.0|1.482;4424.0|1.487;17358.0|1.493;56188.0|1.498;136646.0|1.504;167521.0|1.509;160536.0|1.515;102560.0|1.52;58320.0|1.525;21360.0|1.531;6971.0|1.537;2735.0|1.542;1732.0|1.548;1111.0|`);

const chartEl = ref(null);
const notice = ref('');

function plotPeak() {
  const rows = parseRtIntensityPairs(inputText.value);

  if (!rows.length || !chartEl.value) {
    notice.value = 'No valid points found. Keep the format as rt;intensity|rt;intensity|...';
    if (chartEl.value) {
      Plotly.purge(chartEl.value);
    }
    return;
  }

  notice.value = '';

  const trace = {
    x: rows.map((row) => row.rt),
    y: rows.map((row) => row.intensity),
    type: 'scatter',
    mode: 'lines',
    line: {
      width: 2.4,
      color: '#0071e3',
    },
    fill: 'tozeroy',
    fillcolor: 'rgba(0, 113, 227, 0.18)',
    name: 'Intensity',
  };

  const layout = {
    margin: { l: 70, r: 20, t: 10, b: 60 },
    paper_bgcolor: '#ffffff',
    plot_bgcolor: '#ffffff',
    xaxis: {
      title: {
        text: 'Retention time (min)',
        standoff: 22,
        font: { family: 'Arial, Helvetica, sans-serif', size: 16 },
      },
      tickfont: { family: 'Arial, Helvetica, sans-serif', size: 13 },
      showline: true,
      linecolor: '#0f172a',
      linewidth: 1.7,
      zeroline: false,
      ticks: 'outside',
      ticklen: 6,
      tickwidth: 1,
      tickcolor: '#0f172a',
    },
    yaxis: {
      title: {
        text: 'Intensity',
        standoff: 12,
        font: { family: 'Arial, Helvetica, sans-serif', size: 16 },
      },
      tickfont: { family: 'Arial, Helvetica, sans-serif', size: 13 },
      showline: true,
      linecolor: '#0f172a',
      linewidth: 1.7,
      zeroline: false,
      ticks: 'outside',
      ticklen: 6,
      tickwidth: 1,
      tickcolor: '#0f172a',
      rangemode: 'tozero',
      separatethousands: true,
      automargin: true,
    },
  };

  Plotly.newPlot(chartEl.value, [trace], layout, {
    responsive: true,
    displaylogo: false,
  });
}

async function downloadPng() {
  if (!chartEl.value) {
    return;
  }

  const imageUrl = await Plotly.toImage(chartEl.value, {
    format: 'png',
    scale: 2,
    width: 1280,
    height: 720,
  });

  const a = document.createElement('a');
  a.href = imageUrl;
  a.download = 'peak_shape.png';
  a.click();
}

function downloadCsv() {
  const rows = parseRtIntensityPairs(inputText.value);
  if (!rows.length) {
    notice.value = 'CSV export is available after valid points are entered.';
    return;
  }

  const csv = toPeakCsv(rows);
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);

  const a = document.createElement('a');
  a.href = url;
  a.download = 'peak_shape.csv';
  a.click();

  URL.revokeObjectURL(url);
}

function onInputKeyDown(event) {
  if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
    plotPeak();
  }
}

onMounted(() => {
  plotPeak();
});

onBeforeUnmount(() => {
  if (chartEl.value) {
    Plotly.purge(chartEl.value);
  }
});
</script>

<template>
  <section class="view-shell peak-view">
    <div class="hero-row">
      <div>
        <p class="kicker">Peak QC</p>
        <h1 class="page-title slim">Peak Shape Viewer</h1>
        <p class="page-subtitle narrow">
          Paste RT-intensity pairs in <code>rt;intensity</code> format, create a clean area plot, then export as PNG or CSV.
        </p>
      </div>
    </div>

    <div class="content-grid">
      <section class="panel">
        <header class="panel-header">
          <h2 class="panel-title">Input</h2>
          <span class="pill">Cmd/Ctrl + Enter to plot</span>
        </header>
        <div class="panel-body input-body">
          <textarea
            v-model="inputText"
            aria-label="Peak shape input"
            @keydown="onInputKeyDown"
            placeholder="rt;intensity|rt;intensity|..."
          />

          <div class="actions">
            <button class="btn btn-primary" type="button" @click="plotPeak">Plot</button>
            <button class="btn btn-subtle" type="button" @click="downloadPng">Download PNG</button>
            <button class="btn btn-subtle" type="button" @click="downloadCsv">Download CSV</button>
          </div>
          <p v-if="notice" class="hint warn">{{ notice }}</p>
          <p class="hint">Non-numeric pairs are ignored automatically.</p>
        </div>
      </section>

      <section class="panel">
        <header class="panel-header">
          <h2 class="panel-title">RT vs Intensity</h2>
        </header>
        <div class="panel-body">
          <div ref="chartEl" class="plot"></div>
        </div>
      </section>
    </div>
  </section>
</template>

<style scoped>
.peak-view {
  display: grid;
  gap: 16px;
}

.slim {
  font-size: clamp(1.8rem, 3.5vw, 2.6rem);
}

.narrow {
  max-width: 72ch;
}

.content-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: minmax(300px, 440px) minmax(0, 1fr);
}

.input-body {
  display: grid;
  gap: 12px;
}

textarea {
  min-height: 220px;
}

.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.hint {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.84rem;
}

.warn {
  color: var(--warning);
}

.plot {
  width: 100%;
  min-height: 470px;
}

@media (max-width: 980px) {
  .content-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .plot {
    min-height: 400px;
  }
}
</style>
