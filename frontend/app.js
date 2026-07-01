// DOM Elements
const addCourseForm = document.getElementById('add-course-form');
const courseCodeInput = document.getElementById('course-code');
const courseTitleInput = document.getElementById('course-title');
const courseUnitsInput = document.getElementById('course-units');

const searchCodeInput = document.getElementById('search-code');
const searchBtn = document.getElementById('search-btn');
const searchResultBox = document.getElementById('search-result');

const filenameInput = document.getElementById('filename-input');
const saveBtn = document.getElementById('save-btn');
const loadBtn = document.getElementById('load-btn');

const totalCoursesCount = document.getElementById('total-courses-count');
const totalUnitsCount = document.getElementById('total-units-count');
const courseCountBadge = document.getElementById('course-count-badge');
const coursesTbody = document.getElementById('courses-tbody');

const toast = document.getElementById('toast');
const toastMessage = document.getElementById('toast-message');

/**
 * Displays a toast notification with the specified message and style.
 * @param {string} message - Text to show in toast.
 * @param {string} type - Notification level ('success' or 'error').
 */
function showToast(message, type = 'success') {
    toastMessage.textContent = message;
    toast.className = `toast-notification ${type}`;
    toast.classList.remove('hidden');

    // Auto-hide after 3.5 seconds
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3500);
}

/**
 * Updates the semester KPIs (Total courses count and total units count).
 */
async function updateKPIs() {
    try {
        // Fetch total credit units computed recursively in the backend
        const response = await fetch('/api/courses/total_units');
        const data = await response.json();
        
        if (data.status === 'success') {
            totalUnitsCount.textContent = data.total_units;
        }
    } catch (error) {
        console.error('Failed to load total units:', error);
    }
}

/**
 * Fetches the course registry from the API and updates the HTML table.
 */
async function fetchAndRenderCourses() {
    try {
        const response = await fetch('/api/courses');
        const data = await response.json();

        if (data.status === 'success') {
            const courses = data.courses;
            
            // Update KPI count & badge count
            totalCoursesCount.textContent = courses.length;
            courseCountBadge.textContent = `${courses.length} items`;

            // Clear table rows
            coursesTbody.innerHTML = '';

            // Check if directory is empty
            if (courses.length === 0) {
                coursesTbody.innerHTML = `
                    <tr class="empty-state-row">
                        <td colspan="4">
                            <div class="empty-state">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                                </svg>
                                <p>No courses registered yet.</p>
                                <span>Add a course on the left to get started.</span>
                            </div>
                        </td>
                    </tr>
                `;
                return;
            }

            // Loop and render rows
            for (let i = 0; i < courses.length; i++) {
                const c = courses[i];
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="course-code-cell">${escapeHtml(c.course_code)}</td>
                    <td class="course-title-cell">${escapeHtml(c.course_title)}</td>
                    <td class="course-unit-cell">${c.unit}</td>
                    <td class="actions-cell" style="text-align: right;">
                        <button class="btn-action edit-btn" data-code="${escapeHtml(c.course_code)}" data-title="${escapeHtml(c.course_title)}" data-unit="${c.unit}" title="Edit Course">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                <path d="M18.5 2.5a2.121 2.121 0 1 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                            </svg>
                        </button>
                        <button class="btn-action delete-btn" data-code="${escapeHtml(c.course_code)}" title="Delete Course">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="3 6 5 6 21 6"></polyline>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                <line x1="10" y1="11" x2="10" y2="17"></line>
                                <line x1="14" y1="11" x2="14" y2="17"></line>
                            </svg>
                        </button>
                    </td>
                `;
                coursesTbody.appendChild(tr);
            }
        }
    } catch (error) {
        showToast('Error loading course registry', 'error');
        console.error(error);
    }
}

/**
 * Escapes special characters in strings to prevent HTML injection.
 * @param {string} text - Unclean raw string.
 * @returns {string} Safe HTML string.
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

// Add Course Submission Event
addCourseForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const payload = {
        course_code: courseCodeInput.value,
        course_title: courseTitleInput.value,
        unit: parseInt(courseUnitsInput.value)
    };

    try {
        const response = await fetch('/api/courses', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (data.status === 'success') {
            showToast(`Registered ${payload.course_code} successfully!`);
            addCourseForm.reset();
            
            // Refresh board and stats
            await fetchAndRenderCourses();
            await updateKPIs();
        } else {
            showToast(data.message || 'Failed to add course', 'error');
        }
    } catch (error) {
        showToast('Network error, please try again.', 'error');
    }
});

async function performSearch() {
    const searchQuery = searchCodeInput.value.trim();
    if (!searchQuery) {
        searchResultBox.classList.add('hidden');
        return;
    }

    try {
        const response = await fetch(`/api/courses/search?query=${encodeURIComponent(searchQuery)}`);
        const data = await response.json();

        if (data.status === 'success') {
            searchResultBox.classList.remove('hidden');
            
            if (data.found && data.courses.length > 0) {
                let html = `<div class="search-results-list" style="display:flex; flex-direction:column; gap:8px;">`;
                for (let i = 0; i < data.courses.length; i++) {
                    const c = data.courses[i];
                    html += `
                        <div class="result-card" style="border-bottom: 1px solid var(--card-border); padding-bottom: 6px; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h4 style="margin: 0; color: var(--accent);">${escapeHtml(c.course_code)}</h4>
                                <p style="margin: 2px 0 4px 0; font-size: 0.85rem; color: var(--text-muted);">${escapeHtml(c.course_title)}</p>
                                <div class="result-meta" style="font-size: 0.75rem;">${c.unit} Credit Units</div>
                            </div>
                            <div class="result-actions" style="display: flex; gap: 4px;">
                                <button class="btn-action edit-btn" data-code="${escapeHtml(c.course_code)}" data-title="${escapeHtml(c.course_title)}" data-unit="${c.unit}" title="Edit Course">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                        <path d="M18.5 2.5a2.121 2.121 0 1 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                                    </svg>
                                </button>
                                <button class="btn-action delete-btn" data-code="${escapeHtml(c.course_code)}" title="Delete Course">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <polyline points="3 6 5 6 21 6"></polyline>
                                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                        <line x1="10" y1="11" x2="10" y2="17"></line>
                                        <line x1="14" y1="11" x2="14" y2="17"></line>
                                    </svg>
                                </button>
                            </div>
                        </div>
                    `;
                }
                html += `</div>`;
                searchResultBox.innerHTML = html;
            } else {
                searchResultBox.innerHTML = `
                    <div class="result-error">
                        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="12" y1="8" x2="12" y2="12"></line>
                            <line x1="12" y1="16" x2="12.01" y2="16"></line>
                        </svg>
                        <span>No courses match "${escapeHtml(searchQuery)}".</span>
                    </div>
                `;
            }
        }
    } catch (error) {
        showToast('Search query failed', 'error');
    }
}

searchBtn.addEventListener('click', performSearch);
searchCodeInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        performSearch();
    }
});

// Save to File event
saveBtn.addEventListener('click', async () => {
    const filename = filenameInput.value.trim();
    
    try {
        const response = await fetch('/api/courses/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename })
        });
        const data = await response.json();

        if (data.status === 'success') {
            showToast(data.message);
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        showToast('Could not reach backend to save file.', 'error');
    }
});

// Load from File event
loadBtn.addEventListener('click', async () => {
    const filename = filenameInput.value.trim();

    try {
        const response = await fetch('/api/courses/load', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename })
        });
        const data = await response.json();

        if (data.status === 'success') {
            showToast(data.message);
            // Refresh elements
            await fetchAndRenderCourses();
            await updateKPIs();
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        showToast('Could not reach backend to load file.', 'error');
    }
});

// Modal Element Selectors
const editModal = document.getElementById('edit-modal');
const editCourseForm = document.getElementById('edit-course-form');
const editOldCodeInput = document.getElementById('edit-old-code');
const editCourseCodeInput = document.getElementById('edit-course-code');
const editCourseTitleInput = document.getElementById('edit-course-title');
const editCourseUnitsInput = document.getElementById('edit-course-units');
const cancelEditBtn = document.getElementById('cancel-edit-btn');
const closeModalBtn = document.getElementById('close-modal-btn');

const deleteModal = document.getElementById('delete-modal');
const deleteCourseInfo = document.getElementById('delete-course-info');
const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
const cancelDeleteBtn = document.getElementById('cancel-delete-btn');

let courseCodeToDelete = '';

// Edit Modal Functions
function openEditModal(code, title, unit) {
    editOldCodeInput.value = code;
    editCourseCodeInput.value = code;
    editCourseTitleInput.value = title;
    editCourseUnitsInput.value = unit;
    editModal.classList.remove('hidden');
}

function closeEditModal() {
    editModal.classList.add('hidden');
    editCourseForm.reset();
}

closeModalBtn.addEventListener('click', closeEditModal);
cancelEditBtn.addEventListener('click', closeEditModal);

// Delete Modal Functions
function openDeleteModal(code) {
    courseCodeToDelete = code;
    deleteCourseInfo.textContent = code;
    deleteModal.classList.remove('hidden');
}

function closeDeleteModal() {
    deleteModal.classList.add('hidden');
    courseCodeToDelete = '';
}

cancelDeleteBtn.addEventListener('click', closeDeleteModal);

// Close modals when clicking outside the content
window.addEventListener('click', (e) => {
    if (e.target === editModal) closeEditModal();
    if (e.target === deleteModal) closeDeleteModal();
});

// Edit Form Submission
editCourseForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const old_code = editOldCodeInput.value;
    const payload = {
        old_code: old_code,
        course_code: editCourseCodeInput.value,
        course_title: editCourseTitleInput.value,
        unit: parseInt(editCourseUnitsInput.value)
    };

    try {
        const response = await fetch('/api/courses', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (data.status === 'success') {
            showToast(`Updated ${payload.course_code} successfully!`);
            closeEditModal();
            
            // Refresh table, KPIs, and search results
            await fetchAndRenderCourses();
            await updateKPIs();
            if (searchCodeInput.value.trim()) {
                await performSearch();
            }
        } else {
            showToast(data.message || 'Failed to update course', 'error');
        }
    } catch (error) {
        showToast('Network error, please try again.', 'error');
    }
});

// Delete confirmation click
confirmDeleteBtn.addEventListener('click', async () => {
    if (!courseCodeToDelete) return;

    try {
        const response = await fetch(`/api/courses?code=${encodeURIComponent(courseCodeToDelete)}`, {
            method: 'DELETE'
        });
        const data = await response.json();

        if (data.status === 'success') {
            showToast(`Deleted ${courseCodeToDelete} successfully!`);
            closeDeleteModal();
            
            // Refresh table, KPIs, and search results
            await fetchAndRenderCourses();
            await updateKPIs();
            if (searchCodeInput.value.trim()) {
                await performSearch();
            }
        } else {
            showToast(data.message || 'Failed to delete course', 'error');
        }
    } catch (error) {
        showToast('Network error, please try again.', 'error');
    }
});

// Helper for Edit click
function handleEditClick(btn) {
    const code = btn.getAttribute('data-code');
    const title = btn.getAttribute('data-title');
    const unit = btn.getAttribute('data-unit');
    openEditModal(code, title, unit);
}

// Helper for Delete click
function handleDeleteClick(btn) {
    const code = btn.getAttribute('data-code');
    openDeleteModal(code);
}

// Event Delegation on Table
coursesTbody.addEventListener('click', (e) => {
    const editBtn = e.target.closest('.edit-btn');
    const deleteBtn = e.target.closest('.delete-btn');
    if (editBtn) handleEditClick(editBtn);
    if (deleteBtn) handleDeleteClick(deleteBtn);
});

// Event Delegation on Search results
searchResultBox.addEventListener('click', (e) => {
    const editBtn = e.target.closest('.edit-btn');
    const deleteBtn = e.target.closest('.delete-btn');
    if (editBtn) handleEditClick(editBtn);
    if (deleteBtn) handleDeleteClick(deleteBtn);
});

// Initial Setup on Page Load
window.addEventListener('DOMContentLoaded', async () => {
    await fetchAndRenderCourses();
    await updateKPIs();
});
