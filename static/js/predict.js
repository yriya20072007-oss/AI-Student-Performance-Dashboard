// static/js/predict.js
// Handles student prediction form validation, sample presets, AJAX classification, and probability bars.

document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('predictionForm');
  if (!form) return;

  const formAlert = document.getElementById('formAlert');
  const formAlertText = document.getElementById('formAlertText');
  const submitBtn = document.getElementById('submitBtn');
  const resultContainer = document.getElementById('predictionResult');
  const resultGradeText = document.getElementById('resultGradeText');
  const resultDescText = document.getElementById('resultDescText');
  const resultConfidenceText = document.getElementById('resultConfidenceText');
  const probList = document.getElementById('probList');

  // Input elements
  const inputs = {
    Age: document.getElementById('inputAge'),
    Gender: document.getElementById('inputGender'),
    Ethnicity: document.getElementById('inputEthnicity'),
    ParentalEducation: document.getElementById('inputParentalEducation'),
    StudyTimeWeekly: document.getElementById('inputStudyTimeWeekly'),
    Absences: document.getElementById('inputAbsences'),
    Tutoring: document.getElementById('inputTutoring'),
    ParentalSupport: document.getElementById('inputParentalSupport'),
    Extracurricular: document.getElementById('inputExtracurricular'),
    Sports: document.getElementById('inputSports'),
    Music: document.getElementById('inputMusic'),
    Volunteering: document.getElementById('inputVolunteering'),
  };

  // Sample presets for quick student evaluation
  const presets = {
    high: {
      Age: '17', Gender: '1', Ethnicity: '0', ParentalEducation: '3',
      StudyTimeWeekly: '18.5', Absences: '2', Tutoring: '1', ParentalSupport: '3',
      Extracurricular: '1', Sports: '1', Music: '1', Volunteering: '1'
    },
    avg: {
      Age: '16', Gender: '0', Ethnicity: '1', ParentalEducation: '2',
      StudyTimeWeekly: '9.5', Absences: '12', Tutoring: '0', ParentalSupport: '2',
      Extracurricular: '0', Sports: '0', Music: '0', Volunteering: '0'
    },
    risk: {
      Age: '18', Gender: '1', Ethnicity: '0', ParentalEducation: '1',
      StudyTimeWeekly: '2.5', Absences: '26', Tutoring: '0', ParentalSupport: '1',
      Extracurricular: '0', Sports: '0', Music: '0', Volunteering: '0'
    }
  };

  function applyPreset(presetData) {
    clearErrors();
    for (const [key, val] of Object.entries(presetData)) {
      if (inputs[key]) {
        inputs[key].value = val;
      }
    }
  }

  document.getElementById('presetHigh')?.addEventListener('click', () => applyPreset(presets.high));
  document.getElementById('presetAvg')?.addEventListener('click', () => applyPreset(presets.avg));
  document.getElementById('presetRisk')?.addEventListener('click', () => applyPreset(presets.risk));

  document.getElementById('presetClear')?.addEventListener('click', () => {
    form.reset();
    clearErrors();
    resultContainer.classList.remove('visible');
  });

  function clearErrors() {
    formAlert.style.display = 'none';
    for (const key of Object.keys(inputs)) {
      const group = document.getElementById(`group-${key}`);
      const errEl = document.getElementById(`error-${key}`);
      if (group) group.classList.remove('has-error');
      if (errEl) errEl.textContent = '';
    }
  }

  function showErrors(errors) {
    let firstErrorGroup = null;
    for (const [field, msg] of Object.entries(errors)) {
      const group = document.getElementById(`group-${field}`);
      const errEl = document.getElementById(`error-${field}`);
      if (group) {
        group.classList.add('has-error');
        if (!firstErrorGroup) firstErrorGroup = group;
      }
      if (errEl) {
        errEl.textContent = msg;
      }
    }

    formAlertText.textContent = Object.values(errors)[0] || 'Please correct the highlighted inputs.';
    formAlert.style.display = 'flex';

    if (firstErrorGroup) {
      firstErrorGroup.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  function renderPredictionResult(res) {
    resultGradeText.textContent = res.grade_label;
    resultDescText.textContent = res.description;
    resultConfidenceText.textContent = `${res.confidence}%`;

    // Render probability distribution bars
    let html = '';
    res.probabilities.forEach(p => {
      const isPredictedClass = p.is_predicted ? 'is-predicted' : '';
      html += `
        <div class="prob-item ${isPredictedClass}">
          <div class="prob-name">${p.label}</div>
          <div class="prob-bar-container">
            <div class="prob-bar-fill" style="width: ${p.probability}%;"></div>
          </div>
          <div class="prob-pct">${p.probability}%</div>
        </div>
      `;
    });
    probList.innerHTML = html;

    resultContainer.classList.add('visible');
    resultContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // Handle form submission
  form.addEventListener('submit', function(e) {
    e.preventDefault();
    clearErrors();

    // Client-side quick check
    const clientErrors = {};
    for (const [key, el] of Object.entries(inputs)) {
      if (!el.value || el.value.trim() === '') {
        clientErrors[key] = 'This field is required.';
      }
    }

    // Numerical range checks
    const studyVal = parseFloat(inputs.StudyTimeWeekly.value);
    if (!isNaN(studyVal) && (studyVal < 0 || studyVal > 20)) {
      clientErrors['StudyTimeWeekly'] = 'Weekly study time must be between 0.0 and 20.0 hours.';
    }

    const absVal = parseInt(inputs.Absences.value, 10);
    if (!isNaN(absVal) && (absVal < 0 || absVal > 30)) {
      clientErrors['Absences'] = 'Absences must be between 0 and 30 days.';
    }

    if (Object.keys(clientErrors).length > 0) {
      showErrors(clientErrors);
      return;
    }

    // Collect payload
    const payload = {};
    for (const [key, el] of Object.entries(inputs)) {
      payload[key] = el.value.trim();
    }

    // Submit to API
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span>Classifying...</span>';

    fetch('/api/predict', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    })
      .then(async res => {
        const data = await res.json();
        if (!res.ok) {
          throw data.errors || { general: 'Prediction request failed.' };
        }
        return data;
      })
      .then(data => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span>Run Classification</span>';
        renderPredictionResult(data.result);
      })
      .catch(errors => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span>Run Classification</span>';
        if (typeof errors === 'object') {
          showErrors(errors);
        } else {
          showErrors({ general: String(errors) });
        }
      });
  });
});
