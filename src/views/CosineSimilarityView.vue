<script setup>
import { onBeforeUnmount, ref } from 'vue';
import Plotly from 'plotly.js-dist-min';
import {
  cosineSimilarityTolerance,
  normalizeMirrorPeaks,
  parseSpectrum,
} from '../utils/spectra';

const specA = ref('');
const specB = ref('');
const tolerance = ref(0.01);
const resultText = ref('');
const notice = ref('');
const plotEl = ref(null);

function loadExample() {
  specA.value =
    '58.064;0.0074|83.0267;0.0032|109.0437;0.299|116.0474;0.0415|129.0673;0.0035|140.0469;0.008|156.0782;0.0085|166.0629;0.0313|190.0622;0.0031|207.0584;0.004|208.0526;0.0049|215.0833;0.0116|218.0575;0.0051|220.0624;0.0129|221.062;0.0336|222.0698;0.0143|227.0711;0.032|233.0721;0.0089|234.0697;0.1016|235.0866;0.0161|236.0843;0.0051|238.0638;0.0096|240.0784;0.0105|241.0872;0.0077|242.094;0.0167|245.0665;0.0065|246.0702;0.0305|247.0774;0.0717|250.1009;0.0099|260.085;0.0073|261.093;0.0086|262.1009;0.1446|280.1118;0.0065|307.1585;0.0143';

  specB.value =
    '58.0649;0.0211|83.029;0.0055|109.0456;0.4104|116.0492;0.0609|121.0455;0.0052|129.0702;0.0045|140.0493;0.0075|144.0448;0.0049|156.0807;0.014|166.0651;0.0353|215.0858;0.0086|218.0603;0.0052|220.0699;0.0063|221.0639;0.0218|222.0714;0.012|227.0732;0.0231|233.0776;0.0064|234.0717;0.0791|235.0944;0.0052|236.0874;0.0052|238.067;0.0081|240.0813;0.0049|241.0895;0.0065|242.0965;0.0161|246.0719;0.0124|247.0794;0.0508|250.1026;0.0081|260.0889;0.006|261.0951;0.0077|262.103;0.1162|280.1133;0.0102|307.1616;0.0107';

  resultText.value = '';
  notice.value = '';

  if (plotEl.value) {
    Plotly.purge(plotEl.value);
  }
}

function makeMirrorPlot(a, b) {
  if (!plotEl.value) {
    return;
  }

  const { top, bottom, maxMz } = normalizeMirrorPeaks(a, b);

  const traceA = {
    x: top.x,
    y: top.y,
    mode: 'lines',
    name: 'Spectrum A',
    line: { width: 2, color: '#0071e3' },
  };

  const traceB = {
    x: bottom.x,
    y: bottom.y,
    mode: 'lines',
    name: 'Spectrum B',
    line: { width: 2, color: '#dc2626' },
  };

  Plotly.newPlot(
    plotEl.value,
    [traceA, traceB],
    {
      margin: { l: 70, r: 20, t: 12, b: 60 },
      paper_bgcolor: '#ffffff',
      plot_bgcolor: '#ffffff',
      legend: {
        orientation: 'h',
        x: 0,
        y: 1.13,
        font: { family: 'Arial, Helvetica, sans-serif', size: 12 },
      },
      xaxis: {
        title: {
          text: 'm/z',
          standoff: 18,
          font: { family: 'Arial, Helvetica, sans-serif', size: 16 },
        },
        tickfont: { family: 'Arial, Helvetica, sans-serif', size: 13 },
        showline: true,
        linecolor: '#0f172a',
        linewidth: 1.7,
        range: [0, maxMz + 10],
      },
      yaxis: {
        title: {
          text: 'Relative intensity',
          standoff: 10,
          font: { family: 'Arial, Helvetica, sans-serif', size: 16 },
        },
        tickfont: { family: 'Arial, Helvetica, sans-serif', size: 13 },
        showline: true,
        linecolor: '#0f172a',
        linewidth: 1.7,
        zeroline: true,
        zerolinecolor: '#94a3b8',
        ticks: 'outside',
        ticklen: 6,
        tickwidth: 1,
        tickcolor: '#0f172a',
        gridcolor: '#e2e8f0',
      },
    },
    {
      responsive: true,
      displaylogo: false,
    },
  );
}

function runAnalysis() {
  const peaksA = parseSpectrum(specA.value);
  const peaksB = parseSpectrum(specB.value);

  if (!peaksA.length || !peaksB.length) {
    notice.value = 'Please provide both spectra in mz;intensity format.';
    resultText.value = '';
    if (plotEl.value) {
      Plotly.purge(plotEl.value);
    }
    return;
  }

  notice.value = '';

  const score = cosineSimilarityTolerance(peaksA, peaksB, Number(tolerance.value) || 0.01);
  resultText.value = `Cosine similarity = ${score.toFixed(4)}`;
  makeMirrorPlot(peaksA, peaksB);
}

onBeforeUnmount(() => {
  if (plotEl.value) {
    Plotly.purge(plotEl.value);
  }
});
</script>

<template>
  <section class="view-shell msms-view">
    <div class="hero-row">
      <div>
        <p class="kicker">Spectral Matching</p>
        <h1 class="page-title slim">MS/MS Viewer</h1>
        <p class="page-subtitle narrow">
          Compare spectra with intensity-priority 1:1 matching under configurable m/z tolerance and inspect results in a
          mirror plot.
        </p>
      </div>
    </div>

    <section class="panel">
      <header class="panel-header controls-header">
        <h2 class="panel-title">Input spectra</h2>
        <div class="controls">
          <label for="tol-input">m/z tolerance (Da)</label>
          <input id="tol-input" v-model.number="tolerance" type="number" step="0.0001" min="0" />
          <button class="btn btn-primary" type="button" @click="runAnalysis">Plot & Compute</button>
          <button class="btn btn-subtle" type="button" @click="loadExample">Load example</button>
        </div>
      </header>
      <div class="panel-body panel-grid">
        <div class="editor-col">
          <label for="spec-a">Spectrum A</label>
          <textarea id="spec-a" v-model="specA" placeholder="mz;intensity|mz;intensity|..." />
        </div>

        <div class="editor-col">
          <label for="spec-b">Spectrum B</label>
          <textarea id="spec-b" v-model="specB" placeholder="mz;intensity|mz;intensity|..." />
        </div>
      </div>
      <div class="panel-foot">
        <p v-if="resultText" class="result">{{ resultText }}</p>
        <p v-if="notice" class="hint warn">{{ notice }}</p>
      </div>
    </section>

    <section class="panel">
      <header class="panel-header">
        <h2 class="panel-title">Mirror plot</h2>
      </header>
      <div class="panel-body">
        <div ref="plotEl" class="plot"></div>
      </div>
    </section>
  </section>
</template>

<style scoped>
.msms-view {
  display: grid;
  gap: 16px;
}

.slim {
  font-size: clamp(1.8rem, 3.5vw, 2.6rem);
}

.narrow {
  max-width: 72ch;
}

.controls-header {
  flex-wrap: wrap;
}

.controls {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 0.82rem;
  color: var(--text-secondary);
}

.controls input {
  width: 120px;
}

.panel-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.editor-col {
  display: grid;
  gap: 6px;
}

label {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-secondary);
}

textarea {
  min-height: 164px;
}

.panel-foot {
  padding: 0 18px 16px;
}

.result {
  margin: 0;
  font-size: 0.94rem;
  font-weight: 700;
  color: var(--accent-strong);
}

.hint {
  margin: 6px 0 0;
  color: var(--text-muted);
  font-size: 0.84rem;
}

.warn {
  color: var(--warning);
}

.plot {
  width: 100%;
  min-height: 520px;
}

@media (max-width: 920px) {
  .panel-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .plot {
    min-height: 430px;
  }
}

@media (max-width: 640px) {
  .controls input {
    width: 100px;
  }
}
</style>
