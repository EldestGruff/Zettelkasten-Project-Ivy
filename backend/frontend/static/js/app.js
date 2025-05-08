// frontend/static/js/app.js
document.addEventListener('DOMContentLoaded', () => {
    // === Element References ==================================================
    const notesList = document.getElementById('notes-list');
    const createFormContainer = document.getElementById('note-create-form-container');
    const editFormContainer = document.getElementById('note-edit-form-container');
    const noteDetailElement = document.getElementById('note-detail');
    const noteDetailPlaceholder = document.getElementById('note-detail-placeholder');

    // More specific elements grouped
    const elements = {
        create: {
            form: document.getElementById('note-create-form'),
            contentInput: document.getElementById('create-content'),
            memoryTypeSelect: document.getElementById('create-memory-type'),
            error: document.getElementById('create-error'),
            cancelBtn: document.getElementById('cancel-create-btn')
        },
        edit: {
            form: document.getElementById('note-edit-form'),
            noteIdInput: document.getElementById('edit-note-id'),
            contentInput: document.getElementById('edit-content'),
            memoryTypeSelect: document.getElementById('edit-memory-type'),
            error: document.getElementById('edit-error'),
            cancelBtn: document.getElementById('cancel-edit-btn')
        },
        search: {
            input: document.getElementById('search-input'),
            results: document.getElementById('search-results-list'),
            error: document.getElementById('search-error'),
            btn: document.getElementById('search-btn')
        },
        tags: {
            container: document.getElementById('note-tags'), // Added for event delegation
            input: document.getElementById('add-tag-input'),
            error: document.getElementById('add-tag-error'),
            btn: document.getElementById('add-tag-btn')
        },
        links: {
            outgoingList: document.getElementById('note-links-outgoing'),
            incomingList: document.getElementById('note-links-incoming'),
            targetInput: document.getElementById('link-target-note-id'),
            error: document.getElementById('create-link-error'),
            btn: document.getElementById('create-link-btn')
        },
        buttons: {
            showCreateForm: document.getElementById('show-create-form-btn'),
            editNote: document.getElementById('edit-note-btn'),
            archiveNote: document.getElementById('archive-note-btn'),
            deleteNote: document.getElementById('delete-note-btn')
        },
        noteFields: {
            title: document.getElementById('note-title'),
            contentDisplay: document.getElementById('note-content-display'),
            memoryType: document.getElementById('note-memory-type'),
            archived: document.getElementById('note-archived'),
            created: document.getElementById('note-created'),
            updated: document.getElementById('note-updated')
        }
    };

    // === State Management ===================================================
    let currentNote = null;
    let notesCache = [];

    // === API Utilities =======================================================
    const apiCall = async (url, options = {}) => {
        const fetchOptions = {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...(options.headers || {}),
            },
        };
        try {
            const response = await fetch(url, fetchOptions);
            if (!response.ok) {
                let errorDetail = `HTTP error! status: ${response.status}`;
                try {
                    const errorJson = await response.json();
                    errorDetail = errorJson.detail || errorDetail;
                } catch (e) { /* Ignore */ }
                throw new Error(errorDetail);
            }
            if (response.status === 204) {
                return null;
            }
            return await response.json();
        } catch (error) {
            console.error(`API call failed: ${fetchOptions.method || 'GET'} ${url}`, error);
            throw error;
        }
    };

    // === DOM Utilities ======================================================
    const domHelper = {
        toggleVisibility: (element, visible) => {
            if (element) element.classList.toggle('hidden', !visible);
        },
        clearChildren: (element) => {
            if (element) element.innerHTML = '';
        },
        handleError: (element, message = '') => {
            if (!element) return;
            element.textContent = message;
            domHelper.toggleVisibility(element, !!message);
        },
        createListItem: (note, isActive = false) => {
            const li = document.createElement('li');
            li.className = isActive ? 'active' : '';
            li.dataset.noteId = note.id;
            const memoryTypeSpan = document.createElement('span');
            memoryTypeSpan.className = 'memory-type';
            memoryTypeSpan.textContent = `[${note.memory_type}]`;
            const noteIdSpan = document.createElement('span');
            noteIdSpan.className = 'note-id';
            noteIdSpan.textContent = ` ${note.id}`;
            const noteDate = document.createElement('time');
            noteDate.className = 'note-date';
            noteDate.textContent = new Date(note.updated_at).toLocaleDateString();
            li.appendChild(memoryTypeSpan);
            li.appendChild(noteIdSpan);
            li.appendChild(noteDate);
            return li;
        },
        createLinkListItem: (linkedNote) => {
            const li = document.createElement('li');
            const a = document.createElement('a');
            a.href = '#';
            a.dataset.noteId = linkedNote.id;
            a.textContent = `[${linkedNote.memory_type}] ${linkedNote.id}`;
            a.addEventListener('click', (e) => {
                e.preventDefault();
                handleNoteSelection(linkedNote.id);
            });
            li.appendChild(a);
            return li;
        }
    };

    // === Display Logic Specific to Search Results with Score ===
    const displaySearchResultsWithScore = (resultsData) => {
        const searchResultsList = elements.search.results;
        domHelper.clearChildren(searchResultsList);

        if (!resultsData || resultsData.length === 0) {
            const noResultsLi = document.createElement('li');
            noResultsLi.className = 'search-status';
            noResultsLi.textContent = 'No relevant notes found.';
            searchResultsList.appendChild(noResultsLi);
            return;
        }

        resultsData.forEach(result => {
            const listItem = document.createElement('li');
            listItem.className = 'search-result-item';

            let scoreFormatted = '';
            if (typeof result.score === 'number') {
                scoreFormatted = result.score.toFixed(3);
            }

            const link = document.createElement('a');
            link.href = '#';
            link.dataset.noteId = result.id;
            link.className = 'search-result-link';
            link.textContent = `[${result.memory_type}] Note ${result.id}`;
            link.addEventListener('click', (event) => {
                event.preventDefault();
                handleNoteSelection(result.id);
            });
            listItem.appendChild(link);

            if (scoreFormatted) {
                const scoreSpan = document.createElement('span');
                scoreSpan.className = 'search-result-score';
                scoreSpan.textContent = ` (Score: ${scoreFormatted})`;
                listItem.appendChild(scoreSpan);
            }
            
            const br = document.createElement('br');
            listItem.appendChild(br);

            const dateSmall = document.createElement('small');
            dateSmall.className = 'search-result-date';
            dateSmall.textContent = `Updated: ${new Date(result.updated_at).toLocaleDateString()}`;
            listItem.appendChild(dateSmall);

            searchResultsList.appendChild(listItem);
        });
    };


    // === Note Display Logic ==================================================
    const displayNoteDetail = (note) => {
        currentNote = note;

        if (elements.noteFields.title) elements.noteFields.title.textContent = `Note: ${note.id}`;
        if (elements.noteFields.contentDisplay) elements.noteFields.contentDisplay.textContent = note.content;
        if (elements.noteFields.memoryType) elements.noteFields.memoryType.textContent = note.memory_type;
        if (elements.noteFields.archived) elements.noteFields.archived.textContent = note.is_archived ? 'Yes' : 'No';
        if (elements.noteFields.created) elements.noteFields.created.textContent = new Date(note.created_at).toLocaleString();
        if (elements.noteFields.updated) elements.noteFields.updated.textContent = new Date(note.updated_at).toLocaleString();

        domHelper.clearChildren(elements.tags.container);
        if (note.tags && note.tags.length > 0) {
            note.tags.forEach(tag => {
                const tagSpan = document.createElement('span');
                tagSpan.className = 'tag';
                tagSpan.textContent = tag.name;
                const removeBtn = document.createElement('button');
                removeBtn.className = 'remove-tag';
                removeBtn.textContent = '×';
                removeBtn.title = `Remove tag '${tag.name}'`;
                removeBtn.dataset.tagId = tag.id;
                tagSpan.appendChild(removeBtn);
                elements.tags.container.appendChild(tagSpan);
            });
        } else {
            if (elements.tags.container) elements.tags.container.textContent = 'None';
        }

        if (elements.buttons.archiveNote) {
            elements.buttons.archiveNote.disabled = false;
            elements.buttons.archiveNote.textContent = note.is_archived ? 'Unarchive' : 'Archive';
        }
        if (elements.buttons.deleteNote) elements.buttons.deleteNote.disabled = false;
        if (elements.buttons.editNote) elements.buttons.editNote.disabled = false;
        if (elements.tags.btn) elements.tags.btn.disabled = false;
        if (elements.links.btn) elements.links.btn.disabled = false;

        domHelper.toggleVisibility(noteDetailElement, true);
        domHelper.toggleVisibility(noteDetailPlaceholder, false);
        domHelper.toggleVisibility(editFormContainer, false);
        domHelper.toggleVisibility(createFormContainer, false);

        fetchAndDisplayLinks(note.id);
        highlightSelectedNote(note.id);
    };

    const handleMissingNote = (noteId) => {
        domHelper.handleError(noteDetailPlaceholder, `Note ID ${noteId} not found or could not be loaded.`);
        domHelper.toggleVisibility(noteDetailElement, false);
        domHelper.toggleVisibility(noteDetailPlaceholder, true);
        currentNote = null;
        highlightSelectedNote(null);
        if (elements.buttons.archiveNote) elements.buttons.archiveNote.disabled = true;
        if (elements.buttons.deleteNote) elements.buttons.deleteNote.disabled = true;
        if (elements.buttons.editNote) elements.buttons.editNote.disabled = true;
        if (elements.tags.btn) elements.tags.btn.disabled = true;
        if (elements.links.btn) elements.links.btn.disabled = true;
    };

    // === Event Handlers ======================================================
    const handleNoteSelection = async (noteId) => {
        domHelper.handleError(noteDetailPlaceholder);
        try {
            const note = await apiCall(`/notes/${noteId}`);
            note ? displayNoteDetail(note) : handleMissingNote(noteId);
        } catch (error) {
            handleMissingNote(noteId);
            console.error(`Error selecting note ${noteId}:`, error);
        }
    };

    const handleCreateNote = async (event) => {
        event.preventDefault();
        const { contentInput, memoryTypeSelect, error: errorElement, form } = elements.create;
        domHelper.handleError(errorElement);
        const content = contentInput.value.trim();
        if (!content) {
            return domHelper.handleError(errorElement, 'Content cannot be empty');
        }
        try {
            const newNote = await apiCall('/notes/', {
                method: 'POST',
                body: JSON.stringify({
                    content: content,
                    memory_type: memoryTypeSelect.value
                })
            });
            form.reset();
            domHelper.toggleVisibility(createFormContainer, false);
            await fetchAndDisplayNotes();
            if (newNote && newNote.id) {
                handleNoteSelection(newNote.id);
            }
        } catch (apiError) {
            domHelper.handleError(errorElement, `Creation failed: ${apiError.message}`);
        }
    };

    const handleEditNote = async (event) => {
        event.preventDefault();
        const { noteIdInput, contentInput, memoryTypeSelect, error: errorElement, form } = elements.edit;
        domHelper.handleError(errorElement);
        const noteId = noteIdInput.value;
        const content = contentInput.value.trim();
        if (!content) {
            return domHelper.handleError(errorElement, 'Content cannot be empty.');
        }
        try {
            const updatedNote = await apiCall(`/notes/${noteId}`, {
                method: 'PATCH',
                body: JSON.stringify({
                    content: content,
                    memory_type: memoryTypeSelect.value
                })
            });
            form.reset();
            domHelper.toggleVisibility(editFormContainer, false);
            domHelper.toggleVisibility(noteDetailElement, true);
            displayNoteDetail(updatedNote);
            await fetchAndDisplayNotes();
        } catch (apiError) {
            domHelper.handleError(errorElement, `Update failed: ${apiError.message}`);
        }
    };

    const handleSearch = async () => {
        const { input, results, error: errorElement } = elements.search;
        domHelper.handleError(errorElement); // Clear previous search errors
        domHelper.clearChildren(results); // Clear previous results immediately

        const query = input.value.trim();
        if (!query) {
             // Optionally display a message like "Please enter a search term" or just do nothing
            return;
        }

        // Display "Searching..." message
        const searchingLi = document.createElement('li');
        searchingLi.className = 'search-status';
        searchingLi.textContent = 'Searching...';
        results.appendChild(searchingLi);

        try {
            const responseData = await apiCall('/search/similar', {
                method: 'POST',
                body: JSON.stringify({ query, limit: 15 })
            });
            
            // displaySearchResultsWithScore will clear the "Searching..." message
            if (responseData && responseData.results) {
                displaySearchResultsWithScore(responseData.results);
            } else {
                // Handle case where responseData or responseData.results is missing
                displaySearchResultsWithScore([]); // Will show "No relevant notes found"
            }
        } catch (apiError) {
            domHelper.handleError(errorElement, `Search failed: ${apiError.message}`);
            domHelper.clearChildren(results); // Clear "Searching..."
            const searchFailedLi = document.createElement('li');
            searchFailedLi.className = 'search-error'; // Use a specific class for search errors
            searchFailedLi.textContent = 'Search failed. Please try again.';
            results.appendChild(searchFailedLi);
        }
    };


    const handleAddTag = async () => {
        if (!currentNote) return domHelper.handleError(elements.tags.error, 'No note selected.');
        const { input, error: errorElement, btn } = elements.tags;
        domHelper.handleError(errorElement);
        const tagNameOrId = input.value.trim();
        if (!tagNameOrId) {
            return domHelper.handleError(errorElement, 'Tag name or ID cannot be empty.');
        }
        btn.disabled = true;
        btn.textContent = 'Adding...';
        try {
            const updatedNote = await apiCall(`/notes/${currentNote.id}/tags/${tagNameOrId}`, {
                method: 'POST'
            });
            input.value = '';
            displayNoteDetail(updatedNote);
        } catch (apiError) {
            domHelper.handleError(errorElement, `Failed to add tag: ${apiError.message}`);
        } finally {
            btn.disabled = false;
            btn.textContent = 'Add Tag';
        }
    };

    const handleRemoveTag = async (noteId, tagId) => {
        if (!confirm(`Are you sure you want to remove tag ID ${tagId} from this note?`)) return;
        try {
            const updatedNote = await apiCall(`/notes/${noteId}/tags/${tagId}`, {
                method: 'DELETE'
            });
            displayNoteDetail(updatedNote);
        } catch (error) {
            alert(`Error removing tag: ${error.message}`);
        }
    };

    const handleCreateLink = async () => {
        if (!currentNote) return domHelper.handleError(elements.links.error, 'No source note selected.');
        const { targetInput, error: errorElement, btn } = elements.links;
        domHelper.handleError(errorElement);
        const targetNoteId = targetInput.value.trim();
        if (!targetNoteId) {
            return domHelper.handleError(errorElement, 'Target Note ID cannot be empty.');
        }
        if (targetNoteId === currentNote.id) {
            return domHelper.handleError(errorElement, 'Cannot link a note to itself.');
        }
        if (!/^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(targetNoteId)) {
            return domHelper.handleError(errorElement, "Invalid Target Note ID format (UUID expected).");
        }
        btn.disabled = true;
        btn.textContent = 'Linking...';
        try {
            await apiCall(`/notes/${currentNote.id}/links/${targetNoteId}`, {
                method: 'POST'
            });
            targetInput.value = '';
            await fetchAndDisplayLinks(currentNote.id);
        } catch (apiError) {
            domHelper.handleError(errorElement, `Failed to create link: ${apiError.message}`);
        } finally {
            btn.disabled = false;
            btn.textContent = 'Create Link';
        }
    };

    const handleArchiveNote = async () => {
        if (!currentNote) return;
        const action = currentNote.is_archived ? 'unarchive' : 'archive';
        if (!confirm(`Are you sure you want to ${action} note ${currentNote.id}?`)) return;
        const btn = elements.buttons.archiveNote;
        btn.disabled = true;
        btn.textContent = `${action.charAt(0).toUpperCase() + action.slice(1)}ing...`;
        try {
            const updatedNote = await apiCall(`/notes/${currentNote.id}/${action}`, {
                method: 'POST'
            });
            displayNoteDetail(updatedNote);
            await fetchAndDisplayNotes();
        } catch (error) {
            alert(`Error ${action}ing note: ${error.message}`);
            btn.textContent = currentNote.is_archived ? 'Unarchive' : 'Archive'; // Reset on error
        } finally {
            if (currentNote) btn.disabled = false;
        }
    };

    const handleDeleteNote = async () => {
        if (!currentNote) return;
        const noteIdToDelete = currentNote.id;
        const confirmation = prompt(`To PERMANENTLY DELETE Note ${noteIdToDelete}, please type its ID below:`);
        if (confirmation !== noteIdToDelete) {
            alert('Deletion cancelled or ID mismatch.');
            return;
        }
        if (!confirm('FINAL WARNING: This action is irreversible. Are you sure?')) return;
        const btn = elements.buttons.deleteNote;
        btn.disabled = true;
        btn.textContent = 'Deleting...';
        try {
            await apiCall(`/notes/${noteIdToDelete}/permanent`, {
                method: 'DELETE'
            });
            alert(`Note ${noteIdToDelete} permanently deleted.`);
            currentNote = null;
            domHelper.toggleVisibility(noteDetailElement, false);
            domHelper.handleError(noteDetailPlaceholder, `Note ${noteIdToDelete} deleted. Select another note or create a new one.`);
            domHelper.toggleVisibility(noteDetailPlaceholder, true);
            if (elements.buttons.archiveNote) elements.buttons.archiveNote.disabled = true;
            if (elements.buttons.deleteNote) elements.buttons.deleteNote.disabled = true;
            if (elements.buttons.editNote) elements.buttons.editNote.disabled = true;
            if (elements.tags.btn) elements.tags.btn.disabled = true;
            if (elements.links.btn) elements.links.btn.disabled = true;
            await fetchAndDisplayNotes();
        } catch (error) {
            alert(`Error deleting note: ${error.message}`);
        } finally {
            btn.textContent = 'Delete';
            btn.disabled = !currentNote; // Keep disabled if note was successfully deleted
        }
    };

    // === Helper Functions ===================================================
    const fetchAndDisplayLinks = async (noteId) => {
        if (!elements.links.outgoingList || !elements.links.incomingList) return;
        domHelper.clearChildren(elements.links.outgoingList);
        elements.links.outgoingList.innerHTML = '<li>Loading outgoing links...</li>';
        domHelper.clearChildren(elements.links.incomingList);
        elements.links.incomingList.innerHTML = '<li>Loading incoming links...</li>';
        try {
            const [outgoing, incoming] = await Promise.all([
                apiCall(`/notes/${noteId}/links/outgoing`),
                apiCall(`/notes/${noteId}/links/incoming`)
            ]);
            domHelper.clearChildren(elements.links.outgoingList);
            if (outgoing && outgoing.length > 0) {
                outgoing.forEach(link => elements.links.outgoingList.appendChild(domHelper.createLinkListItem(link)));
            } else {
                elements.links.outgoingList.innerHTML = '<li>None</li>';
            }
            domHelper.clearChildren(elements.links.incomingList);
            if (incoming && incoming.length > 0) {
                incoming.forEach(link => elements.links.incomingList.appendChild(domHelper.createLinkListItem(link)));
            } else {
                elements.links.incomingList.innerHTML = '<li>None</li>';
            }
        } catch (error) {
            console.error(`Error fetching links for note ${noteId}:`, error);
            if (elements.links.outgoingList) elements.links.outgoingList.innerHTML = '<li>Error loading links</li>';
            if (elements.links.incomingList) elements.links.incomingList.innerHTML = '<li>Error loading links</li>';
        }
    };

    const highlightSelectedNote = (noteId) => {
        const listItems = notesList.querySelectorAll('li[data-note-id]');
        listItems.forEach(li => {
            if (li.dataset.noteId === noteId) {
                li.classList.add('active');
            } else {
                li.classList.remove('active');
            }
        });
    };

    // === Initialization =====================================================
    const initializeEventListeners = () => {
        elements.buttons.showCreateForm?.addEventListener('click', () => {
            domHelper.toggleVisibility(createFormContainer, true);
            domHelper.toggleVisibility(noteDetailElement, false);
            domHelper.toggleVisibility(editFormContainer, false);
            domHelper.toggleVisibility(noteDetailPlaceholder, true);
            elements.create.form.reset();
            domHelper.handleError(elements.create.error);
            highlightSelectedNote(null);
        });
        elements.create.cancelBtn?.addEventListener('click', () => {
            domHelper.toggleVisibility(createFormContainer, false);
            if (currentNote) {
                domHelper.toggleVisibility(noteDetailElement, true);
                domHelper.toggleVisibility(noteDetailPlaceholder, false);
            } else {
                domHelper.toggleVisibility(noteDetailPlaceholder, true);
            }
        });
        elements.create.form?.addEventListener('submit', handleCreateNote);
        elements.buttons.editNote?.addEventListener('click', () => {
            if (!currentNote) return;
            elements.edit.noteIdInput.value = currentNote.id;
            elements.edit.contentInput.value = currentNote.content;
            elements.edit.memoryTypeSelect.value = currentNote.memory_type;
            domHelper.toggleVisibility(editFormContainer, true);
            domHelper.toggleVisibility(noteDetailElement, false);
            domHelper.handleError(elements.edit.error);
        });
        elements.edit.cancelBtn?.addEventListener('click', () => {
            domHelper.toggleVisibility(editFormContainer, false);
            if (currentNote) { // Only show detail if a note was being edited
                domHelper.toggleVisibility(noteDetailElement, true);
            } else { // Otherwise, ensure placeholder is visible
                domHelper.toggleVisibility(noteDetailPlaceholder, true);
            }
        });
        elements.edit.form?.addEventListener('submit', handleEditNote);
        notesList?.addEventListener('click', (event) => {
            const listItem = event.target.closest('li[data-note-id]');
            if (listItem && listItem.dataset.noteId) {
                handleNoteSelection(listItem.dataset.noteId);
            }
        });
        elements.search.btn?.addEventListener('click', handleSearch);
        elements.search.input?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleSearch();
            }
        });
        elements.tags.btn?.addEventListener('click', handleAddTag);
        elements.tags.container?.addEventListener('click', (event) => {
            if (event.target.classList.contains('remove-tag')) {
                const tagId = event.target.dataset.tagId;
                if (currentNote && tagId) {
                    handleRemoveTag(currentNote.id, tagId);
                }
            }
        });
        elements.links.btn?.addEventListener('click', handleCreateLink);
        elements.buttons.archiveNote?.addEventListener('click', handleArchiveNote);
        elements.buttons.deleteNote?.addEventListener('click', handleDeleteNote);
    };

    const initializeState = () => {
        domHelper.toggleVisibility(createFormContainer, false);
        domHelper.toggleVisibility(editFormContainer, false);
        domHelper.toggleVisibility(noteDetailElement, false);
        domHelper.toggleVisibility(noteDetailPlaceholder, true);
        if (elements.buttons.editNote) elements.buttons.editNote.disabled = true;
        if (elements.buttons.archiveNote) elements.buttons.archiveNote.disabled = true;
        if (elements.buttons.deleteNote) elements.buttons.deleteNote.disabled = true;
        if (elements.tags.btn) elements.tags.btn.disabled = true;
        if (elements.links.btn) elements.links.btn.disabled = true;
    };

    const fetchAndDisplayNotes = async () => {
        try {
            const notes = await apiCall('/notes/?limit=200');
            domHelper.clearChildren(notesList);
            if (notes && notes.length > 0) {
                notesCache = notes;
                notes.forEach(note => {
                    const listItem = domHelper.createListItem(note, currentNote?.id === note.id);
                    notesList.appendChild(listItem);
                });
            } else {
                notesList.innerHTML = '<li class="empty-list">No notes found. Create one!</li>';
                notesCache = [];
            }
        } catch (error) {
            notesList.innerHTML = `<li class="error">Error loading notes: ${error.message}</li>`;
        }
    };

    initializeEventListeners();
    initializeState();
    fetchAndDisplayNotes();
});