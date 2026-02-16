const STORAGE_KEY = 'ddxCards.v1';
const PASSWORD_HASH_KEY = 'ddxPasswordHash';
const SEED_URL = 'data/seed-data.json';
const fallbackSymptoms = [
  'Abdominal and pelvic pain',
  'Abnormal uterine bleeding',
  'Annular skin lesions',
  'Anxiety, depression',
  'Arthralgias',
  'Back pain',
  'Back Pain in Children',
  'Breast pain (mastalgia)',
  'Chest pain',
  'Cold feeling',
  'Constipation',
  'Cough',
  'Cough, dyspnea  (infant, newborn)',
  'Crying infant (Inconsolable)',
  'Delirium',
  'Dementia, memory loss',
  'Depigmentation, hypopigmentation of skin',
  'Diarrhea',
  'Dizziness, ill-defined',
  'Dysphagia',
  'Dyspnea, tachypnea',
  'Ear pain, otalgia',
  'Edema, leg',
  'Eye pain',
  'Eyelid swelling - Bilateral',
  'Eyelid swelling - Unilateral',
  'Facial flushing, hot flashes',
  'Facial pain',
  'Falls in the elderly',
  'Fatigue, malaise, vague symptoms',
  'Fever (acute, uncertain source)',
  'Flank pain',
  'Genital skin lesion, genital ulcer',
  'Groin pain',
  'Hair Loss',
  'Headache',
  'Hearing loss (deafness)',
  'Hematuria',
  'Hip pain',
  'Hypotension, shock',
  'Insomnia, sleep disturbance',
  'Leg pain, bone pain, extremity pain',
  'Limp in child',
  'Lymphadenopathy',
  'Mental status, acute change (coma, lethargy)',
  'Mouth pain, burning mouth, burning tongue',
  'Mouth ulcers',
  'Muscle cramps',
  'Myalgias, generalized',
  'Nausea, vomiting',
  'Neck pain',
  'Neck mass',
  'Numbness, sensory loss, neuropathy',
  'Pruritus',
  'Rash, generalized',
  'Red eye',
  'Red skin patch',
  'Rhinorrhea, nasal congestion',
  'Scrotal pain',
  'Seizure and seizure mimics',
  'Shoulder pain',
  'Sinus tachycardia',
  'Sore throat, pharyngitis',
  'Stroke and stroke mimics',
  'Sweating, excessive, hyperhidrosis, night sweats',
  'Syncope, near syncope',
  'Tinnitus',
  'Tremor',
  'Urinary symptoms (dysuria, frequency, urgency)',
  'Vertigo',
  'Weakness (objective muscle weakness)',
  'Weight loss'
];

const refs = {
  searchInput: document.getElementById('searchInput'),
  newCardBtn: document.getElementById('newCardBtn'),
  cardList: document.getElementById('cardList'),
  cardForm: document.getElementById('cardForm'),
  deleteBtn: document.getElementById('deleteBtn'),
  exportBtn: document.getElementById('exportBtn'),
  importInput: document.getElementById('importInput'),
  changePassword: document.getElementById('changePassword'),
  overlay: document.getElementById('lockOverlay'),
  overlayForm: document.getElementById('lockForm'),
  overlayPassword: document.getElementById('lockPassword'),
  overlayConfirm: document.getElementById('lockConfirm'),
  overlayInfo: document.getElementById('lockInfo'),
  overlayTitle: document.getElementById('lockTitle'),
  overlayDescription: document.getElementById('lockDescription'),
  overlaySubmit: document.getElementById('lockSubmit'),
  overlayConfirmRow: document.getElementById('lockConfirmRow')
};

refs.changePassword.disabled = true;
if (refs.overlay) {
  refs.overlay.hidden = true;
}

let seedData = {};
let seedSymptoms = [];
let cards = [];
let selectedId = null;
let overlayMode = 'unlock';
let isUnlocked = false;

function serializeSeedList(list) {
  if (!Array.isArray(list)) return '';
  return list.join('\n');
}

function fallbackSeed() {
  return fallbackSymptoms.slice();
}

async function fetchSeedData() {
  try {
    const response = await fetch(SEED_URL);
    if (!response.ok) throw new Error('Seed fetch failed');
    seedData = await response.json();
    seedSymptoms = Object.keys(seedData).sort((a, b) => a.localeCompare(b));
  } catch (error) {
    console.warn('Seed data load failed, using fallback list.', error);
    seedData = {};
    seedSymptoms = fallbackSeed();
  }
  if (!seedSymptoms.length) {
    seedSymptoms = fallbackSeed();
  }
}

function mapSeed(symptom) {
  const seed = seedData[symptom] || {};
  return {
    commonCauses: serializeSeedList(seed.common),
    cantMiss: serializeSeedList(seed.cantMiss),
    source: seed.source || 'University of Toronto Diagnostic Checklist'
  };
}

function newCard(symptom = '') {
  const { commonCauses, cantMiss, source } = mapSeed(symptom);
  return {
    id: crypto.randomUUID(),
    symptom,
    commonCauses,
    cantMiss,
    redFlags: '',
    initialWorkup: '',
    references: '',
    notes: '',
    lastReviewed: '',
    source
  };
}

function persist(newCards) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(newCards));
}

function loadCards() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    const seeded = seedSymptoms.map((symptom) => newCard(symptom));
    persist(seeded);
    return seeded;
  }
  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) throw new Error('Stored value is not an array');
    return parsed;
  } catch (error) {
    console.warn('Stored cards invalid, reseeding.', error);
    const seeded = seedSymptoms.map((symptom) => newCard(symptom));
    persist(seeded);
    return seeded;
  }
}

function currentCard() {
  return cards.find((card) => card.id === selectedId) ?? null;
}

function renderList() {
  const filter = refs.searchInput.value.trim().toLowerCase();
  const filtered = cards
    .filter((card) => card.symptom.toLowerCase().includes(filter))
    .sort((a, b) => a.symptom.localeCompare(b.symptom));
  refs.cardList.innerHTML = '';
  filtered.forEach((card) => {
    const li = document.createElement('li');
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = card.symptom || '(Untitled symptom)';
    if (card.id === selectedId) btn.classList.add('active');
    btn.addEventListener('click', () => {
      selectedId = card.id;
      render();
    });
    li.appendChild(btn);
    refs.cardList.appendChild(li);
  });
  if (!currentCard() && filtered.length > 0) {
    selectedId = filtered[0].id;
  }
}

function fillForm() {
  const card = currentCard();
  if (!card) {
    refs.cardForm.reset();
    return;
  }
  refs.cardForm.symptom.value = card.symptom;
  refs.cardForm.commonCauses.value = card.commonCauses;
  refs.cardForm.cantMiss.value = card.cantMiss;
  refs.cardForm.redFlags.value = card.redFlags;
  refs.cardForm.initialWorkup.value = card.initialWorkup;
  refs.cardForm.references.value = card.references;
  refs.cardForm.notes.value = card.notes;
  refs.cardForm.lastReviewed.value = card.lastReviewed;
  refs.cardForm.source.value = card.source;
}

function render() {
  renderList();
  fillForm();
}

refs.searchInput.addEventListener('input', () => {
  renderList();
});

refs.newCardBtn.addEventListener('click', () => {
  if (!isUnlocked) return;
  const symptom = prompt('Symptom name');
  if (!symptom) return;
  const trimmed = symptom.trim();
  const card = newCard(trimmed);
  cards.push(card);
  selectedId = card.id;
  persist(cards);
  render();
});

refs.cardForm.addEventListener('submit', (event) => {
  event.preventDefault();
  if (!isUnlocked) return;
  const card = currentCard();
  if (!card) return;
  card.symptom = refs.cardForm.symptom.value.trim();
  card.commonCauses = refs.cardForm.commonCauses.value.trim();
  card.cantMiss = refs.cardForm.cantMiss.value.trim();
  card.redFlags = refs.cardForm.redFlags.value.trim();
  card.initialWorkup = refs.cardForm.initialWorkup.value.trim();
  card.references = refs.cardForm.references.value.trim();
  card.notes = refs.cardForm.notes.value.trim();
  card.lastReviewed = refs.cardForm.lastReviewed.value;
  card.source = refs.cardForm.source.value.trim();
  persist(cards);
  render();
});

refs.deleteBtn.addEventListener('click', () => {
  if (!isUnlocked) return;
  const card = currentCard();
  if (!card) return;
  const ok = confirm(`Delete card for "${card.symptom}"?`);
  if (!ok) return;
  cards = cards.filter((c) => c.id !== card.id);
  selectedId = cards[0]?.id ?? null;
  persist(cards);
  render();
});

refs.exportBtn.addEventListener('click', () => {
  if (!isUnlocked) return;
  const blob = new Blob([JSON.stringify(cards, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'ddx-cards.json';
  a.click();
  URL.revokeObjectURL(url);
});

refs.importInput.addEventListener('change', async (event) => {
  if (!isUnlocked) return;
  const file = event.target.files?.[0];
  if (!file) return;
  try {
    const text = await file.text();
    const parsed = JSON.parse(text);
    if (!Array.isArray(parsed)) throw new Error('JSON must be an array of cards');
    cards = parsed
      .filter((item) => item && typeof item === 'object')
      .map((item) => ({
        id: typeof item.id === 'string' ? item.id : crypto.randomUUID(),
        symptom: String(item.symptom ?? ''),
        commonCauses: String(item.commonCauses ?? ''),
        cantMiss: String(item.cantMiss ?? ''),
        redFlags: String(item.redFlags ?? ''),
        initialWorkup: String(item.initialWorkup ?? ''),
        references: String(item.references ?? ''),
        notes: String(item.notes ?? ''),
        lastReviewed: String(item.lastReviewed ?? ''),
        source: String(item.source ?? '')
      }));
    selectedId = cards[0]?.id ?? null;
    persist(cards);
    render();
  } catch (error) {
    alert(`Import failed: ${error.message}`);
  } finally {
    refs.importInput.value = '';
  }
});

async function hashPassword(password) {
  if (window.crypto?.subtle) {
    const buffer = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(password));
    return Array.from(new Uint8Array(buffer))
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('');
  }
  return `legacy:${btoa(password)}`;
}

function showOverlay(mode) {
  overlayMode = mode;
  refs.overlayConfirmRow.style.display = mode === 'unlock' ? 'none' : 'grid';
  refs.overlayTitle.textContent = mode === 'unlock' ? 'Unlock vault' : 'Set password';
  refs.overlayDescription.textContent = mode === 'unlock'
    ? 'Enter your password to unlock the editor.'
    : 'Create a password to protect your notes.';
  refs.overlaySubmit.textContent = mode === 'unlock' ? 'Unlock' : 'Save password';
  refs.overlayInfo.textContent = '';
  refs.overlayPassword.value = '';
  refs.overlayConfirm.value = '';
  refs.overlay.hidden = false;
  refs.overlay.classList.add('active');
  document.body.classList.add('locked');
}

function hideOverlay() {
  refs.overlay.classList.remove('active');
  document.body.classList.remove('locked');
  setTimeout(() => {
    if (!refs.overlay.classList.contains('active')) {
      refs.overlay.hidden = true;
    }
  }, 250);
}

function showLockMessage(message, isError = false) {
  if (!refs.overlayInfo) return;
  refs.overlayInfo.textContent = message;
  refs.overlayInfo.style.color = isError ? 'var(--danger)' : 'var(--muted)';
}

async function handleOverlaySubmit(event) {
  event.preventDefault();
  const password = refs.overlayPassword.value.trim();
  const confirm = refs.overlayConfirm.value.trim();
  if (!password) {
    showLockMessage('Password cannot be empty.', true);
    return;
  }
  if (overlayMode === 'unlock') {
    const stored = localStorage.getItem(PASSWORD_HASH_KEY);
    if (!stored) {
      showOverlay('set');
      return;
    }
    const hashed = await hashPassword(password);
    if (hashed === stored) {
      showLockMessage('Unlocked.', false);
      unlockVault();
      hideOverlay();
      return;
    }
    showLockMessage('Incorrect password.', true);
    return;
  }
  if (password !== confirm) {
    showLockMessage('Passwords must match.', true);
    return;
  }
  const hashed = await hashPassword(password);
  localStorage.setItem(PASSWORD_HASH_KEY, hashed);
  showLockMessage('Password saved.', false);
  unlockVault();
  hideOverlay();
}

function unlockVault() {
  isUnlocked = true;
  refs.changePassword.disabled = false;
}

function lockVault() {
  isUnlocked = false;
  refs.changePassword.disabled = true;
  showOverlay('unlock');
}

refs.overlayForm.addEventListener('submit', handleOverlaySubmit);
refs.changePassword.addEventListener('click', () => {
  if (!isUnlocked) {
    showOverlay('unlock');
    return;
  }
  showOverlay('set');
});

async function initialize() {
  await fetchSeedData();
  cards = loadCards();
  selectedId = cards[0]?.id ?? null;
  const storedPassword = localStorage.getItem(PASSWORD_HASH_KEY);
  if (storedPassword) {
    showOverlay('unlock');
  } else {
    showOverlay('set');
  }
  render();
}

initialize();
