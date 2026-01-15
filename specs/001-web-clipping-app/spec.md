# Feature Specification: Web Clipping and Reference Application

**Feature Branch**: `[001-web-clipping-app]`  
**Created**: 2026-01-15  
**Status**: Draft  
**Input**: User description: "Build an application that would help the user browsing websites to save interesting text for reference. As a user, when I am browsing websites and I find some interesting text, I highlight it in my browser and save it using an extension to be able to search reference it later. For each text clipping I should be able to go back to the originating website, and I should be able to see when it was clipped/saved. Also, I should be able to (optionally) label clippings so I can locate them easily afterwards. My notes (clipped text) should be accessible through a user-friendly web application, grouped by label or website (source)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Capture and revisit a clipping (Priority: P1)

As a person who reads a lot online, I want to quickly save a selected piece of text while browsing and later find it again with its original context, so that I can reliably revisit important information without having to remember where I saw it.

**Why this priority**: Capturing and revisiting clipped text is the core value of the product. Without this, there is no meaningful benefit to the user.

**Independent Test**: If only this story is implemented, a user can save text from a webpage and later, via the web application, see that clipping with its text, capture time, and a link back to the original page.

**Acceptance Scenarios**:

1. **Given** a signed-in user is browsing a supported website and selects a piece of text, **when** they choose the option to save the selection as a clipping, **then** a new clipping is created that stores the selected text, the page title (if available), the full URL, and the capture timestamp.
2. **Given** a user has previously saved one or more clippings, **when** they open the web application and view their list of clippings, **then** they can see each clipping's text preview, capture timestamp, and a clickable link that opens the original page in a new tab or window.

---

### User Story 2 - Organize clippings with labels (Priority: P2)

As a user who saves many clippings, I want to optionally add labels (such as topics or projects) when I save or review a clipping, so that I can later group and find related clippings more easily.

**Why this priority**: Labels significantly improve the ability to manage and retrieve clippings as the collection grows, but basic capture and recall must exist first.

**Independent Test**: If only this story is implemented in addition to basic capture, a user can add, change, and remove labels on clippings and then filter by those labels in the web application.

**Acceptance Scenarios**:

1. **Given** a user is saving a new clipping, **when** they add one or more labels before confirming the save, **then** those labels are stored with the clipping and visible in the web application.
2. **Given** a user is viewing an existing clipping, **when** they edit the clipping's labels and save their changes, **then** the updated labels are reflected wherever the clipping appears in lists and filters.

---

### User Story 3 - Browse and search clippings by label or website (Priority: P3)

As a user looking for something I saved earlier, I want to browse and search my clippings by label, source website, and text content, so that I can quickly locate the information I need even if I do not remember the exact wording.

**Why this priority**: Efficient retrieval across many clippings is critical for long-term usefulness, but becomes most valuable after basic capture and labeling are in place.

**Independent Test**: If this story is implemented in addition to basic capture and labeling, a user can reliably find a specific clipping within a large collection using search and filters without scanning every item manually.

**Acceptance Scenarios**:

1. **Given** a user has clippings with different labels, **when** they filter the list of clippings by a single label, **then** only clippings that have that label are shown.
2. **Given** a user has clippings from multiple websites, **when** they choose to view clippings grouped or filtered by source website, **then** they can see clippings organized by website (for example, showing all clippings from the same domain together).
3. **Given** a user remembers a few words from a clipping, **when** they search using those words, **then** clippings whose text or title contains those words appear in the results.

---

### Edge Cases

- What happens when a user clips a very long piece of text (for example, an entire article section)? The system should still store the full text but show a shortened preview in lists, with the full text accessible in a detailed view.
- What happens when a user saves multiple clippings from the same page or with identical text? Each clipping should be stored separately with its own capture timestamp, while still indicating the same source page.
- How does the system handle a user opening the original page when the website has changed or the page is no longer available? The clipping and its metadata should remain accessible, and the system should display a clear message if the original page cannot be loaded.
- What happens if a user attempts to save a clipping while not signed in? The user should be prompted to sign in (or informed that sign-in is required) before the clipping can be saved.
- How are duplicate label names handled? The system should either prevent creating two distinct labels with exactly the same name for a single user or clearly treat same-named labels as a single label in all lists and filters.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow a signed-in user to save selected text from a visited webpage as a clipping, capturing at minimum the selected text, the page title (if available), the full URL, and the capture timestamp.
- **FR-002**: System MUST allow a user to view a list of their own clippings in a web application, ordered by most recent capture by default.
- **FR-003**: Users MUST be able to open the original webpage of any clipping via a clearly visible link from the clipping list or detail view.
- **FR-004**: System MUST display the capture date and time for each clipping in a human-readable format anywhere the clipping is shown.
- **FR-005**: Users MUST be able to optionally assign one or more labels to a clipping at the time of saving and when editing an existing clipping.
- **FR-006**: Users MUST be able to view all labels they have created and see how many clippings are associated with each label.
- **FR-007**: Users MUST be able to filter or group their clippings by label in the web application.
- **FR-008**: Users MUST be able to filter or group their clippings by source website (for example, by domain) in the web application.
- **FR-009**: Users MUST be able to search their clippings by text content, label name, and website, from within the web application.
- **FR-010**: Users MUST be able to delete clippings they no longer want to keep, and deleted clippings MUST no longer appear in any list, search result, or grouping.
- **FR-011**: System MUST ensure that each user can only view and manage their own clippings; clippings are private to the user and are not visible to other users.
- **FR-012**: System MUST provide a simple explanation or help content that tells users how to capture clippings and how to access them in the web application.

### Key Entities *(include if feature involves data)*

- **User**: Represents a person who signs in to the system. Key attributes include a unique identifier and profile information necessary to distinguish one user from another. A user can own many clippings and labels.
- **Clipping**: Represents a saved piece of text captured from a webpage. Key attributes include the clipped text, page title (if available), full source URL, source website (such as domain), capture timestamp, and associations to one user and zero or more labels.
- **Label**: Represents a user-defined tag used to organize clippings. Key attributes include a label name (and optionally a description or color). A label can be associated with many clippings for the same user.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In usability tests with new users, at least 90% of participants can capture a clipping from a website and later find it again in the web application (using default sorting) within 1 minute, without assistance.
- **SC-002**: In usability tests simulating a user with at least 50 clippings, at least 80% of participants can successfully use labels or website-based grouping to locate a relevant clipping within 30 seconds, without assistance.
- **SC-003**: For a representative sample of 100 recently created clippings where the original pages are still available on the internet, at least 95% of "Open original page" actions successfully load the correct website page.
- **SC-004**: In user feedback collected after at least two weeks of use, the average satisfaction score for "Saving a clipping" and "Finding a clipping again" is at least 4.0 out of 5.
- **SC-005**: Under typical usage conditions (for example, up to 1,000 clippings for a single user), the time from requesting the list or search results to seeing them rendered in the web application is perceived by users as responsive, with at least 95% of test interactions completing within a few seconds.

## Assumptions and Dependencies

- Users create an account and sign in before saving or viewing clippings; the specific sign-in mechanism will be decided separately and is not defined in this specification.
- The primary content captured is text selected by the user; capturing images, full-page screenshots, or complex formatting is outside the scope of this feature.
- Users have access to a modern web browser and an approved capture mechanism (such as a browser-based tool) that allows selected text and associated metadata to be sent to the system.
- The system stores clipping text and metadata even if the original webpage later changes or is removed; returning to the original page depends on the continued availability of that page on the public internet.
- Sharing clippings with other users, collaborative workspaces, and advanced permission models are explicitly out of scope for this feature.
