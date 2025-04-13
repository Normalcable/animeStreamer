// static/player.js

document.addEventListener('DOMContentLoaded', function() {

    // --- Video Player Logic ---
    const player = document.getElementById('main-player');
    const episodeButtons = document.querySelectorAll('.episode-button');
    const currentEpisodeTitle = document.getElementById('current-episode-title');
    const videoErrorDiv = document.getElementById('video-error');
    const loadingIndicator = document.getElementById('loading-indicator');
    const downloadCurrentButton = document.getElementById('download-current-episode');
    let currentActiveButton = null;

    function updateDownloadButton(src, name) {
         if (src && name) {
            downloadCurrentButton.href = src;
            downloadCurrentButton.setAttribute('download', name);
            downloadCurrentButton.classList.add('visible');
        } else {
            downloadCurrentButton.href = '#';
            downloadCurrentButton.removeAttribute('download');
            downloadCurrentButton.classList.remove('visible');
        }
    }

    function selectEpisode(button, isInitialLoad = false) {
        if (currentActiveButton) currentActiveButton.classList.remove('active');
        button.classList.add('active');
        currentActiveButton = button;
        const episodeSrc = button.getAttribute('data-episode-src');
        const episodeName = button.getAttribute('data-episode-name');
        currentEpisodeTitle.textContent = episodeName;
        videoErrorDiv.style.display = 'none'; videoErrorDiv.textContent = '';
        updateDownloadButton(episodeSrc, episodeName);
        if (!isInitialLoad) {
            player.pause(); player.removeAttribute('src');
            // Clear previous sources if any (good practice)
            while (player.firstChild) {
                player.removeChild(player.firstChild);
            }
            player.load(); // Reset player state
        }
        player.src = episodeSrc;
         if (!isInitialLoad) {
            if(loadingIndicator) loadingIndicator.style.display = 'block';
            player.play().catch(e => console.warn("Playback initiation error:", e.message));
        } else {
             if(loadingIndicator) loadingIndicator.style.display = 'none';
        }
    }

    if (player) { // Only add listeners if player exists
        player.addEventListener('waiting', () => { if(loadingIndicator) loadingIndicator.style.display = 'block'; });
        player.addEventListener('canplay', () => { if(loadingIndicator) loadingIndicator.style.display = 'none'; });
        player.addEventListener('playing', () => { if(loadingIndicator) loadingIndicator.style.display = 'none'; });
        player.addEventListener('ended', () => { if(loadingIndicator) loadingIndicator.style.display = 'none'; });
        player.addEventListener('error', (e) => {
             if(loadingIndicator) loadingIndicator.style.display = 'none';
             let errorMsg = 'Error loading video. ';
             const videoError = player.error;
             if (videoError) {
                switch (videoError.code) {
                    case videoError.MEDIA_ERR_ABORTED: errorMsg += 'Playback aborted.'; break;
                    case videoError.MEDIA_ERR_NETWORK: errorMsg += 'Network error caused download to fail.'; break;
                    case videoError.MEDIA_ERR_DECODE: errorMsg += 'Decoding error.'; break;
                    case videoError.MEDIA_ERR_SRC_NOT_SUPPORTED: errorMsg += 'Media format not supported.'; break;
                    default: errorMsg += 'An unknown error occurred.'; break;
                }
             } else { errorMsg += 'An unspecified error occurred.' }
             if (currentActiveButton) {
                 errorMsg += ` [File: ${currentActiveButton.getAttribute('data-episode-name')}]`;
             }
             console.error('Video Error Event:', errorMsg, e, player.error);
             if (videoErrorDiv) {
                 videoErrorDiv.textContent = errorMsg; videoErrorDiv.style.display = 'block';
             }
             updateDownloadButton(null, null); // Hide download on error
        });
    }

    episodeButtons.forEach(button => {
        button.addEventListener('click', function() {
             if (this !== currentActiveButton) {
                 selectEpisode(this, false);
             } else {
                 // Toggle play/pause if clicking the already active one
                 if (player && player.paused) {
                     player.play().catch(e=>console.warn("Play failed",e));
                 } else if (player) {
                     player.pause();
                 }
             }
        });
    });

    // --- Auto-select first episode on load ---
    if (episodeButtons.length > 0) {
        selectEpisode(episodeButtons[0], true);
    } else {
         if(currentEpisodeTitle) currentEpisodeTitle.textContent = "No compatible episodes found";
         if(loadingIndicator) loadingIndicator.style.display = 'none';
         updateDownloadButton(null, null);
    }


    // --- Comment Form Logic ---
    const commentForm = document.getElementById('comment-form');
    const commentsList = document.getElementById('comments-list');
    const commentErrorDiv = document.getElementById('comment-error');
    const noCommentsLi = document.getElementById('no-comments-yet');

     // --- Helper function to format timestamp (basic example) ---
     function formatTimestamp(isoString) {
        if (!isoString) return '';
        try {
            const date = new Date(isoString);
            // Make it a bit more readable than raw ISO
            return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
        } catch (e) {
            return isoString; // Fallback to raw string if parsing fails
        }
     }

    // --- Function to safely create HTML elements (prevents XSS) ---
    function createTextElement(tag, text) {
        const element = document.createElement(tag);
        element.textContent = text; // Safely sets text content
        return element;
    }

    // --- Function to add a new comment to the list ---
    function addCommentToDOM(comment) {
        if (!commentsList) return; // Don't proceed if list doesn't exist

        const listItem = document.createElement('li');

        const authorSpan = createTextElement('span', comment.name);
        authorSpan.className = 'comment-author';

        const timestampSpan = createTextElement('span', ` (${formatTimestamp(comment.timestamp)})`);
        timestampSpan.className = 'comment-timestamp';

        const bodyDiv = createTextElement('div', comment.comment);
        bodyDiv.className = 'comment-body';

        listItem.appendChild(authorSpan);
        listItem.appendChild(timestampSpan);
        listItem.appendChild(bodyDiv);

        // Add the new comment to the *top* of the list
        commentsList.prepend(listItem);

        // Remove the "No comments yet" message if it exists and is currently displayed
        const currentNoCommentsLi = document.getElementById('no-comments-yet');
        if (currentNoCommentsLi) {
            currentNoCommentsLi.remove();
        }
    }

    // --- Handle Comment Form Submission ---
    if (commentForm) {
        // Get the submission URL from the data attribute ONCE
        const addCommentUrl = commentForm.getAttribute('data-add-comment-url');

        commentForm.addEventListener('submit', function(event) {
            event.preventDefault(); // Stop default page reload
            if (commentErrorDiv) {
                commentErrorDiv.style.display = 'none'; // Hide previous errors
                commentErrorDiv.textContent = '';
            }

            const formData = new FormData(commentForm);

            // Use the URL retrieved earlier
            if (!addCommentUrl) {
                 console.error("Add comment URL not found on form data attribute.");
                 if (commentErrorDiv) {
                    commentErrorDiv.textContent = 'Error: Cannot determine submission URL.';
                    commentErrorDiv.style.display = 'block';
                 }
                 return; // Stop submission if URL is missing
            }

            fetch(addCommentUrl, {
                method: 'POST',
                body: formData // Send form data directly
            })
            .then(response => {
                if (!response.ok) {
                    // Try to get error message from backend JSON response
                    return response.json().then(errData => {
                        // Use the error message from backend if available, otherwise use status text
                        throw new Error(errData.error || response.statusText || `HTTP error! Status: ${response.status}`);
                    }).catch(() => {
                        // If parsing the error JSON fails, throw a generic error
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    });
                }
                return response.json(); // Parse successful JSON response
            })
            .then(data => {
                if (data.success && data.comment) {
                    // Add the new comment to the top of the list
                    addCommentToDOM(data.comment);
                    // Clear the form fields
                    commentForm.reset();
                } else {
                    // Handle cases where success is false or comment is missing
                    throw new Error(data.error || 'Failed to post comment. Unknown reason.');
                }
            })
            .catch(error => {
                console.error('Error submitting comment:', error);
                if (commentErrorDiv) {
                    commentErrorDiv.textContent = `Error: ${error.message}`;
                    commentErrorDiv.style.display = 'block';
                }
            });
        });
    }

     // --- Initial formatting for existing timestamps ---
     if (commentsList) {
         const existingTimestamps = commentsList.querySelectorAll('.comment-timestamp');
         existingTimestamps.forEach(span => {
             // Extract the raw timestamp (might be inside parentheses)
             const rawTimestamp = span.textContent.replace(/[()]/g, '').trim();
             span.textContent = ` (${formatTimestamp(rawTimestamp)})`;
         });
     }


    // --- Download All Button Placeholder ---
    const downloadAllButton = document.querySelector('.download-all-button');
    if (downloadAllButton) {
        downloadAllButton.addEventListener('click', function(event) {
            // Check if it's just a placeholder link
            if (this.getAttribute('href') === '#') {
                event.preventDefault();
                alert('This feature requires server-side implementation to create a ZIP file.');
            }
        });
    }

}); // End of DOMContentLoaded listener