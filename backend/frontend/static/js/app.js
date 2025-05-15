// frontend/static/js/app.js
// Includes AI suggestion display and feedback logging

document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM fully loaded and parsed");

    // --- DOM Element References ---
    const notesListElement = document.getElementById('notes-list');
    const showCreateFormBtn = document.getElementById('show-create-form-btn');
    const createFormContainer = document.getElementById('note-create-form-container');
    const createForm = document.getElementById('note-create-form');
    const createContentInput = document.getElementById('create-content');
    const createMemoryTypeInput = document.getElementById('create-memory-type');
    const cancelCreateBtn = document.getElementById('cancel-create-btn');
    const createErrorElement = document.getElementById('create-error');
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
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    const searchResultsList = document.getElementById('search-results-list');
    const searchErrorElement = document.getElementById('search-error');
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
    const aiSuggestionIndicatorElement = document.getElementById('ai-suggestion-indicator');
    const aiSuggestedTypeTextElement = document.getElementById('ai-suggested-type-text');
    const aiSuggestionReasoningElement = document.getElementById('ai-suggestion-reasoning');
    const applyAiSuggestionLink = document.getElementById('apply-ai-suggestion-link');
    const editFormAiSuggestionElement = document.getElementById('edit-form-ai-suggestion');
    const noteSummaryDisplayElement = document.getElementById('note-summary-display');

    let currentNote = null;
    let notesCache = [];

    async function apiCall(url, options = {}) {
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                let errorDetail = `HTTP error! status: ${response.status}`;
                try {
                    const errorJson = await response.json();
                    errorDetail = errorJson.detail || errorDetail;
                } catch (e) { /* Ignore */ }
                throw new Error(errorDetail);
            }
            if (response.status === 204) return null;
            return await response.json();
        } catch (error) {
            console.error(`API call failed: ${options.method || 'GET'} ${url}`, error);
            throw error;
        }
    }

    function displayNoteList(notes) {
        notesListElement.innerHTML = '';
        if (!notes || notes.length === 0) {
            notesListElement.innerHTML = '<li>No notes found. Create one!</li>';
            return;
        }
        notesCache = notes;
        notes.forEach(note => {
            const listItem = document.createElement('li');
            listItem.textContent = `[${note.memory_type}] ${note.id.substring(0,8)}...`;
            listItem.dataset.noteId = note.id;
            if (currentNote && currentNote.id === note.id) listItem.classList.add('active');
            listItem.addEventListener('click', () => handleNoteSelection(note.id));
            notesListElement.appendChild(listItem);
        });
    }

    function displayNoteDetail(note) {
        currentNote = note;
        noteTitleElement.textContent = `Note: ${note.id}`;
        noteContentDisplayElement.textContent = note.content;
        noteMemoryTypeElement.textContent = note.memory_type;
        noteArchivedElement.textContent = note.is_archived ? 'Yes' : 'No';
        noteCreatedElement.textContent = new Date(note.created_at).toLocaleString();
        noteUpdatedElement.textContent = new Date(note.updated_at).toLocaleString();

        noteTagsElement.innerHTML = '';
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

        if (aiSuggestionIndicatorElement && aiSuggestedTypeTextElement && aiSuggestionReasoningElement && applyAiSuggestionLink) {
            if (note.ai_suggestion && note.ai_suggestion.suggested_type) {
                const suggested = note.ai_suggestion.suggested_type;
                const reasoning = note.ai_suggestion.reasoning || "No reasoning provided.";
                aiSuggestedTypeTextElement.textContent = suggested;
                aiSuggestionReasoningElement.textContent = `Reasoning: ${reasoning}`;
                aiSuggestionIndicatorElement.classList.remove('hidden');
                aiSuggestionReasoningElement.classList.remove('hidden');
                if (note.memory_type !== suggested) {
                    applyAiSuggestionLink.classList.remove('hidden');
                    applyAiSuggestionLink.onclick = async (e) => {
                        e.preventDefault();
                        if (confirm(`Apply AI suggestion: '${suggested}' for this note?`)) {
                            await handleUpdateNoteType(note.id, suggested, note.ai_suggestion);
                        }
                    };
                } else {
                    applyAiSuggestionLink.classList.add('hidden');
                }
            } else {
                aiSuggestionIndicatorElement.classList.add('hidden');
                aiSuggestionReasoningElement.classList.add('hidden');
                applyAiSuggestionLink.classList.add('hidden');
            }
        }


        archiveNoteBtn.textContent = note.is_archived ? 'Unarchive' : 'Archive';
        if(archiveNoteBtn) archiveNoteBtn.dataset.noteId = note.id;
        if(archiveNoteBtn) archiveNoteBtn.disabled = false;
        if(deleteNoteBtn) deleteNoteBtn.dataset.noteId = note.id;
        if(deleteNoteBtn) deleteNoteBtn.disabled = false;
        if(addTagBtn) addTagBtn.disabled = false;
        if(createLinkBtn) createLinkBtn.disabled = false;
        if(addTagInput) addTagInput.value = '';
        if(linkTargetNoteIdInput) linkTargetNoteIdInput.value = '';
        if(addTagErrorElement) hideError(addTagErrorElement);
        if(createLinkErrorElement) hideError(createLinkErrorElement);

        noteDetailElement.classList.remove('hidden');
        if(editFormContainer) editFormContainer.classList.add('hidden');
        if(noteDetailPlaceholder) noteDetailPlaceholder.classList.add('hidden');
        if(createFormContainer) createFormContainer.classList.add('hidden');


        fetchAndDisplayLinks(note.id);
        highlightSelectedNote(note.id);

        // --- Display AI Generated Summary ---
        if (noteSummaryDisplayElement) {
            if (note.summary) {
                noteSummaryDisplayElement.textContent = note.summary;
                noteSummaryDisplayElement.classList.remove('hidden'); // Assuming .hidden might be used
            } else {
                noteSummaryDisplayElement.textContent = 'No summary generated.'; // Or hide it
                // noteSummaryDisplayElement.classList.add('hidden');
            }
        } else {
            console.error("displayNoteDetail: noteSummaryDisplayElement not found!");
        }
        // --- End Display Summary ---

    }

    function displayLinks(listElement, links) {
        listElement.innerHTML = '';
        if (links && links.length > 0) {
            links.forEach(linkedNote => {
                const li = document.createElement('li');
                const link = document.createElement('a');
                link.href = '#';
                link.textContent = `[${linkedNote.memory_type}] ${linkedNote.id.substring(0,8)}...`;
                link.dataset.noteId = linkedNote.id;
                link.onclick = (e) => { e.preventDefault(); handleNoteSelection(linkedNote.id); };
                li.appendChild(link);
                listElement.appendChild(li);
            });
        } else {
            listElement.innerHTML = '<li>None</li>';
        }
    }

    function displaySearchResults(results) {
        searchResultsList.innerHTML = '';
        if (!results || results.length === 0) {
            searchResultsList.innerHTML = '<li>No relevant notes found.</li>';
            return;
        }
        results.forEach(result => {
            const listItem = document.createElement('li');
            const scoreFormatted = result.score.toFixed(3);
            const link = document.createElement('a');
            link.href = '#';
            link.dataset.noteId = result.id;
            link.className = 'search-result-link';
            link.textContent = `[${result.memory_type}] ${result.id.substring(0,8)}...`;
            link.addEventListener('click', (event) => {
                event.preventDefault();
                handleNoteSelection(result.id);
            });
            const scoreSpan = document.createElement('span');
            scoreSpan.textContent = ` (Score: ${scoreFormatted})`;
            const br = document.createElement('br');
            const dateSmall = document.createElement('small');
            dateSmall.textContent = `Updated: ${new Date(result.updated_at).toLocaleDateString()}`;
            listItem.appendChild(link);
            listItem.appendChild(scoreSpan);
            listItem.appendChild(br);
            listItem.appendChild(dateSmall);
            searchResultsList.appendChild(listItem);
        });
    }

    function showCreateForm() {
        if(createFormContainer) createFormContainer.classList.remove('hidden');
        if(noteDetailElement) noteDetailElement.classList.add('hidden');
        if(noteDetailPlaceholder) noteDetailPlaceholder.classList.remove('hidden');
        if(editFormContainer) editFormContainer.classList.add('hidden');
        if(createErrorElement) hideError(createErrorElement);
        if(createForm) createForm.reset();
        currentNote = null;
        highlightSelectedNote(null);
    }

    function hideCreateForm() {
        if(createFormContainer) createFormContainer.classList.add('hidden');
        if (!currentNote && noteDetailPlaceholder) {
            noteDetailPlaceholder.classList.remove('hidden');
        } else if (currentNote && noteDetailElement) {
            noteDetailElement.classList.remove('hidden');
        }
    }

    function showEditForm() {
        if (!currentNote) return;
        if(editNoteIdInput) editNoteIdInput.value = currentNote.id;
        if(editContentInput) editContentInput.value = currentNote.content;
        if(editMemoryTypeInput) editMemoryTypeInput.value = currentNote.memory_type;

        if (editFormAiSuggestionElement) {
            if (currentNote.ai_suggestion &&
                currentNote.ai_suggestion.suggested_type &&
                currentNote.ai_suggestion.suggested_type !== currentNote.memory_type) {
                editFormAiSuggestionElement.textContent = `(AI originally suggested: ${currentNote.ai_suggestion.suggested_type})`;
                editFormAiSuggestionElement.classList.remove('hidden');
            } else {
                editFormAiSuggestionElement.classList.add('hidden');
                editFormAiSuggestionElement.textContent = '';
            }
        }

        if(noteDetailElement) noteDetailElement.classList.add('hidden');
        if(createFormContainer) createFormContainer.classList.add('hidden');
        if(editFormContainer) editFormContainer.classList.remove('hidden');
        if(noteDetailPlaceholder) noteDetailPlaceholder.classList.add('hidden');
        if(editErrorElement) hideError(editErrorElement);
    }

    function hideEditForm() {
        if(editFormContainer) editFormContainer.classList.add('hidden');
        if (currentNote && noteDetailElement) {
             noteDetailElement.classList.remove('hidden');
        } else if (noteDetailPlaceholder) {
             noteDetailPlaceholder.classList.remove('hidden');
        }
    }

    function showError(element, message) {
        if(element) {
            element.textContent = message;
            element.classList.remove('hidden');
        } else {
            console.warn("showError: Element not found to display message:", message);
        }
    }

    function hideError(element) {
         if(element) {
            element.classList.add('hidden');
            element.textContent = '';
         }
    }

    function highlightSelectedNote(noteId) {
        const listItems = notesListElement.querySelectorAll('li');
        listItems.forEach(li => {
            if (li.dataset.noteId && li.dataset.noteId === noteId) {
                li.classList.add('active');
            } else {
                li.classList.remove('active');
            }
        });
    }

    async function logAiCategorizationFeedback(noteId, noteContent, aiSuggestion, userChosenType) {
        if (!noteId || !userChosenType) {
            console.warn("Cannot log feedback: Missing noteId or userChosenType");
            return;
        }
        const contentSnippet = noteContent ? noteContent.substring(0, 500) + (noteContent.length > 500 ? "..." : "") : null;
        const feedbackData = {
            note_id: noteId,
            note_content_snippet: contentSnippet,
            ai_suggested_type: aiSuggestion ? aiSuggestion.suggested_type : null,
            ai_reasoning: aiSuggestion ? aiSuggestion.reasoning : null,
            user_chosen_type: userChosenType
        };
        console.log("Logging AI categorization feedback:", feedbackData);
        try {
            await apiCall('/ai-tools/categorization-feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(feedbackData)
            });
            console.log("AI categorization feedback logged successfully.");
        } catch (error) {
            console.error("Error logging AI categorization feedback:", error);
        }
    }

    async function handleUpdateNoteType(noteId, newMemoryType, originalAiSuggestionObject) {
        console.log(`User applying/changing memory type for note ${noteId} to ${newMemoryType}`);
        try {
            const noteBeingUpdated = notesCache.find(n => n.id === noteId) || currentNote;
            if (!noteBeingUpdated) {
                console.error("Could not find note object to get content for feedback.");
                alert("Error: Could not find note data for feedback.");
                return;
            }
            const updatedNoteFromAPI = await apiCall(`/notes/${noteId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ memory_type: newMemoryType })
            });
            await logAiCategorizationFeedback(
                noteId,
                noteBeingUpdated.content,
                originalAiSuggestionObject,
                newMemoryType
            );
            const displayableNote = {...updatedNoteFromAPI, ai_suggestion: originalAiSuggestionObject };
            displayNoteDetail(displayableNote);
            await fetchAndDisplayNotes();
        } catch (error) {
            console.error(`Error updating note type for ${noteId}:`, error);
            alert(`Failed to update memory type: ${error.message}`);
        }
    }

    // --- Event Handlers ---
    async function handleNoteSelection(noteId) {
        console.log(`Selecting note detail for ID: ${noteId}`);
        if(createErrorElement) hideError(createErrorElement);
        if(editErrorElement) hideError(editErrorElement);
        if(noteDetailPlaceholder) noteDetailPlaceholder.classList.add('hidden');
        try {
            const note = await apiCall(`/notes/${noteId}`);
            if (note) {
                 displayNoteDetail(note);
            } else {
                 console.warn(`Note ${noteId} not found when fetching detail.`);
                 await fetchAndDisplayNotes();
                 if(noteDetailPlaceholder) noteDetailPlaceholder.classList.remove('hidden');
                 if(noteDetailElement) noteDetailElement.classList.add('hidden');
                 currentNote = null;
                 highlightSelectedNote(null);
            }
        } catch (error) {
            if(noteDetailPlaceholder) {
                showError(noteDetailPlaceholder, `Error loading note: ${error.message}`);
                noteDetailPlaceholder.classList.remove('hidden');
            }
            if(noteDetailElement) noteDetailElement.classList.add('hidden');
            currentNote = null;
            highlightSelectedNote(null);
        }
    }

    async function handleCreateNote(event) {
        event.preventDefault();
        if(createErrorElement) hideError(createErrorElement);
        const noteDataFromForm = {
            content: createContentInput.value.trim(),
            memory_type: createMemoryTypeInput.value
        };
        if (!noteDataFromForm.content) {
            if(createErrorElement) showError(createErrorElement, "Content cannot be empty.");
            return;
        }
        try {
            const createdNoteWithSuggestion = await apiCall('/notes/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(noteDataFromForm)
            });
            console.log("Note created:", createdNoteWithSuggestion);
            await logAiCategorizationFeedback(
                createdNoteWithSuggestion.id,
                createdNoteWithSuggestion.content,
                createdNoteWithSuggestion.ai_suggestion,
                noteDataFromForm.memory_type
            );
            hideCreateForm();
            await fetchAndDisplayNotes();
            handleNoteSelection(createdNoteWithSuggestion.id);
        } catch (error) {
            if(createErrorElement) showError(createErrorElement, `Failed to create note: ${error.message}`);
        }
    }

    async function handleEditNote(event) {
        event.preventDefault();
        if(editErrorElement) hideError(editErrorElement);
        const noteId = editNoteIdInput.value;
        const editedNoteDataFromForm = {
            content: editContentInput.value.trim(),
            memory_type: editMemoryTypeInput.value
        };
        if (!editedNoteDataFromForm.content) {
             if(editErrorElement) showError(editErrorElement, "Content cannot be empty.");
            return;
        }
        try {
            const originalMemoryTypeBeforeEdit = currentNote ? currentNote.memory_type : null;
            const originalAiSuggestionForThisNote = currentNote ? currentNote.ai_suggestion : null;
            const updatedNoteFromAPI = await apiCall(`/notes/${noteId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(editedNoteDataFromForm)
            });
            console.log("Note updated:", updatedNoteFromAPI);
            if (currentNote && originalMemoryTypeBeforeEdit !== editedNoteDataFromForm.memory_type) {
                await logAiCategorizationFeedback(
                    updatedNoteFromAPI.id,
                    updatedNoteFromAPI.content,
                    originalAiSuggestionForThisNote,
                    editedNoteDataFromForm.memory_type
                );
            }
            const displayableNote = {...updatedNoteFromAPI, ai_suggestion: originalAiSuggestionForThisNote };
            displayNoteDetail(displayableNote);
            await fetchAndDisplayNotes();
        } catch (error) {
            if(editErrorElement) showError(editErrorElement, `Failed to update note: ${error.message}`);
        }
    }

    async function handleSearch() {
        const query = searchInput.value.trim();
        searchResultsList.innerHTML = '<li>Searching...</li>';
        if(searchErrorElement) hideError(searchErrorElement);
        if (!query) {
            searchResultsList.innerHTML = '';
            return;
        }
        try {
            const searchData = { query: query, limit: 15 };
            const responseData = await apiCall('/search/similar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(searchData)
            });
            displaySearchResults(responseData.results);
        } catch (error) {
            if(searchErrorElement) showError(searchErrorElement, `Search failed: ${error.message}`);
            searchResultsList.innerHTML = '<li>Search failed.</li>';
        }
    }

    async function handleToggleArchive() {
        if (!currentNote || !archiveNoteBtn) return;
        const noteId = currentNote.id;
        const isArchived = currentNote.is_archived;
        const action = isArchived ? 'unarchive' : 'archive';
        const confirmationMessage = `Are you sure you want to ${action} note ${noteId}?`;
        if (!confirm(confirmationMessage)) return;
        archiveNoteBtn.disabled = true;
        archiveNoteBtn.textContent = `${action.charAt(0).toUpperCase() + action.slice(1)}ing...`;
        try {
            const updatedNote = await apiCall(`/notes/${noteId}/${action}`, { method: 'POST' });
            displayNoteDetail(updatedNote);
            await fetchAndDisplayNotes();
        } catch (error) {
            alert(`Error ${action}ing note: ${error.message}`);
            archiveNoteBtn.disabled = false;
            archiveNoteBtn.textContent = isArchived ? 'Unarchive' : 'Archive';
        }
    }

    async function handleDeleteNote() {
        if (!currentNote || !deleteNoteBtn) return;
        const noteId = currentNote.id;
        const confirmation1 = confirm(`PERMANENTLY DELETE NOTE ${noteId}? This cannot be undone.`);
        if (!confirmation1) return;
        const confirmation2 = prompt(`To confirm, type note ID (${noteId}):`);
        if (confirmation2 !== noteId) {
             alert("Confirmation ID mismatch. Note not deleted.");
            return;
        }
        deleteNoteBtn.disabled = true;
        deleteNoteBtn.textContent = 'Deleting...';
        try {
            await apiCall(`/notes/${noteId}/permanent`, { method: 'DELETE' });
            alert(`Note ${noteId} permanently deleted.`);
            currentNote = null;
            if(noteDetailElement) noteDetailElement.classList.add('hidden');
            if(noteDetailPlaceholder) {
                noteDetailPlaceholder.textContent = `Note ${noteId} deleted. Select another.`;
                noteDetailPlaceholder.classList.remove('hidden');
            }
            if(archiveNoteBtn) archiveNoteBtn.disabled = true;
            if(deleteNoteBtn) deleteNoteBtn.disabled = true;
            if(addTagBtn) addTagBtn.disabled = true;
            if(createLinkBtn) createLinkBtn.disabled = true;
            if(deleteNoteBtn) deleteNoteBtn.textContent = 'Delete';
            await fetchAndDisplayNotes();
        } catch (error) {
            alert(`Error deleting note: ${error.message}`);
            if(deleteNoteBtn) {
                deleteNoteBtn.disabled = false;
                deleteNoteBtn.textContent = 'Delete';
            }
        }
    }

    async function handleRemoveTag(noteId, tagId) {
        if (!confirm(`Remove tag ID ${tagId} from this note?`)) return;
        try {
            const updatedNote = await apiCall(`/notes/${noteId}/tags/${tagId}`, { method: 'DELETE' });
            displayNoteDetail(updatedNote);
        } catch (error) {
             alert(`Error removing tag: ${error.message}`);
        }
    }

    async function handleAddTag() {
        if (!currentNote || !addTagBtn || !addTagErrorElement) return;
        hideError(addTagErrorElement);
        const noteId = currentNote.id;
        const tagInputVal = addTagInput.value.trim();
        if (!tagInputVal) {
            showError(addTagErrorElement, "Enter an existing Tag ID.");
            return;
        }
        const tagId = parseInt(tagInputVal, 10);
        if (isNaN(tagId)) {
            showError(addTagErrorElement, "Invalid input: Numeric Tag ID required.");
            return;
        }
        addTagBtn.disabled = true;
        addTagBtn.textContent = 'Adding...';
        try {
            const updatedNote = await apiCall(`/notes/${noteId}/tags/${tagId}`, { method: 'POST' });
            displayNoteDetail(updatedNote);
            addTagInput.value = '';
        } catch (error) {
            showError(addTagErrorElement, `Failed: ${error.message}`);
        } finally {
            addTagBtn.disabled = false;
            addTagBtn.textContent = 'Add Tag';
        }
    }

    async function handleCreateLink() {
        if (!currentNote || !createLinkBtn || !createLinkErrorElement) return;
        hideError(createLinkErrorElement);
        const sourceNoteId = currentNote.id;
        const targetNoteId = linkTargetNoteIdInput.value.trim();
        if (!targetNoteId) {
            showError(createLinkErrorElement, "Enter Target Note ID.");
            return;
        }
        if (!/^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(targetNoteId)) {
             showError(createLinkErrorElement, "Invalid Target Note ID format (UUID expected).");
             return;
        }
        if (sourceNoteId === targetNoteId) {
             showError(createLinkErrorElement, "Cannot link a note to itself.");
             return;
        }
        createLinkBtn.disabled = true;
        createLinkBtn.textContent = 'Linking...';
        try {
            await apiCall(`/notes/${sourceNoteId}/links/${targetNoteId}`, { method: 'POST' });
            await fetchAndDisplayLinks(sourceNoteId);
            linkTargetNoteIdInput.value = '';
        } catch (error) {
            showError(createLinkErrorElement, `Failed: ${error.message}`);
        } finally {
            createLinkBtn.disabled = false;
            createLinkBtn.textContent = 'Create Link';
        }
    }

    // --- Async Function Wrappers (Initial load, Links) ---
    async function fetchAndDisplayNotes() {
        console.log("Fetching notes list...");
        try {
            if (!currentNote && noteDetailPlaceholder) {
                 noteDetailPlaceholder.classList.remove('hidden');
            }
            const notes = await apiCall('/notes/?limit=200');
            displayNoteList(notes);
        } catch (error) {
            console.error("Error fetching notes:", error);
            notesListElement.innerHTML = `<li>Error loading notes: ${error.message}</li>`;
        }
    }

    async function fetchAndDisplayLinks(noteId) {
        if(outgoingLinksList) outgoingLinksList.innerHTML = '<li>Loading...</li>';
        if(incomingLinksList) incomingLinksList.innerHTML = '<li>Loading...</li>';
        try {
            const [outgoing, incoming] = await Promise.all([
                apiCall(`/notes/${noteId}/links/outgoing`),
                apiCall(`/notes/${noteId}/links/incoming`)
            ]);
            if(outgoingLinksList) displayLinks(outgoingLinksList, outgoing);
            if(incomingLinksList) displayLinks(incomingLinksList, incoming);
        } catch (error) {
            console.error(`Error fetching links for note ${noteId}:`, error);
            if(outgoingLinksList) outgoingLinksList.innerHTML = '<li>Error loading links</li>';
            if(incomingLinksList) incomingLinksList.innerHTML = '<li>Error loading links</li>';
        }
    }

    // --- Initial Setup & Event Listeners ---
    // Null checks for all elements before adding listeners
    if (showCreateFormBtn) showCreateFormBtn.addEventListener('click', showCreateForm);
    if (cancelCreateBtn) cancelCreateBtn.addEventListener('click', hideCreateForm);
    if (createForm) createForm.addEventListener('submit', handleCreateNote);

    if (editNoteBtn) editNoteBtn.addEventListener('click', showEditForm);
    if (cancelEditBtn) cancelEditBtn.addEventListener('click', hideEditForm);
    if (editForm) editForm.addEventListener('submit', handleEditNote);

    if (archiveNoteBtn) archiveNoteBtn.addEventListener('click', handleToggleArchive);
    if (deleteNoteBtn) deleteNoteBtn.addEventListener('click', handleDeleteNote);
    if (addTagBtn) addTagBtn.addEventListener('click', handleAddTag);
    if (createLinkBtn) createLinkBtn.addEventListener('click', handleCreateLink);

    if (searchBtn) searchBtn.addEventListener('click', handleSearch);
    if (searchInput) searchInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter' || event.keyCode === 13) {
            event.preventDefault();
            handleSearch();
        }
    });

    // Disable buttons initially
    if(archiveNoteBtn) archiveNoteBtn.disabled = true;
    if(deleteNoteBtn) deleteNoteBtn.disabled = true;
    if(addTagBtn) addTagBtn.disabled = true;
    if(createLinkBtn) createLinkBtn.disabled = true;

    fetchAndDisplayNotes(); // Initial data load

}); // End of DOMContentLoaded