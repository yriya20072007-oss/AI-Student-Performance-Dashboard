// static/js/data_table.js
// Handles search, filter, sort, and pagination for the Data Explorer table via /api/data.

document.addEventListener('DOMContentLoaded', function() {
  const tableBody = document.getElementById('tableBody');
  if (!tableBody) return;

  const searchInput = document.getElementById('searchInput');
  const genderFilter = document.getElementById('genderFilter');
  const tutoringFilter = document.getElementById('tutoringFilter');
  const supportFilter = document.getElementById('supportFilter');
  const pageSizeSelect = document.getElementById('pageSizeSelect');
  const resetFiltersBtn = document.getElementById('resetFiltersBtn');

  const paginationInfo = document.getElementById('paginationInfo');
  const pageIndicator = document.getElementById('pageIndicator');
  const firstPageBtn = document.getElementById('firstPageBtn');
  const prevPageBtn = document.getElementById('prevPageBtn');
  const nextPageBtn = document.getElementById('nextPageBtn');
  const lastPageBtn = document.getElementById('lastPageBtn');

  // State variables
  let currentPage = 1;
  let totalPages = 1;
  let sortBy = 'StudentID';
  let sortDir = 'asc';
  let debounceTimer = null;

  const gradeNames = ['A', 'B', 'C', 'D', 'F'];
  const ethnicityNames = ['Caucasian', 'African Am.', 'Asian', 'Other'];
  const parentEduNames = ['None', 'High School', 'Some College', "Bachelor's", 'Higher'];
  const supportNames = ['None', 'Low', 'Moderate', 'High', 'Very High'];

  function fetchAndRenderData() {
    const params = new URLSearchParams({
      page: currentPage,
      page_size: pageSizeSelect.value,
      sort_by: sortBy,
      sort_dir: sortDir,
      search: searchInput.value.trim(),
      gender: genderFilter.value,
      tutoring: tutoringFilter.value,
      parental_support: supportFilter.value
    });

    tableBody.innerHTML = '<tr><td colspan="15" style="text-align: center; padding: 20px; color: var(--color-text-muted);">Loading student records...</td></tr>';

    fetch(`/api/data?${params.toString()}`)
      .then(res => res.json())
      .then(res => {
        totalPages = res.total_pages;
        currentPage = res.page;
        renderRows(res.data);
        renderPagination(res.total, res.page, res.page_size, res.total_pages);
      })
      .catch(err => {
        console.error('Data load error:', err);
        tableBody.innerHTML = '<tr><td colspan="15" style="text-align: center; padding: 20px; color: var(--color-danger);">Failed to load data. Please refresh.</td></tr>';
      });
  }

  function renderRows(records) {
    if (!records || records.length === 0) {
      tableBody.innerHTML = '<tr><td colspan="15" style="text-align: center; padding: 24px; color: var(--color-text-muted);">No student records match the selected filters.</td></tr>';
      return;
    }

    let html = '';
    records.forEach(r => {
      const gClass = parseInt(r.GradeClass, 10);
      const gLetter = gradeNames[gClass] || '?';
      const badgeClass = `grade-badge-${gClass}`;

      html += `
        <tr>
          <td><strong>${r.StudentID}</strong></td>
          <td>${r.Age}</td>
          <td>${r.Gender === 1 ? 'Male' : 'Female'}</td>
          <td>${ethnicityNames[r.Ethnicity] || r.Ethnicity}</td>
          <td>${parentEduNames[r.ParentalEducation] || r.ParentalEducation}</td>
          <td>${Number(r.StudyTimeWeekly).toFixed(1)}</td>
          <td>${r.Absences}</td>
          <td>${r.Tutoring === 1 ? 'Yes' : 'No'}</td>
          <td>${supportNames[r.ParentalSupport] || r.ParentalSupport}</td>
          <td>${r.Extracurricular === 1 ? 'Yes' : 'No'}</td>
          <td>${r.Sports === 1 ? 'Yes' : 'No'}</td>
          <td>${r.Music === 1 ? 'Yes' : 'No'}</td>
          <td>${r.Volunteering === 1 ? 'Yes' : 'No'}</td>
          <td><strong>${Number(r.GPA).toFixed(2)}</strong></td>
          <td><span class="grade-badge ${badgeClass}">${gLetter} (${gClass})</span></td>
        </tr>
      `;
    });

    tableBody.innerHTML = html;
  }

  function renderPagination(total, page, pageSize, totalPagesCount) {
    const start = total === 0 ? 0 : (page - 1) * pageSize + 1;
    const end = Math.min(page * pageSize, total);
    paginationInfo.textContent = `Showing ${start} to ${end} of ${total} entries`;
    pageIndicator.textContent = `Page ${page} of ${totalPagesCount}`;

    firstPageBtn.disabled = (page <= 1);
    prevPageBtn.disabled = (page <= 1);
    nextPageBtn.disabled = (page >= totalPagesCount);
    lastPageBtn.disabled = (page >= totalPagesCount);
  }

  // Sorting header clicks
  document.querySelectorAll('#dataTable th.sortable').forEach(th => {
    th.addEventListener('click', function() {
      const col = this.getAttribute('data-col');
      if (sortBy === col) {
        sortDir = (sortDir === 'asc') ? 'desc' : 'asc';
      } else {
        sortBy = col;
        sortDir = 'asc';
      }

      // Update header indicators
      document.querySelectorAll('#dataTable th.sortable').forEach(header => {
        const iconSpan = header.querySelector('.sort-icon');
        if (header.getAttribute('data-col') === sortBy) {
          iconSpan.textContent = sortDir === 'asc' ? ' ▲' : ' ▼';
        } else {
          iconSpan.textContent = '';
        }
      });

      currentPage = 1;
      fetchAndRenderData();
    });
  });

  // Filter change handlers
  genderFilter.addEventListener('change', () => { currentPage = 1; fetchAndRenderData(); });
  tutoringFilter.addEventListener('change', () => { currentPage = 1; fetchAndRenderData(); });
  supportFilter.addEventListener('change', () => { currentPage = 1; fetchAndRenderData(); });
  pageSizeSelect.addEventListener('change', () => { currentPage = 1; fetchAndRenderData(); });

  // Debounced search input
  searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      currentPage = 1;
      fetchAndRenderData();
    }, 250);
  });

  // Reset filters button
  resetFiltersBtn.addEventListener('click', () => {
    searchInput.value = '';
    genderFilter.value = '';
    tutoringFilter.value = '';
    supportFilter.value = '';
    pageSizeSelect.value = '25';
    sortBy = 'StudentID';
    sortDir = 'asc';
    currentPage = 1;

    document.querySelectorAll('#dataTable th.sortable .sort-icon').forEach(s => s.textContent = '');
    fetchAndRenderData();
  });

  // Pagination navigation buttons
  firstPageBtn.addEventListener('click', () => {
    if (currentPage > 1) { currentPage = 1; fetchAndRenderData(); }
  });

  prevPageBtn.addEventListener('click', () => {
    if (currentPage > 1) { currentPage--; fetchAndRenderData(); }
  });

  nextPageBtn.addEventListener('click', () => {
    if (currentPage < totalPages) { currentPage++; fetchAndRenderData(); }
  });

  lastPageBtn.addEventListener('click', () => {
    if (currentPage < totalPages) { currentPage = totalPages; fetchAndRenderData(); }
  });

  // Initial load
  fetchAndRenderData();
});
