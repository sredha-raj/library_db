document.addEventListener('DOMContentLoaded', () => {
  // Modal handlers
  window.openModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('active');
      document.body.style.overflow = 'hidden';
    }
  };

  window.closeModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('active');
      document.body.style.overflow = '';
    }
  };

  // Close modals on clicking outside or escape key
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        overlay.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay.active').forEach(modal => {
        modal.classList.remove('active');
      });
      document.body.style.overflow = '';
    }
  });

  // Tab switching
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-tab');
      if (!targetTab) return; // allows link tabs
      const parentContainer = btn.closest('.tabs-container') || document;
      
      parentContainer.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      parentContainer.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const pane = document.getElementById(targetTab);
      if (pane) pane.classList.add('active');
    });
  });

  // Auto-dismiss alerts after 5 seconds
  setTimeout(() => {
    document.querySelectorAll('.flash-message').forEach(el => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(-10px)';
      el.style.transition = 'all 0.4s ease';
      setTimeout(() => el.remove(), 400);
    });
  }, 5000);

  // Return modal fine calculation helper in Indian Rupees (₹)
  window.prepareReturnModal = function(borrowId, memberName, bookTitle, copyId, dueDateStr) {
    const borrowIdInput = document.getElementById('returnBorrowId');
    const returnInfo = document.getElementById('returnModalInfo');
    const returnDateInput = document.getElementById('returnDateInput');
    const fineInput = document.getElementById('fineAmountInput');
    const fineNote = document.getElementById('fineCalculationNote');

    if (borrowIdInput) borrowIdInput.value = borrowId;
    if (returnInfo) {
      returnInfo.innerHTML = `<strong>${bookTitle}</strong> (Copy #${copyId}) borrowed by <strong>${memberName}</strong>. Due: <em>${dueDateStr}</em>`;
    }

    const todayStr = new Date().toISOString().split('T')[0];
    if (returnDateInput) {
      returnDateInput.value = todayStr;
      
      const calcFine = () => {
        const retDate = new Date(returnDateInput.value);
        const dueDate = new Date(dueDateStr);
        const diffDays = Math.ceil((retDate - dueDate) / (1000 * 60 * 60 * 24));
        if (diffDays > 0) {
          const fine = (diffDays * 5.0).toFixed(2);
          fineInput.value = fine;
          fineNote.textContent = `${diffDays} day(s) overdue @ ₹5.00/day = ₹${fine}`;
          fineNote.style.color = '#fb7185';
        } else {
          fineInput.value = '0.00';
          fineNote.textContent = 'Returned on or before due date. No late fine applied (₹0.00).';
          fineNote.style.color = '#34d399';
        }
      };

      returnDateInput.addEventListener('change', calcFine);
      calcFine();
    }

    openModal('returnBookModal');
  };

  // Category Edit Modal Helper
  window.openEditCategoryModal = function(catId, catName) {
    const form = document.getElementById('editCategoryForm');
    const input = document.getElementById('editCategoryName');
    if (form && input) {
      form.action = `/metadata/category/${catId}/edit`;
      input.value = catName;
      openModal('editCategoryModal');
    }
  };

  // Publisher Edit Modal Helper
  window.openEditPublisherModal = function(pubId, name, address, phone) {
    const form = document.getElementById('editPublisherForm');
    if (form) {
      form.action = `/metadata/publisher/${pubId}/edit`;
      document.getElementById('editPublisherName').value = name;
      document.getElementById('editPublisherAddress').value = address || '';
      document.getElementById('editPublisherPhone').value = phone || '';
      openModal('editPublisherModal');
    }
  };

  // Author Edit Modal Helper
  window.openEditAuthorModal = function(authorId, name, nationality) {
    const form = document.getElementById('editAuthorForm');
    if (form) {
      form.action = `/metadata/author/${authorId}/edit`;
      document.getElementById('editAuthorName').value = name;
      document.getElementById('editAuthorNationality').value = nationality || '';
      openModal('editAuthorModal');
    }
  };

  // SQL Runner Console execution
  const runQueryBtn = document.getElementById('btnRunQuery');
  const sqlEditor = document.getElementById('sqlQueryInput');
  const queryResultsBox = document.getElementById('queryResultsBox');

  if (runQueryBtn && sqlEditor && queryResultsBox) {
    runQueryBtn.addEventListener('click', async () => {
      const sql = sqlEditor.value.trim();
      if (!sql) return;

      runQueryBtn.disabled = true;
      runQueryBtn.textContent = 'Executing...';
      queryResultsBox.innerHTML = '<div style="padding: 20px; color: var(--text-muted);"><span class="db-dot" style="display:inline-block; margin-right:8px;"></span>Running SQL query against SQLite3 database...</div>';

      try {
        const resp = await fetch('/api/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: sql })
        });
        const data = await resp.json();

        if (data.error) {
          queryResultsBox.innerHTML = `
            <div style="padding: 18px; color: #fb7185; background: rgba(244, 63, 94, 0.1); border-radius: 8px;">
              <strong>SQL Error:</strong> ${data.error}
            </div>
          `;
        } else {
          let html = `
            <div style="margin-bottom: 12px; font-size: 0.82rem; color: var(--accent-emerald);">
              Query executed successfully. Returned <strong>${data.count}</strong> row(s).
            </div>
            <div class="table-responsive">
              <table class="data-table">
                <thead>
                  <tr>
                    ${data.headers.map(h => `<th>${h}</th>`).join('')}
                  </tr>
                </thead>
                <tbody>
                  ${data.rows.map(row => `
                    <tr>
                      ${row.map(val => `<td>${val !== null ? val : '<span style="color:var(--text-dim)">NULL</span>'}</td>`).join('')}
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          `;
          queryResultsBox.innerHTML = html;
        }
      } catch (err) {
        queryResultsBox.innerHTML = `<div style="padding: 18px; color: #fb7185;">Network or execution error: ${err.message}</div>`;
      } finally {
        runQueryBtn.disabled = false;
        runQueryBtn.textContent = 'Run SQL';
      }
    });

    // Sample query chips
    document.querySelectorAll('.query-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        sqlEditor.value = chip.getAttribute('data-sql');
        runQueryBtn.click();
      });
    });
  }

  // Database Reset / Re-seed Button
  const btnResetDb = document.getElementById('btnResetDatabase');
  if (btnResetDb) {
    btnResetDb.addEventListener('click', async () => {
      if (!confirm('Are you sure you want to reset all tables and re-seed clean Indian library demonstration data?')) return;
      btnResetDb.disabled = true;
      btnResetDb.textContent = 'Resetting...';

      try {
        const res = await fetch('/api/reset-demo', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
          alert('Database reset and seeded with Indian records! Reloading...');
          window.location.reload();
        } else {
          alert('Failed: ' + data.error);
        }
      } catch (e) {
        alert('Error: ' + e.message);
      } finally {
        btnResetDb.disabled = false;
        btnResetDb.textContent = 'Reset & Re-seed Data';
      }
    });
  }
});
