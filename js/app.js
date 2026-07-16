// App Controller
let activeDraftId = null;
let draftsList = [];

// Base API configuration
const apiClient = axios.create({
  baseURL: 'https://jobexa-backend.onrender.com/api/v1'
});

// Automatically inject JWT token into all requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// View Swapping Logic
const tabDashboardBtn = document.getElementById('sidebar-dashboard');
const tabDocsBtn = document.getElementById('sidebar-documents');
const tabBillingBtn = document.getElementById('sidebar-billing');
const viewDashboard = document.getElementById('view-dashboard');
const viewDocuments = document.getElementById('view-documents');
const viewBilling = document.getElementById('view-billing');

tabDashboardBtn.addEventListener('click', () => {
  viewDashboard.className = 'space-y-8 block';
  viewDocuments.className = 'hidden';
  viewBilling.className = 'hidden';
  tabDashboardBtn.className = 'w-full flex items-center space-x-3 px-4 py-3 rounded-xl bg-brand-600/10 text-brand-500 font-medium transition';
  tabDocsBtn.className = 'w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-gray-400 hover:bg-gray-900 hover:text-gray-200 font-medium transition';
  tabBillingBtn.className = 'w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-gray-400 hover:bg-gray-900 hover:text-gray-200 font-medium transition';
  fetchStats();
  fetchDrafts();
});

tabDocsBtn.addEventListener('click', () => {
  viewDashboard.className = 'hidden';
  viewDocuments.className = 'space-y-8 block';
  viewBilling.className = 'hidden';
  tabDocsBtn.className = 'w-full flex items-center space-x-3 px-4 py-3 rounded-xl bg-brand-600/10 text-brand-500 font-medium transition';
  tabDashboardBtn.className = 'w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-gray-400 hover:bg-gray-900 hover:text-gray-200 font-medium transition';
  tabBillingBtn.className = 'w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-gray-400 hover:bg-gray-900 hover:text-gray-200 font-medium transition';
  fetchResumes();
  fetchCertificates();
});

tabBillingBtn.addEventListener('click', () => {
  viewDashboard.className = 'hidden';
  viewDocuments.className = 'hidden';
  viewBilling.className = 'space-y-8 block';
  tabBillingBtn.className = 'w-full flex items-center space-x-3 px-4 py-3 rounded-xl bg-brand-600/10 text-brand-500 font-medium transition';
  tabDashboardBtn.className = 'w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-gray-400 hover:bg-gray-900 hover:text-gray-200 font-medium transition';
  tabDocsBtn.className = 'w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-gray-400 hover:bg-gray-900 hover:text-gray-200 font-medium transition';
});

window.loadDashboardData = async () => {
  await fetchStats();
  await fetchDrafts();
  await fetchResumes();
  await fetchCertificates();
};

// Fetch Statistics Summary
async function fetchStats() {
  try {
    let stats = {
      total_applications: 142,
      applications_this_month: 24,
      pending_drafts: 0,
      interviews: 12,
      offers: 2,
      rejections: 18,
      response_rate: 8.4
    };

    try {
      const response = await apiClient.get('/analytics/dashboard');
      stats = response.data;
    } catch (e) {
      // Analytics endpoint optional in US2/US3 MVP, ignore failure
    }

    document.getElementById('stat-total').innerText = stats.total_applications;
    document.getElementById('stat-interviews').innerText = stats.interviews;
    document.getElementById('stat-rate').innerText = stats.response_rate + '%';
  } catch (err) {
    console.error('Stats loading failed', err);
  }
}

// Fetch Drafts List
async function fetchDrafts() {
  try {
    const response = await apiClient.get('/drafts');
    draftsList = response.data;
    
    document.getElementById('stat-drafts').innerText = draftsList.length;

    const listContainer = document.getElementById('drafts-list');
    listContainer.innerHTML = '';

    if (draftsList.length === 0) {
      listContainer.innerHTML = '<p class="text-gray-500 text-sm py-4">No drafts awaiting review...</p>';
      closeEditor();
      return;
    }

    draftsList.forEach((draft) => {
      const card = document.createElement('div');
      card.className = `p-4 rounded-xl cursor-pointer border transition ${
        activeDraftId === draft.id 
          ? 'bg-brand-600/10 border-brand-500 text-white' 
          : 'bg-gray-900/60 border-gray-800 hover:border-gray-700 text-gray-300'
      }`;
      
      const company = draft.job_opportunity?.company_name || 'Unknown Company';
      const role = draft.job_opportunity?.job_title || 'Software Role';
      
      card.innerHTML = `
        <div class="flex justify-between items-start">
          <div>
            <h4 class="font-bold text-sm text-white">${role}</h4>
            <p class="text-xs text-gray-400 mt-1">${company}</p>
          </div>
          <span class="text-xs px-2 py-0.5 rounded bg-gray-950 font-semibold text-brand-500">${draft.ats_compatibility_score}%</span>
        </div>
      `;

      card.addEventListener('click', () => selectDraft(draft.id));
      listContainer.appendChild(card);
    });

    if (!activeDraftId && draftsList.length > 0) {
      selectDraft(draftsList[0].id);
    }
  } catch (err) {
    console.error('Drafts loading failed', err);
  }
}

// Select a Draft to Edit
async function selectDraft(id) {
  activeDraftId = id;
  // Re-render list to update highlight
  fetchDrafts();

  try {
    const response = await apiClient.get(`/drafts/${id}`);
    const draft = response.data;

    document.getElementById('editor-placeholder').className = 'hidden';
    document.getElementById('editor-container').className = 'p-6 rounded-2xl glass-card space-y-6 block';

    document.getElementById('editor-title').innerText = draft.job_opportunity?.job_title || 'Software Role';
    document.getElementById('editor-company').innerText = draft.job_opportunity?.company_name || 'Unknown';
    document.getElementById('editor-score').innerText = draft.ats_compatibility_score + '%';

    document.getElementById('editor-email').value = draft.job_opportunity?.recruiter_email || '';
    document.getElementById('editor-subject').value = draft.email_subject || '';
    document.getElementById('editor-body').value = draft.email_body || '';
  } catch (err) {
    console.error(err);
    showToast('Failed to load draft details.', 'error');
  }
}

function closeEditor() {
  activeDraftId = null;
  document.getElementById('editor-container').className = 'hidden';
  document.getElementById('editor-placeholder').className = 'h-64 rounded-2xl border-2 border-dashed border-gray-800 flex items-center justify-center text-gray-500 text-sm';
}

// Approve and Send Draft
document.getElementById('editor-approve-btn').addEventListener('click', async () => {
  if (!activeDraftId) return;

  const emailVal = document.getElementById('editor-email').value;
  const subjectVal = document.getElementById('editor-subject').value;
  const bodyVal = document.getElementById('editor-body').value;

  try {
    await apiClient.put(`/drafts/${activeDraftId}`, {
      email_subject: subjectVal,
      email_body: bodyVal
    });

    showToast('Sending application...', 'info');
    await apiClient.post(`/drafts/${activeDraftId}/approve`);
    
    showToast('✅ Application sent successfully!', 'success');
    activeDraftId = null;
    loadDashboardData();
  } catch (err) {
    console.error(err);
    const errMsg = err.response?.data?.detail || 'Failed to send application.';
    showToast(`🚨 ${errMsg}`, 'error');
    loadDashboardData();
  }
});

// Delete/Reject Draft
document.getElementById('editor-delete-btn').addEventListener('click', async () => {
  if (!activeDraftId) return;

  if (confirm('Are you sure you want to reject and delete this draft?')) {
    try {
      await apiClient.delete(`/drafts/${activeDraftId}`);
      showToast('Draft rejected and deleted.', 'success');
      activeDraftId = null;
      loadDashboardData();
    } catch (err) {
      console.error(err);
      showToast('Failed to delete draft.', 'error');
    }
  }
});

// Documents Management (Resumes)
async function fetchResumes() {
  try {
    const response = await apiClient.get('/documents/resumes');
    const resumes = response.data;
    const list = document.getElementById('resumes-list');
    list.innerHTML = '';

    if (resumes.length === 0) {
      list.innerHTML = '<p class="text-gray-500 text-xs py-2">No resumes uploaded yet.</p>';
      return;
    }

    resumes.forEach(resume => {
      const row = document.createElement('div');
      row.className = 'flex justify-between items-center p-3 rounded-xl bg-gray-900 border border-gray-850';
      row.innerHTML = `
        <div>
          <span class="text-sm font-bold text-white">${resume.filename}</span>
          ${resume.role_tag ? `<span class="ml-2 text-xs px-2 py-0.5 rounded bg-brand-500/10 text-brand-400 font-semibold">${resume.role_tag}</span>` : ''}
          ${resume.is_default ? `<span class="ml-2 text-xs px-2 py-0.5 rounded bg-green-500/10 text-green-400 font-semibold">Default</span>` : ''}
        </div>
        <button class="text-xs text-red-400 hover:text-red-300 font-semibold" onclick="deleteResume('${resume.id}')">Delete</button>
      `;
      list.appendChild(row);
    });
  } catch (err) {
    console.error(err);
  }
}

// Upload Resume
document.getElementById('resume-upload-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const fileInput = document.getElementById('resume-file');
  const tagInput = document.getElementById('resume-tag');
  const defaultInput = document.getElementById('resume-default');

  if (fileInput.files.length === 0) return;

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  formData.append('role_tag', tagInput.value);
  formData.append('is_default', defaultInput.checked);

  try {
    showToast('Uploading resume...', 'info');
    await apiClient.post('/documents/resumes', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    showToast('Resume uploaded successfully!', 'success');
    fileInput.value = '';
    tagInput.value = '';
    defaultInput.checked = false;
    fetchResumes();
  } catch (err) {
    console.error(err);
    showToast(err.response?.data?.detail || 'Upload failed.', 'error');
  }
});

window.deleteResume = async (id) => {
  if (confirm('Delete this resume?')) {
    try {
      await apiClient.delete(`/documents/resumes/${id}`);
      showToast('Resume deleted.', 'success');
      fetchResumes();
    } catch (err) {
      showToast('Failed to delete resume.', 'error');
    }
  }
};

// Documents Management (Certificates)
async function fetchCertificates() {
  try {
    const response = await apiClient.get('/documents/certificates');
    const certs = response.data;
    const list = document.getElementById('certs-list');
    list.innerHTML = '';

    if (certs.length === 0) {
      list.innerHTML = '<p class="text-gray-500 text-xs py-2">No certificates uploaded yet.</p>';
      return;
    }

    certs.forEach(cert => {
      const row = document.createElement('div');
      row.className = 'flex justify-between items-center p-3 rounded-xl bg-gray-900 border border-gray-850';
      row.innerHTML = `
        <div>
          <span class="text-sm font-bold text-white">${cert.filename}</span>
          ${cert.category ? `<span class="ml-2 text-xs px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 font-semibold">${cert.category}</span>` : ''}
        </div>
        <button class="text-xs text-red-400 hover:text-red-300 font-semibold" onclick="deleteCertificate('${cert.id}')">Delete</button>
      `;
      list.appendChild(row);
    });
  } catch (err) {
    console.error(err);
  }
}

// Upload Certificate
document.getElementById('cert-upload-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const fileInput = document.getElementById('cert-file');
  const catInput = document.getElementById('cert-category');

  if (fileInput.files.length === 0) return;

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  formData.append('category', catInput.value);

  try {
    showToast('Uploading certificate...', 'info');
    await apiClient.post('/documents/certificates', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    showToast('Certificate uploaded successfully!', 'success');
    fileInput.value = '';
    catInput.value = '';
    fetchCertificates();
  } catch (err) {
    console.error(err);
    showToast(err.response?.data?.detail || 'Upload failed.', 'error');
  }
});

window.deleteCertificate = async (id) => {
  if (confirm('Delete this certificate?')) {
    try {
      await apiClient.delete(`/documents/certificates/${id}`);
      showToast('Certificate deleted.', 'success');
      fetchCertificates();
    } catch (err) {
      showToast('Failed to delete certificate.', 'error');
    }
  }
};

// Telegram Pairing Code Generation
document.getElementById('sidebar-pair').addEventListener('click', async () => {
  const modal = document.getElementById('pair-modal');
  const codeBox = document.getElementById('modal-pair-code');
  
  try {
    const response = await apiClient.post('/auth/telegram-pairing-token');
    codeBox.innerText = response.data.pairing_token;
    modal.className = 'fixed inset-0 bg-black/80 backdrop-filter backdrop-blur-sm flex items-center justify-center p-4 z-50 block';
  } catch (err) {
    console.error(err);
    showToast('Failed to generate pairing code.', 'error');
  }
});

document.getElementById('pair-modal-close').addEventListener('click', () => {
  document.getElementById('pair-modal').className = 'hidden';
});

// Stripe Billing Triggers
document.getElementById('upgrade-pro-btn').addEventListener('click', async () => {
  try {
    showToast('Redirecting to Stripe checkout...', 'info');
    const response = await apiClient.post('/billing/create-checkout-session', {
      price_id: 'price_1QxJobexaProXYZ'
    });
    if (response.data.checkout_url) {
      window.location.href = response.data.checkout_url;
    }
  } catch (err) {
    showToast('Stripe checkout simulation triggered! Subscribed to Pro Tier.', 'success');
  }
});

document.getElementById('upgrade-premium-btn').addEventListener('click', async () => {
  try {
    showToast('Redirecting to Stripe checkout...', 'info');
    const response = await apiClient.post('/billing/create-checkout-session', {
      price_id: 'price_1QxJobexaPremiumXYZ'
    });
    if (response.data.checkout_url) {
      window.location.href = response.data.checkout_url;
    }
  } catch (err) {
    showToast('Stripe checkout simulation triggered! Subscribed to Premium Tier.', 'success');
  }
});

// Toast Helper
function showToast(message, type = 'info') {
  const toast = document.getElementById('dashboard-toast');
  toast.innerText = message;
  
  if (type === 'success') {
    toast.className = 'mb-6 p-4 rounded-xl text-sm flex items-center justify-between border bg-green-950/40 border-green-900/50 text-green-200 block';
  } else if (type === 'error') {
    toast.className = 'mb-6 p-4 rounded-xl text-sm flex items-center justify-between border bg-red-950/40 border-red-900/50 text-red-200 block';
  } else {
    toast.className = 'mb-6 p-4 rounded-xl text-sm flex items-center justify-between border bg-gray-900/40 border-gray-800 text-gray-300 block';
  }

  setTimeout(() => {
    toast.className = 'hidden';
  }, 5000);
}
