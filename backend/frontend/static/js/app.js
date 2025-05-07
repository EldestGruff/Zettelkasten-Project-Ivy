// frontend/static/js/app.js

document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM fully loaded and parsed");

    // --- DOM Element References ---
    // Sidebar
    const notesListElement = document.getElementById('notes-list');
    const showCreateFormBtn = document.getElementById('show-create-form-btn');
    const createFormContainer = document.getElementById('note-create-form-container');
    const createForm = document.getElementById('note-create-form');
    const createContentInput = document.getElementById('create-content');
    const createMemoryTypeInput = document.getElementById('create-memory-type');
    const cancelCreateBtn = document.getElementById('cancel-create-btn');
    const createErrorElement = document.getElementById('create-error');

    // Main View
    const noteDetailElement = document.getElementById('note-detail');
    const noteDetailPlaceholder = document.getElementById('note-detail-placeholder');
    const noteTitleElement = document.getElementById('note-title');
    const noteContentDisplayElement = document.getElementById('note-content-display');
    const noteMemoryTypeElement = document.getElementById('note-memory-type');
    const noteArchivedElement = document.getElementById('note-archived');
    const noteTagsElement = document.getElementById('note-tags');
    const noteCreatedElement = document.getElementById('note-created');
    const noteUpdatedElement = document.getElementById('note-updated');
    const editNoteBtn = document.getElementById('edit-note-btn');
    const archiveNoteBtn = document.getElementById('archive-note-btn');
    const deleteNoteBtn = document.getElementById('delete-note-btn');
    const outgoingLinksList = document.getElementById('note-links-outgoing');
    const incomingLinksList = document.getElementById('note-links-incoming');

    // Edit Form
    const editFormContainer = document.getElementById('note-edit-form-container');
    const editForm = document.getElementById('note-edit-form');
    const editNoteIdInput = document.getElementById('edit-note-id');
    const editContentInput = document.getElementById('edit-content');
    const editMemoryTypeInput = document.getElementById('edit-memory-type');
    const cancelEditBtn = document.getElementById('cancel-edit-btn');
    const editErrorElement = document.getElementById('edit-error');
    const addTagInput = document.getElementById('add-tag-input');
    const addTagBtn = document.getElementById('add-tag-btn');
    const addTagErrorElement = document.getElementById('add-tag-error');
    const linkTargetNoteIdInput = document.getElementById('link-target-note-id');
    const createLinkBtn = document.getElementById('create-link-btn');
    const createLinkErrorElement = document.getElementById('create-link-error');
    // --- Global State (Simple) ---
    let currentNote = null; // Store the currently displayed note object
    let notesCache = []; // Simple cache for the notes list

    // --- API Helper ---
    // Basic helper for fetch calls, handling errors and JSON parsing
    async function apiCall(url, options = {}) {
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                let errorDetail = `HTTP error! status: ${response.status}`;
                try {
                    // Try to get more detail from API error response
                    const errorJson = await response.json();
                    errorDetail = errorJson.detail || errorDetail;
                } catch (e) { /* Ignore if response body isn't JSON */ }
                throw new Error(errorDetail);
            }
            // Handle 204 No Content responses specifically
            if (response.status === 204) {
                return null; // Or return a specific marker if needed
            }
            return await response.json();
        } catch (error) {
            console.error(`API call failed: ${options.method || 'GET'} ${url}`, error);
            throw error; // Re-throw for specific handlers
        }
    }

    // --- UI Update Functions ---
    function displayNoteList(notes) {
        notesListElement.innerHTML = ''; // Clear previous list
        if (notes.length === 0) {
            notesListElement.innerHTML = '<li>No notes found. Create one!</li>';
            return;
        }
        notesCache = notes; // Update cache
        notes.forEach(note => {
            const listItem = document.createElement('li');
            // Simple preview - maybe use first line of content later
            listItem.textContent = `[${note.memory_type}] ${note.id}`; // Example text
            listItem.dataset.noteId = note.id;
            // Highlight if it's the currently selected note
            if (currentNote && currentNote.id === note.id) {
                listItem.classList.add('active');
            }
            listItem.addEventListener('click', () => handleNoteSelection(note.id));
            notesListElement.appendChild(listItem);
        });
    }

function displayNoteDetail(note) {
    currentNote = note; // Update global state

    // Populate static fields
    noteTitleElement.textContent = `Note: ${note.id}`;
    noteContentDisplayElement.textContent = note.content;
    noteMemoryTypeElement.textContent = note.memory_type;
    noteArchivedElement.textContent = note.is_archived ? 'Yes' : 'No';
    noteCreatedElement.textContent = new Date(note.created_at).toLocaleString();
    noteUpdatedElement.textContent = new Date(note.updated_at).toLocaleString();

    // Populate Tags (with remove buttons)
    noteTagsElement.innerHTML = ''; // Clear previous tags
    if (note.tags && note.tags.length > 0) {
        note.tags.forEach(tag => {
            const tagSpan = document.createElement('span');
            tagSpan.textContent = tag.name;
            const removeBtn = document.createElement('button');
            removeBtn.textContent = 'x';
            removeBtn.title = `Remove tag '${tag.name}'`;
            removeBtn.dataset.tagId = tag.id;
            removeBtn.onclick = () => handleRemoveTag(note.id, tag.id);
            tagSpan.appendChild(removeBtn);
            noteTagsElement.appendChild(tagSpan);
        });
    } else {
        noteTagsElement.textContent = 'None';
    }

    // Update Archive button text/state
    archiveNoteBtn.textContent = note.is_archived ? 'Unarchive' : 'Archive';
    archiveNoteBtn.dataset.noteId = note.id; // Store ID for handler
    archiveNoteBtn.disabled = false; // Enable button

    // Store ID for delete button handler
    deleteNoteBtn.dataset.noteId = note.id;
    deleteNoteBtn.disabled = false; // Enable button

    // Enable Add Tag / Create Link buttons
    addTagBtn.disabled = false;
    createLinkBtn.disabled = false;
    addTagInput.value = ''; // Clear inputs
    linkTargetNoteIdInput.value = '';
    hideError(addTagErrorElement); // Hide errors
    hideError(createLinkErrorElement);

    // Show/hide sections
    noteDetailElement.classList.remove('hidden');
    editFormContainer.classList.add('hidden'); // Hide edit form if it was open
    noteDetailPlaceholder.classList.add('hidden');

    // Fetch and display links
    fetchAndDisplayLinks(note.id);

    // Highlight selected note in the list
    highlightSelectedNote(note.id);
}

    function displayLinks(listElement, links) {
         listElement.innerHTML = ''; // Clear loading/previous
         if (links.length > 0) {
            links.forEach(linkedNote => {
                const li = document.createElement('li');
                const link = document.createElement('a');
                link.textContent = `[${linkedNote.memory_type}] ${linkedNote.id}`; // Display minimal info
                link.dataset.noteId = linkedNote.id;
                link.onclick = () => handleNoteSelection(linkedNote.id); // Navigate on click
                li.appendChild(link);
                listElement.appendChild(li);
            });
         } else {
            listElement.innerHTML = '<li>None</li>';
         }
    }

    function showCreateForm() {
        createFormContainer.classList.remove('hidden');
        noteDetailElement.classList.add('hidden');
        noteDetailPlaceholder.classList.add('hidden');
        editFormContainer.classList.add('hidden');
        hideError(createErrorElement);
        createForm.reset(); // Clear form fields
        highlightSelectedNote(null); // Deselect notes list
    }

    function hideCreateForm() {
        createFormContainer.classList.add('hidden');
        // Show placeholder only if no note is selected
        if (!currentNote) {
            noteDetailPlaceholder.classList.remove('hidden');
        } else {
            noteDetailElement.classList.remove('hidden');
        }
    }

    function showEditForm() {
        if (!currentNote) return; // Should not happen if edit btn is clicked correctly

        // Populate form
        editNoteIdInput.value = currentNote.id;
        editContentInput.value = currentNote.content;
        editMemoryTypeInput.value = currentNote.memory_type;

        // Show/hide sections
        noteDetailElement.classList.add('hidden');
        editFormContainer.classList.remove('hidden');
        hideError(editErrorElement);
    }

    function hideEditForm() {
        editFormContainer.classList.add('hidden');
        // Show detail view for the current note again
        if (currentNote) {
             noteDetailElement.classList.remove('hidden');
        } else {
             noteDetailPlaceholder.classList.remove('hidden');
        }
    }

    function showError(element, message) {
        element.textContent = message;
        element.classList.remove('hidden');
    }
    function hideError(element) {
        element.classList.add('hidden');
    }

    function highlightSelectedNote(noteId) {
        const listItems = notesListElement.querySelectorAll('li');
        listItems.forEach(li => {
            if (li.dataset.noteId === noteId) {
                li.classList.add('active');
            } else {
                li.classList.remove('active');
            }
        });
    }

    // --- Event Handlers ---
    async function handleNoteSelection(noteId) {
        console.log(`Fetching note detail for ID: ${noteId}`);
        hideError(createErrorElement); // Hide errors if switching view
        hideError(editErrorElement);
        try {
            const note = await apiCall(`/notes/${noteId}`);
            if (note) {
                 displayNoteDetail(note);
            } else {
                 // Handle case where note might have been deleted/archived between list load and click
                 console.warn(`Note ${noteId} not found when fetching detail.`);
                 fetchAndDisplayNotes(); // Refresh list
                 noteDetailPlaceholder.classList.remove('hidden');
                 noteDetailElement.classList.add('hidden');
                 currentNote = null;
            }
        } catch (error) {
            showError(noteDetailPlaceholder, `Error loading note: ${error.message}`);
            noteDetailPlaceholder.classList.remove('hidden');
            noteDetailElement.classList.add('hidden');
            currentNote = null;
        }
    }

    async function handleCreateNote(event) {
        event.preventDefault(); // Prevent default HTML form submission
        hideError(createErrorElement);
        console.log("Submitting create note form...");

        const noteData = {
            content: createContentInput.value.trim(),
            memory_type: createMemoryTypeInput.value
        };

        if (!noteData.content) {
            showError(createErrorElement, "Content cannot be empty.");
            return;
        }

        try {
            const createdNote = await apiCall('/notes/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(noteData)
            });
            console.log("Note created:", createdNote);
            hideCreateForm();
            await fetchAndDisplayNotes(); // Refresh the list
            // Automatically select the newly created note
            handleNoteSelection(createdNote.id);
        } catch (error) {
            console.error("Error creating note:", error);
            showError(createErrorElement, `Failed to create note: ${error.message}`);
        }
    }

    async function handleEditNote(event) {
        event.preventDefault();
        hideError(editErrorElement);
        console.log("Submitting edit note form...");

        const noteId = editNoteIdInput.value;
        const noteData = {
            content: editContentInput.value.trim(),
            memory_type: editMemoryTypeInput.value
        };

        if (!noteData.content) {
             showError(editErrorElement, "Content cannot be empty.");
            return;
        }

        try {
            const updatedNote = await apiCall(`/notes/${noteId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(noteData) // Send only editable fields
            });
            console.log("Note updated:", updatedNote);
            // Instead of full refresh, update currentNote and display directly
            displayNoteDetail(updatedNote); // This hides edit form and shows updated details
            // Refresh the main list in the background in case sorting changes
            fetchAndDisplayNotes();
        } catch (error) {
            console.error("Error updating note:", error);
            showError(editErrorElement, `Failed to update note: ${error.message}`);
        }
    }

    async function handleRemoveTag(noteId, tagId) {
        console.log(`Attempting to remove tag ${tagId} from note ${noteId}`);
        if (!confirm(`Are you sure you want to remove tag ID ${tagId} from this note?`)) {
            return;
        }
        try {
            const updatedNote = await apiCall(`/notes/${noteId}/tags/${tagId}`, {
                method: 'DELETE'
            });
            // Refresh the detail view to show updated tags
            displayNoteDetail(updatedNote);
        } catch (error) {
             alert(`Error removing tag: ${error.message}`); // Simple alert for now
        }
    }

async function handleToggleArchive() {
    console.log("handleToggleArchive entered. currentNote:", currentNote);
    if (!currentNote) return;

    const noteId = currentNote.id;
    const isArchived = currentNote.is_archived;
    const action = isArchived ? 'unarchive' : 'archive';
    const confirmationMessage = `Are you sure you want to ${action} note ${noteId}?`;

    console.log("About to show confirmation:", confirmationMessage);
    if (!confirm(confirmationMessage)) {
        console.log("Confirmation denied.");
        return;
    }
    console.log("Confirmation accepted. Proceeding with API call...");

    try {
        // Disable button during API call
        archiveNoteBtn.disabled = true;
        archiveNoteBtn.textContent = `${action.charAt(0).toUpperCase() + action.slice(1)}ing...`;

        const updatedNote = await apiCall(`/notes/${noteId}/${action}`, {
            method: 'POST'
        });

        console.log("API call successful, updating UI...");
        displayNoteDetail(updatedNote); // Update details shown (incl. button text)
        fetchAndDisplayNotes(); // Refresh list view in case filtering changes

    } catch (error) {
        console.error(`Error in handleToggleArchive: ${error.message}`);
        alert(`Error ${action}ing note: ${error.message}`);
         // Re-enable button and reset text on error
         archiveNoteBtn.disabled = false;
         archiveNoteBtn.textContent = isArchived ? 'Unarchive' : 'Archive';
    }
}
// -----------------------------------------

    // --- Async Function Wrappers (Initial load, Links) ---
    async function fetchAndDisplayNotes() {
        console.log("Fetching notes list...");
        try {
            const notes = await apiCall('/notes/?limit=200'); // Increase limit?
            displayNoteList(notes);
        } catch (error) {
            console.error("Error fetching notes:", error);
            notesListElement.innerHTML = `<li>Error loading notes: ${error.message}</li>`;
        }
    }

     async function fetchAndDisplayLinks(noteId) {
        // Reset link lists
        outgoingLinksList.innerHTML = '<li>Loading...</li>';
        incomingLinksList.innerHTML = '<li>Loading...</li>';
        try {
             // Fetch outgoing and incoming links concurrently
            const [outgoing, incoming] = await Promise.all([
                apiCall(`/notes/${noteId}/links/outgoing`),
                apiCall(`/notes/${noteId}/links/incoming`)
            ]);
            displayLinks(outgoingLinksList, outgoing);
            displayLinks(incomingLinksList, incoming);
        } catch (error) {
            console.error(`Error fetching links for note ${noteId}:`, error);
            outgoingLinksList.innerHTML = '<li>Error loading links</li>';
            incomingLinksList.innerHTML = '<li>Error loading links</li>';
        }
     }

// Near the end of DOMContentLoaded
console.log("Attempting to add listener to archiveNoteBtn:", archiveNoteBtn); // Check the button object
if (archiveNoteBtn) {
    archiveNoteBtn.addEventListener('click', handleToggleArchive);
    console.log("Listener added to archiveNoteBtn"); // Confirm listener attached
} else {
    console.error("Archive button element not found!");
}

    // --- Initial Setup & Event Listeners ---
    fetchAndDisplayNotes(); // Load initial list

    showCreateFormBtn.addEventListener('click', showCreateForm);
    cancelCreateBtn.addEventListener('click', hideCreateForm);
    createForm.addEventListener('submit', handleCreateNote);

    editNoteBtn.addEventListener('click', showEditForm);
    cancelEditBtn.addEventListener('click', hideEditForm);
    editForm.addEventListener('submit', handleEditNote);

    // Add listeners for new buttons
    archiveNoteBtn.addEventListener('click', handleToggleArchive);
    deleteNoteBtn.addEventListener('click', handleDeleteNote);
    addTagBtn.addEventListener('click', handleAddTag);
    createLinkBtn.addEventListener('click', handleCreateLink);

    // Disable buttons initially until a note is selected
    archiveNoteBtn.disabled = true;
    deleteNoteBtn.disabled = true;
    addTagBtn.disabled = true;
    createLinkBtn.disabled = true;

});
